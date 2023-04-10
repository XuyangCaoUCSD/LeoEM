# LeoEM: a Real-Time Low-Earth-Orbit Satellite Network Emulator 🛰️

### from *SaTCP: Link-Layer Informed TCP Adaptation for Highly Dynamic LEO Satellite Networks*, IEEE INFOCOM 2023

Xuyang Cao ([xuc054@eng.ucsd.edu](mailto:xuc054@eng.ucsd.edu)) and Prof. Xinyu Zhang ([xyzhang@eng.ucsd.edu](mailto:xyzhang@eng.ucsd.edu)) from University of California San Diego

LeoEM emulates highly dynamic low-Earth-Orbit (LEO) satellite networks (satnets) with crucial configurable parameters (e.g., whether to use inter-satellite laser or bent-pipe radio for the physical layer) and features (e.g., the presence of handovers). It faithfully represents not only the LEO satnets but also the network stack in the end hosts' OS, so any program can be natively run and evaluated over the dynamic links in real time. Not constrained by application-level simulation, the network has a high degree of real-time observability. For example, video streams can be exchanged between two ends of an emulated satnet path, isolated by two network namespaces. Meanwhile, the media quality can be directly monitored through playback. Therefore, LeoEM provides a powerful and flexible platform for researchers to experiment their innovations targeting LEO satellite networks.

## Overview

To use LeoEM, let's first understand the following high-level workflow and the function of each component. 

We can see LeoEM is divided into three stages. 

![Image: workflow.png](https://github.com/XuyangCaoUCSD/LeoEM/blob/main/workflow.png)

The details (e.g., prerequisites, setups, execution, and principles) of each component can be found in the README of its corresponding subdirectory.

### Stage 1: LEO Constellation Construction

Given our ultimate goal is to emulate the network, we will first derive the time-varying spatial data of all the network components in the constellation. I.e., satellites. In this way, we can calculate the connectivity among nodes, latency of a link, and candidate routes at a certain moment.

Essentially, you specify the key parameters of a LEO constellation in `constellation_params/`, which will then be fed into some orbit propogation software. The software will calculate the dynamic 3D location of the celestial object using reasonable orbit model, at certain frame rate, across one orbit period. In our case, those of all the satellites in the constellation will be computed and saved. For this purpose, we adopt StarPerf's solution and implementation. Big thanks to StarPerf and their detailed explainations to our questions. Please see `StarPerf_MATLAB_stage/` for details.

The spatial data output will reside in `constellation_output/`. 

Some LEO systems' data are available at StarPerf and you could directly use them for stage 2.

### Stage 2: Dynamic Route Computation

Knowing how nodes move over time from stage 1, you specify the source and destination. You also choose inter-satellite lasers or bent-pipe radios as the links. To use bent-pipe, ground station locations (`ground_stations.xlsx`) will be needed for relaying purpose. We adopt shortest-path/Dijkstra's algorithm for route computation with the propogation latency as the weight. We adopt yet modify StarPerf's route computation components. Big thanks to StarPerf again. Please see `route_stage/` for details.

Stage 2 hence outputs the precomputed end-to-end dynamic routes across one oribtal period, after which they just repeat. They reside in `precomputed_paths/`.

### Stage 3: Real-Time Network Emulation 

Finally, the route data from stage 2 will be fed to the emulator process(es), and now you can *experience* the LEO satnet! Specifically, two network namespaces will be created, and they are reachable from each other through the emulated dynamic network. Also, handovers and less-disruptive events will be introduced to the network as well. The underlying technology is Mininet and a set of Linux network utilities. Please see `emulation_stage/` for details.

What exciting is you can run (networked) programs natively on the two namespaces which represent two end UEs, and observe the behaviors of the entire real software network stack in real time. That means you can see how the physical dynamics may impact the IP-, transport-, application-layer implementations. Furthermore, you can modify the network stack in kernel or userspace to experiment your idea against the high network dynamics!

Please check each folder to start LeoEM, following the above workflow. Don't hesitate to ask us questions! 

## SaTCP

Another main contribution of the paper is SaTCP, a link-layer informed TCP adaptation that inhibit the congestion control when a handover is approaching. We also open-source our SaTCP implementation and the calculation of handover prediction error (i.e., report timing error in the paper). For details and the integration with LeoEM, please see `satcp/`. 

## Citing LeoEM or SaTCP
If you use LeoEM or SaTCP, please cite with the following BibTeX entry.
```bibtex
@inproceedings{caozhang2023satcp,
  title={SaTCP: Link-Layer Informed TCP Adaptation for Highly Dynamic LEO Satellite Networks,
  author={Cao, Xuyang and Zhang, Xinyu},
  year={2023},
  booktitle={IEEE INFOCOM 2023 - IEEE Conference on Computer Communications},
}
```























