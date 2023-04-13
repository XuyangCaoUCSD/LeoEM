"""
    the very emulator program at stage 3
    powered by Mininet
"""
from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg
from mininet.util import dumpNodeConnections
import time
import networkx as nx
import numpy
import random
import scipy.io as scio
import math
from mininet.cli import CLI
from ast import literal_eval
from mininet.node import RemoteController
import sys
import socket
import subprocess
import concurrent.futures
import threading
import logging
import logging.handlers

my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.DEBUG)

handler = logging.handlers.SysLogHandler(address = '/dev/log')

my_logger.addHandler(handler)

REMOTE_CONTROLLER_IP = "127.0.0.1"
kernel_output = open('/dev/kmsg', 'w')
# number of seconds delayed before reporting the new handover status to UEs
status_report_delayed_shift = -0.5
# SATCP_aggresive_duration = 0.5

if len(sys.argv) != 2:
    print("need to specify the path information file!")
    exit()

intermediate_hop_num = 0
frame_length = 1
path_info_file = sys.argv[1]

last_routing_path = ["NULL"]
current_routing_path = ["NULL"]
last_node_delay = ["NULL"]
current_node_delay = ["NULL"]

# according to the Starlink website and practical measurement from Starlink Reddit community,
# set the bent-pipe link bandwidth of current commercial satellite network to be 150 Mbps
bent_pipe_link_bandwidth = 150
# a negligible delay value assigned to links when the simulation has not started yet
unitialized_bent_pipe_delay = '0.01ms'
# a very generous queue size to store packets during handovers 
switch_queue_size = 50000

switches = []

'''
    temporarily turn off and on the link between dish and ingress sat nodes to simulate the link break due to path change
'''
def simulate_dish_gateway_sat_handover(net_dish_sat_delay):
    try:
        net = net_dish_sat_delay[0]
        dish = net_dish_sat_delay[1]
        sat = net_dish_sat_delay[2]
        delay = net_dish_sat_delay[3]
        subprocess.run(["echo", "UNIX TIME: %s: end handover triggered!" % str(time.time())], stdout=kernel_output)
        # HANDOVER STARTS
        net.configLinkStatus(dish, sat, 'down')
        time.sleep(delay)
        net.configLinkStatus(dish, sat, 'up')
        # HANDOVER ENDS
    except Exception as e:
        print("failed to simulate end handover:", e)

'''
    temporarily turn off and on the link between two intermediate switching nodes to simulate the link break due to path change
'''
def simulate_link_break(net_and_node_i):
    try:
        net = net_and_node_i[0]
        i = net_and_node_i[1]
        subprocess.run(["echo", "UNIX TIME: %s: intermediate handover triggered!" % str(time.time())], stdout=kernel_output)
        net.configLinkStatus('s%s' % (i), 's%s' % (i + 1), 'down')
        net.configLinkStatus('s%s' % (i), 's%s' % (i + 1), 'up')
    except Exception as e:
        print("failed to simulate intermediate handover:", e)


def report_handover_status_asynchronously(handover_status, delay):
    t = threading.Thread(target = report_handover_status, args = (handover_status, delay), daemon = True)
    t.start()
    return t

'''
    report the (upcoming) handover status to the user device
    handover_status: 1 represents an upcoming handover; 0 represents no handover in the near future
'''
def report_handover_status(handover_status, delay):
    time.sleep(delay)
    msg_from_client = str(handover_status)
    bytes_to_send = str.encode(msg_from_client)
    server_addr = ("127.0.0.1", 20001)
    # create a UDP socket at client side
    udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # send to server using created UDP socket
    udp_client_socket.sendto(bytes_to_send, server_addr)
    udp_client_socket.close()

