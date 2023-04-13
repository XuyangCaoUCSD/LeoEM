## SaTCP Implementation

Please read the paper to understand the principle of SaTCP. 

### Principle

The implementation of SaTCP is the modified `tcp_cubic.c` in Linux kernel. `report_relay.c` is the disruptive-event report relay program at the userspace. Please see the following illustration:

<p align="center">
<img src="https://github.com/XuyangCaoUCSD/LeoEM/blob/main/emulation_stage/satcp/satcparch.jpg" width=50% height=50%>
</p>

When there is a coming disruptive event, `../emulator` will signal `report_relay` through a network socket. Then, `report_relay` will forward the signal to the modified CUBIC cc instances through [`netlink`](https://linux.die.net/man/7/netlink). Then, modified CUBIC will inhibit its congestion control properly. To highlight, `emulator` takes the handover prediction inaccuracy into consideration and may produce delayed or too early reports. We adopt the mechanism in the paper: send the report earlier by $T_{earlier}$ and increases the cc inhibition duration to $D$. 

You can configure $T_{earlier}$ in `../emulator.py` (in seconds):

$-T_{earlier}$ = `status_report_delayed_shift` 

You can configure $D$ in `report_relay.c`. Simply modify the value of `SATCP_DURATION` (in seconds).

### To Use SaTCP:

1. Have the Linux kernel source codes. Replace `source/net/ipv4/tcp_cubic.c` with the one we provided. Compile and use the kernel.  
2. Make sure you select CUBIC as the TCP congestion control algorithm. In Ubuntu:
```Bash
$ sudo sysctl net.ipv4.tcp_congestion_control=cubic
```
3. Compile `report_relay.c`:
```Bash
$ gcc -o report_relay report_relay.c -lpthread
```
4. Run report relay program:
```Bash
./report_relay
```

Done! Run the emulator following instructions in `../`, and see if you have better TCP throughput under the dynamic LEO satellite network!