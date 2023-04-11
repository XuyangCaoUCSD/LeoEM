"""
    read the constellation output from StarPerf's Matlab stage

    generate only the necessary link information at each cycle for the network emulator,
    so the emulator can directly access the information and change the link properties 
    without repeatedly computing the same link information on the fly

    inter-satellite laser +Grid connectivity is used

    handover strategies used (align with Starlink's 15-sec handoff description)
    * for every cycle, check if the current gateway can still form a path to the destination:
        * if not: find the closest satellite as the new gateway and retry to form a new path. Reset the 15 seconds counter
        * if so:
            if not reach 15 seconds yet, continue to use the current gateway
            if 15 seconds already, find the closest satellite as the new gateway and retry to form a new path; reset the 15 seconds counter
"""

import networkx as nx
import scipy.io as scio
import math
import sys
import math
from utility import *

if len(sys.argv) != 11:
    print("need to specify the name of folder containing the constellation info from StarPerf Matlab stage as the second argument!") # 2
    print("need to specify the name of (routing path) output file as the third argument!") # 3
    print("need to specify the number of satellites as the fourth argument!") # 4
    print("need to specify the number of cycles as the fifth argument!") # 5
    print("need to specify the latitude and longitude of test location 1 as the sixth and seventh argument!") # 6, 7
    print("need to specify the latitude and longitude of test location 2 as the eighth and ninth argument!") # 8, 9
    print("need to specify the depression and elevation angles of the constellation as the tenth and eleventh argument!") # 10, 11
    exit()

constellation_folder_name = sys.argv[1]
output_file_name = sys.argv[2]
satellite_num = int(sys.argv[3])
cycles = int(sys.argv[4])
test_1_lla = (float(sys.argv[5]), float(sys.argv[6]), 0)
test_2_lla = (float(sys.argv[7]), float(sys.argv[8]), 0)
test_1_cbf, test_2_cbf = lla2cbf(test_1_lla), lla2cbf(test_2_lla)
depression, elevation = float(sys.argv[9]), float(sys.argv[10])
central_angle = 180 - 2 * (depression + elevation)

# read the positions for satellites
data_path = 'constellation_outputs/' + constellation_folder_name + '/position.mat'
data = scio.loadmat(data_path)
# positions[satellite_id][0][l/l/a][cycle]
positions = data['position']
cbf_positions = data['position_cbf']

output_file = open("../precomputed_paths/" + output_file_name, "w")
node_nums = []
no_path_cycle_num = 0

# counters for user 1 and user 2 that remind them to switch gateway satellites
counter1 = 0
counter2 = 0
# previously used gateway satellites
test_1_gateway_pervious = [math.inf, -1]
test_2_gateway_pervious = [math.inf, -1]
# what satellites are currently covering user 1 and user 2
satellites_in_view1 = []
satellites_in_view2 = []