'''
    this function will be used to find intermediate nodes that will undergo a handover.

    for example:
    old path (size n): [-1, 749, 8, 812, 11, 876, 14, 67, 79, 45, 1395, -2]
    new path (size m): [-1, 749, 8, 812, 14, 68, 79, 45, 1395, -2]
    then we let handover occur at (812, 14), (68, 79) momentarily, which should be enough.

    returned value will be a (m-1) size array containing 0s and 1s. An 1 at index i means ith and (i+1)th nodes will have a handover.
'''
def compute_link_delta(old_link, new_link):
    old_intermediate = old_link[1:-1]
    new_intermediate = new_link[1:-1]
    handover_arr = [0] * (len(new_intermediate) - 1)
    # j is the old link pointer
    j = 0
    for i in range(0, len(new_intermediate)):
        if new_intermediate[i] in old_intermediate:
            # ends the difference
            if old_intermediate.index(new_intermediate[i]) != j:
                handover_arr[i - 1] = 1
                j = old_intermediate.index(new_intermediate[i])
            j += 1
        else:
            # starts the difference
            if i > 0 and new_intermediate[i - 1] in old_intermediate:
                handover_arr[i - 1] = 1
    
    return [0] + handover_arr + [0]
    

class MyTopo( Topo ):
    def __init__( self ):
        "Create custom topo."
        global switches

        # initialize topology
        Topo.__init__( self )

        # spawn the two test hosts (user end devices)
        h1 = self.addHost('h1', ip="10.0.1.101/24")
        h2 = self.addHost('h2', ip="10.0.1.102/24")
        # spawn enough number of satellite nodes required for a path at anytime
        # hence s0 is the first user's dish, and s_(intermediate_hop_num - 1) is the second user's dish
        for i in range(intermediate_hop_num):
            switches.append(self.addSwitch('s%s' % i))
        # create the satellite links
        for i in range(intermediate_hop_num - 1):
            self.addLink('s%s' % i, 's%s' % (i + 1), bw = bent_pipe_link_bandwidth, delay = unitialized_bent_pipe_delay, max_queue_size=switch_queue_size)
        # connect the user device and their dish together (the delay should be negligible)
        self.addLink("h1", "s0", bw = bent_pipe_link_bandwidth, delay = unitialized_bent_pipe_delay, max_queue_size=switch_queue_size)
        self.addLink("h2", "s%s" % (intermediate_hop_num - 1), bw = bent_pipe_link_bandwidth, delay = unitialized_bent_pipe_delay, max_queue_size=switch_queue_size)

        '''
            
                        /------s1(sat)------\                 /------s3(sat)------\                  /------...------\
            h1 --- s0 (dish)                 s2(ground station)                    s4(ground station)                 s(intermediate_hop_num - 1)(dish) --- h2
        '''

'''
    update the bandwidth and delay for the link between node1 and node2

    net: the mininet object
    node1: the name of node1 (string)
    node2: the name of node2 (string)
    bw: the bandwidth value in Mbps (int)
    delay: the one-way delay value (e.x. '5ms'; string)
'''
def set_link_properties(net, node1, node2, bw, delay, max_queue_size=switch_queue_size):
    hop_a = net.getNodeByName(node1)
    hop_b = net.getNodeByName(node2)
    interfaces = hop_a.connectionsTo(hop_b)
    src_intf = interfaces[0][0]
    dst_intf = interfaces[0][1]
    src_intf.config(bw = bw, delay = delay, max_queue_size=switch_queue_size, smooth_change = True)
    dst_intf.config(bw = bw, delay = delay, max_queue_size=switch_queue_size, smooth_change = True)


def initialize_link(net):
    # assign a reasonable bandwidth and a negligible delay (since not start yet) to links
    for i in range (intermediate_hop_num - 1):
        set_link_properties(net, "s%s" % str(i), "s%s" % str(i + 1), bent_pipe_link_bandwidth, unitialized_bent_pipe_delay, max_queue_size=switch_queue_size)

    set_link_properties(net, "h1", "s0", bent_pipe_link_bandwidth, unitialized_bent_pipe_delay, max_queue_size=switch_queue_size)
    set_link_properties(net, "h2", "s%s" % (intermediate_hop_num - 1), bent_pipe_link_bandwidth, unitialized_bent_pipe_delay, max_queue_size=switch_queue_size)

    # since available routing path has not been read yet, turn off the network by turning down s0<->s1 link
    # net.configLinkStatus('s0', 's1', 'down')

