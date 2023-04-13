## Network Emulation Stage

Finally, your host will experience the dynamic LEO satellite networks as per your requests in stage 1 and 2. 

### Prerequisites and Notes

* [Install Mininet from **source code**](https://github.com/mininet/mininet), as the emulator program relies on its libraries. Follow its `README.md` and especially `INSTALL`. Note: 
    * Before you build the source codes of Mininet, please replace `mininet/link.py` with `link_smooth.py` in `Mininet_config`. Then, rename `mininet/link_smooth.py` back to `mininet/link.py`.
      * Why? This was a decent-known bug in Mininet community. To change the link characteristics on the fly, Mininet actually did a "link teardown and recreation" with the updated values. This is convenient in terms of implementation, yet it creates an obvious artifact. The link should not be temporarily unavailable. See [this](https://github.com/mininet/mininet/pull/650) for more details.
    * Please do a full installation as per the instruction in `INSTALL`. E.g., the POX utility should also be installed for you. After that, put `learning_switch.py` in `~/pox/pox/misc`. This specifies the functionalities of the switching nodes (e.g., satellites and ground stations). You could customize it. 
* Please install Mininet and use the emulator on a physical, rather than virtual, machine. Besides performance reason, the emulator process shall have accurate time elapse. Can you guarantee that on a virtual machine? [Why?](https://www.vmware.com/content/dam/digitalmarketing/vmware/en/pdf/techpaper/Timekeeping-In-VirtualMachines.pdf)

### Use

Great! Let's run the emulator.

First, run this so network components in the emulator will be instructed to behave as learning switches (append `&` to run in the background):
```bash
$ python3 ~/pox/pox.py misc.learning_switch
```
Then start emulation (assume you are in `emulation_stage/`)!
```bash
$ python3 emulator.py route_filename
```
Where `route_filename` is the dynamic route output produced in stage 2. The program will seek the file name in `../precomputed_paths`.

For example, to start the emulation between San Diego and New York City with bent-pipe connectivity using Starlink Shell 1:
```bash
$ python3 emulator.py Starlink_SD_NY_15_BP_path.log
```

You will see the following interface:

<p align="center">
<img src="https://github.com/XuyangCaoUCSD/LeoEM/blob/main/emulation_stage/setup.png">
</p>

This is a "pre-emulation" phase. Before the emulation starts and the network becomes dynamic, here we give you the chance to start all the testing/logging programs in advance. For example, run `xterm h1 h2` will bring up the terminals for the two UEs. Start your programs there (which share the same file namespace as the emulator host).

Then run `exit` in the main interface. The emulation will start. You will see something like the following:

<p align="center">
<img src="https://github.com/XuyangCaoUCSD/LeoEM/blob/main/emulation_stage/run.png">
</p>

Assume your loggers will save data along the way. The emulation process lasts for one orbital period, which is embodied as the number of data points in the precomputed routes.  

Enjoy using! Let us know any questions or your feedback!

### Principle

How the handovers are determined?

Coming soon...