L = getCoverageLimitL(elevation, depression, 550 * 10 ** 3)
# start generating the desired path between two test locations
for current_cycle in range(1, cycles + 1):
    print("cycle", current_cycle)
    try:
        G = nx.Graph()
        edges = []
        G.add_nodes_from(range(satellite_num))
        # determine the best entry satellite
        # use the min-distance criteria
        # find the closest satellite/gateway for each test location: [delay, satellite_number]
        min_test_1_gateway = [math.inf, -1]
        min_test_2_gateway = [math.inf, -1]
        satellites_in_view1 = []
        satellites_in_view2 = []
        # check if a satellite is covering a ground station / test location
        # if so, build the edge between the satellite and ground station vertice
        for satellite_id in range(0, satellite_num):
            satellite_lla = (positions[satellite_id][0][0][current_cycle - 1], positions[satellite_id][0][1][current_cycle - 1], positions[satellite_id][0][2][current_cycle - 1])
            satellite_cbf = (cbf_positions[satellite_id][0][0][current_cycle - 1], cbf_positions[satellite_id][0][1][current_cycle - 1], cbf_positions[satellite_id][0][2][current_cycle - 1])
            # check the satellite coverage for the test location 1
            test_1_covered = checkSatCoverGroundStation(satellite_cbf, test_1_cbf, L)
            if test_1_covered:
                sat_t1_latency = computeLatency(satellite_cbf, test_1_cbf)
                satellites_in_view1.append([sat_t1_latency, satellite_id])
                if sat_t1_latency < min_test_1_gateway[0]:
                    min_test_1_gateway[0], min_test_1_gateway[1] = sat_t1_latency, satellite_id
            # check the satellite coverage for the test location 2
            test_2_covered = checkSatCoverGroundStation(satellite_cbf, test_2_cbf, L)
            if test_2_covered:
                sat_t2_latency = computeLatency(satellite_cbf, test_2_cbf)
                satellites_in_view2.append([sat_t2_latency, satellite_id])
                if sat_t2_latency < min_test_2_gateway[0]:
                    min_test_2_gateway[0], min_test_2_gateway[1] = sat_t2_latency, satellite_id


        # load latency data (+Grid connectivity)
        latency_data_path = 'constellation_outputs/' + constellation_folder_name + '/delay/' + str(current_cycle) + '.mat'
        latency_data = scio.loadmat(latency_data_path)
        delay = latency_data['delay']
        for i in range(satellite_num):
            for j in range(i + 1, satellite_num):
                if delay[i][j] > 0:
                    edges.append((i, j, (delay[i][j])/1000))
        G.add_weighted_edges_from(edges)

        # continue to use the previous gateway
        test_1_gateway = test_1_gateway_pervious
        test_2_gateway = test_2_gateway_pervious

        '''
        determine whether to select a new gateway
        according to Starlink federal file:

        "Because the Starlink satellites are constantly moving, the
        network plans these connections on 15 second intervals, continuously re-generating and
        publishing a schedule of connections to the satellite fleet and handing off connections between
        satellites."
        '''
        if pathExists(test_1_gateway[1], test_2_gateway[1], G):
            # if the gateway(s) already used for 15 seconds, the signal can be poor and find a new gw
            if counter1 == 15:
                test_1_gateway = min_test_1_gateway
            if counter2 == 15:
                test_2_gateway = min_test_2_gateway
        else:
            # path does not exists, force the connection to a new gateway satellite then
            # try just the test 1 side
            if pathExists(min_test_1_gateway[1], test_2_gateway[1], G):
                test_1_gateway = min_test_1_gateway
                # reset the counter
                counter1 = 15
            # try just the test 2 side
            elif pathExists(test_1_gateway[1], min_test_2_gateway[1], G):
                test_2_gateway = min_test_2_gateway
                counter2 = 15
            # update both sides' gws, as there are no other choice remaining
            else:
                test_1_gateway = min_test_1_gateway
                test_2_gateway = min_test_2_gateway
                counter1 = 15
                counter2 = 15
        
        # if the two selected gateways still cannot form a valid routing path, check if we can use another less optimal (further) gateway combination
        if not pathExists(test_1_gateway[1], test_2_gateway[1], G):
            alternative_test_1_gateway = [math.inf, -1]
            alternative_test_2_gateway = [math.inf, -1]
            print("satellites in view for 1:", satellites_in_view1)
            print("satellites in view for 2:", satellites_in_view2)
            for sat1 in satellites_in_view1:
                for sat2 in satellites_in_view2:
                    if pathExists(sat1[1], sat2[1], G):
                        if (sat1[0] + sat2[0]) < (alternative_test_1_gateway[0] + alternative_test_2_gateway[0]):
                            alternative_test_1_gateway, alternative_test_2_gateway = sat1, sat2
        
            if pathExists(alternative_test_1_gateway[1], alternative_test_2_gateway[1], G):
                test_1_gateway, test_2_gateway = alternative_test_1_gateway, alternative_test_2_gateway
                print("alternative less optimal gateway combination found!")
                counter1 = 15
                counter2 = 15

        print("gw1:", test_1_gateway[1])
        print("gw2:", test_2_gateway[1])
        # some updates
        test_1_gateway_pervious = test_1_gateway
        test_2_gateway_pervious = test_2_gateway
        if counter1 == 15:
            counter1 = 0
        else:
            counter1 += 1
        if counter2 == 15:
            counter2 = 0
        else:
            counter2 += 1

        # start generating the actual routing path details
        if test_1_gateway[1] == -1 or test_2_gateway[1] == -1:
            raise nx.exception.NetworkXNoPath

        routing_path = nx.dijkstra_path(G, test_1_gateway[1], test_2_gateway[1])
        node_num = len(routing_path)
        node_delay = [test_1_gateway[0]]
        for i in range(node_num - 1):
            node_delay.append(G.get_edge_data(routing_path[i], routing_path[i + 1])['weight'])
        node_delay.append(test_2_gateway[0])
        routing_path.insert(0, -1)
        routing_path.append(-2)
        delay_sum = sum(node_delay)
        node_num += 2
        node_nums.append(node_num)
        output_file.write(str(current_cycle))
        output_file.write("$")
        output_file.write(str(routing_path))
        output_file.write("$")
        output_file.write(str(node_num))
        output_file.write("$")
        output_file.write(str(node_delay))
        output_file.write("$")
        output_file.write(str(delay_sum))
        output_file.write("\n")
    except nx.exception.NetworkXNoPath:
        no_path_cycle_num += 1
        output_file.write(str(current_cycle))
        output_file.write("$")
        output_file.write("NULL")
        output_file.write("\n")
    
output_file.close()
print("max number of hops needed is %s" % str(max(node_nums)))
print("percentage of time there is no route: %s" % str(no_path_cycle_num / float(cycles)))
print("all link information has been written to %s" % output_file_name)
exit()