'''
    efficiently simulate the the handover interruption process if any and update the link latency
    given the new routing path or position change of satellites.
    handover interruption time formula is from the paper at https://ieeexplore.ieee.org/document/9014090
    the function is essentially the core part of the emulator, where the major dynamics occur.

    link_info_all_cycles: the data structure returned by read_link_info
    net: the mininet object
'''
def update_precomputed_link(link_info_all_cycles, net):
    print("cycle numbers:",len(link_info_all_cycles))
    global current_routing_path, last_routing_path, last_node_delay, current_node_delay

    # precompute the amount of delay for each prediction
    data_path = 'satcp/report_timing_error/comparsion_1_2/latency_deltas.mat'
    data = scio.loadmat(data_path)
    latency_deltas = data['latency_deltas']
    latency_deltas = latency_deltas[0]
    signness = [1, -1]
    prediction_delays = []
    for i in range(len(link_info_all_cycles)):
        prediction_delays.append(random.choice(latency_deltas) * random.choice(signness) + status_report_delayed_shift)
        # if you want perfect prediction...
        # prediction_delays.append(0)
    
    # precompute whether there will be handover at each cycle (so ealier cycle can decide whether to send ealier report for later cycle)
    handovers = [0]
    for i in range(1, len(link_info_all_cycles)):
        # check end handover
        last_cycle = link_info_all_cycles[i - 1]
        current_cycle = link_info_all_cycles[i]
        # no available path at current cycle: no handover
        if current_cycle[1] == "NULL":
            handovers.append(0)
            continue
        # just reconnect to the Internet: handover
        if last_cycle[1] == "NULL":
            handovers.append(1)
            continue
        current_routing_path = current_cycle[1]
        last_routing_path = last_cycle[1]
        # ingress/egress satellite change: handover
        if current_routing_path[1] != last_routing_path[1] or current_routing_path[-2] != last_routing_path[-2]:
            handovers.append(1)
            continue
        # check intermediate handover
        if sum(compute_link_delta(last_routing_path, current_routing_path)) != 0:
            handovers.append(1)
            continue
        # otherwise no handover
        handovers.append(0) 
        
    # go through each cycle and change the network properties accordingly
    for index in range(len(link_info_all_cycles)):
        tstart = time.time()
        cycle = link_info_all_cycles[index][0]
        print("cycle:", index)
        if index + 1!= cycle:
            print("not reading the correct cycle!")
            return

        # help trigger ealier handover reports for cycles later; will do for the next 3 cycles
        # for the next cycle
        if index + 1 < len(link_info_all_cycles) and -1 < prediction_delays[index + 1] < 0 and handovers[index + 1] == 1:
            subprocess.run(["echo", "earlier handover report triggered"], stdout=kernel_output)
            print("handover report for cycle %s with %s delay" % (str(index + 1), str(prediction_delays[index + 1])))
            report_handover_status_asynchronously(1, 1 - -prediction_delays[index + 1])
            
        # for the cycle after the next
        if index + 2 < len(link_info_all_cycles) and -2 < prediction_delays[index + 2] < -1 and handovers[index + 2] == 1:
            subprocess.run(["echo", "earlier handover report triggered"], stdout=kernel_output)
            print("handover report for cycle %s with %s delay" % (str(index + 2), str(prediction_delays[index + 2])))
            report_handover_status_asynchronously(1, 2 - -prediction_delays[index + 2])

        # for the cycle after the next
        if index + 3 < len(link_info_all_cycles) and -3 < prediction_delays[index + 3] < -2 and handovers[index + 3] == 1:
            subprocess.run(["echo", "earlier handover report triggered"], stdout=kernel_output)
            print("handover report for cycle %s with %s delay" % (str(index + 3), str(prediction_delays[index + 3])))
            report_handover_status_asynchronously(1, 3 - -prediction_delays[index + 3])

        # if at this cycle there is no routing path, turn down s0<->s1 link to
        # represent the service unavailability
        if link_info_all_cycles[index][1] == "NULL":
            current_routing_path = ["NULL"]
            current_node_delay = ["NULL"]
            net.configLinkStatus('s0', 's1', 'down')
            print("turn off the link due to lack of route")
            time.sleep(frame_length)
            continue
        
        # there is a valid routing path
        new_routing_path = link_info_all_cycles[index][1]
        node_num = link_info_all_cycles[index][2]
        node_delay = link_info_all_cycles[index][3]
        delay_sum = link_info_all_cycles[index][4]
        net.configLinkStatus('s0', 's1', 'up')

        # update the topology (i.e. routing path) accordingly
        last_routing_path = current_routing_path
        last_node_delay = current_node_delay
        current_routing_path = new_routing_path
        current_node_delay = node_delay

        # -------------------------HANDOVER PHASE (DISH <--> GATEWAY SATELLITE)-------------------------------------------
        # simulate handover interruption if the last gateway satellite is different than the current one
        user1_net_dish_sat_delay = None
        user2_net_dish_sat_delay = None
        # trigger handover if now we have a valid path
        if last_node_delay == ["NULL"]:
            user1_net_dish_sat_delay = (net, "s0", "s1", 3 * current_node_delay[0])
            user2_net_dish_sat_delay = (net, 's%s' % (intermediate_hop_num - 1), 's%s' % (intermediate_hop_num - 2), 3 * current_node_delay[-1])
        else:
            # if the gateway satellite at user 1 changes
            if current_routing_path[1] != last_routing_path[1]:
                handover_delay1 = 3 * last_node_delay[0] + 3 * current_node_delay[0]
                user1_net_dish_sat_delay = (net, "s0", "s1", handover_delay1)
            # if the gateway satellite at user 2 changes
            if current_routing_path[-2] != last_routing_path[-2]:
                handover_delay2 = 3 * last_node_delay[-1] + 3 * current_node_delay[-1]
                user2_net_dish_sat_delay = (net, 's%s' % (intermediate_hop_num - 1), 's%s' % (intermediate_hop_num - 2), handover_delay2)

        end_handover_nodes = []
        if user1_net_dish_sat_delay is not None:
            end_handover_nodes.append(user1_net_dish_sat_delay)
        if user2_net_dish_sat_delay is not None:
            end_handover_nodes.append(user2_net_dish_sat_delay)
        # -------------------------------------------------------------------------------------

        # -------------------------HANDOVER PHASE (INTERMEDIATE NODES)-------------------------------------------
        handover_arr = compute_link_delta(last_routing_path, current_routing_path)
        handover_nodes_group1 = []
        handover_nodes_group2 = []
        for i in range(0, len(handover_arr)):
            if handover_arr[i] == 1:
                # append if the last one is not i - 1 (avoid altering two interfaces of the same node at the same time)
                if not handover_nodes_group1 or handover_nodes_group1[-1][1] != i - 1:
                    handover_nodes_group1.append((net, i))
                else:
                    handover_nodes_group2.append((net, i))
                
        # since there can be multiple intermediate nodes experiencing handovers, using multithreading to simulate those
        # handovers in parallel (more authentic)
        print("cycle %s: intermediate handover nodes:" % index, handover_nodes_group1 + handover_nodes_group2)
        print("cycle %s: end handover nodes:" % index, end_handover_nodes)

        # send delayed handover report here
        if handover_nodes_group1 or handover_nodes_group2 or end_handover_nodes:
            if prediction_delays[index] >= 0:
                print("handover report for cycle %s with %s delay" % (str(index), str(prediction_delays[index])))
                report_handover_status_asynchronously(1, prediction_delays[index])
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor: 
            executor.map(simulate_link_break, handover_nodes_group1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor: 
            executor.map(simulate_link_break, handover_nodes_group2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor: 
            executor.map(simulate_dish_gateway_sat_handover, end_handover_nodes)

        # "handoff" process almost done: update the test locations' gateways (i.e. the delay and bandwidth between the ground and the gateway)
        dish_gateway_link_weight1 = node_delay[0]
        set_link_properties(net, "s0", "s1", 150, '%ss' % dish_gateway_link_weight1, max_queue_size=switch_queue_size)
        dish_gateway_link_weight2 = node_delay[-1]
        set_link_properties(net, 's%s' % (intermediate_hop_num - 2), 's%s' % (intermediate_hop_num - 1), 150, '%ss' % dish_gateway_link_weight2, max_queue_size=switch_queue_size)
        # -------------------------------------------------------------------------------------

        # -------------------------ROUTING PATH UPDATE PHASE-------------------------------------------
        # update each intermediate link's delay and bandwidth on the new path 
        # (not including links between entry satellite and user dish)
        for current_hop_idx in range(0, len(current_routing_path) - 3):
            # method from https://mailman.stanford.edu/pipermail/mininet-discuss/2013-December/003667.html
            weight = node_delay[current_hop_idx + 1]
            set_link_properties(net, "s%s" % (current_hop_idx + 1), "s%s" % str(current_hop_idx + 2), bent_pipe_link_bandwidth, '%ss' % weight, max_queue_size=switch_queue_size)

        # make sure links connecting extra dummy hops will not create burden for the new path
        for extra_hop_idx in range(len(current_routing_path) - 3, (intermediate_hop_num - 3)):
            set_link_properties(net, "s%s" % (extra_hop_idx + 1), "s%s" % str(extra_hop_idx + 2), bent_pipe_link_bandwidth, unitialized_bent_pipe_delay, max_queue_size=switch_queue_size)
        # -------------------------------------------------------------------------------------

        # sleep for extra time to reach one cycle duration
        tend = time.time()
        sleep_duration = frame_length - (tend - tstart)
        if sleep_duration < 0:
            sleep_duration = 0
        time.sleep(sleep_duration)

topos = { 'mytopo': ( lambda: MyTopo() ) }

'''
read the routing path information at each cycle precomputed by the second stage
so return a data structure that will contain the detailed routing information for each cycle, which will
be used as the input for the core simulation function update_precomputed_link().

input_file_name: the file containing the routing path information
'''
def read_link_info(input_file_name):
    global intermediate_hop_num

    link_info_all_cycles = []
    in_file = open("../precomputed_paths/" + input_file_name, "r")
    for line in in_file:
        values = line.split("$")
        if len(values) < 5:
            cycle_read = literal_eval(values[0])
            link_info_all_cycles.append([cycle_read, "NULL"])
        else:
            cycle_read = literal_eval(values[0])
            routing_path_read = literal_eval(values[1])
            node_num_read = literal_eval(values[2])
            if node_num_read > intermediate_hop_num:
                intermediate_hop_num = node_num_read
            node_delay_read = literal_eval(values[3])
            delay_sum_read = literal_eval(values[4])
            link_info_all_cycles.append([cycle_read, routing_path_read, node_num_read, node_delay_read, delay_sum_read])
    in_file.close()
    return link_info_all_cycles

def main():
    my_logger.info("START MININET LEO SATELLITE NETWORK SIMULATION!")
    links = read_link_info(path_info_file)
    my_topo = MyTopo()
    print("create the network")
    net = Mininet(topo=my_topo, link=TCLink, controller=None, xterms=False, host=CPULimitedHost, autoPinCpus=True, autoSetMacs=True)
    # NOTE: please turn on your own learning switch controller (e.x. the POX one provided in the repo)
    net.addController("c0",
                      controller=RemoteController,
                      ip=REMOTE_CONTROLLER_IP,
                      port=6633)
    print("start the network...")
    initialize_link(net)
    print("enter Mininet command line stage. here you can do prestage configuration. enter 'exit' to start the simulation")
    net.start()
    # enter interactive mode first to allow users to set up measurement tools like iPerf and ping on test hosts
    # e.g., run xterm h1 h2 to spawn the terminals for h1 and h2, and run iperf on them:
    # on host 2: iperf -s -i 0.2
    # on host 1: iperf -i 0.2 -t 1000000 -c 10.0.1.102 > iperf.log
    # type exit to leave the interactive mode
    CLI(net)
    # start dynamic simulation
    print("start dynamic link simulation")
    update_precomputed_link(links, net)

    net.stop()
    net.stopXterms()
    print("simulation successfully completed!")

if __name__ == '__main__':
    main()
