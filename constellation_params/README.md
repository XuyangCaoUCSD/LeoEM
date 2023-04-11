## LEO Constellation Parameter Specification

(Adopting StarPerf's Framework)

Please specify the following key parameters in `parameter.xlsx`, following the self-explanatory format:

* Name: just a unique identifier of the constellation.
* Altitude: the altitude of satellites. See the visualization.
* Cycle: the orbital period (in seconds). I.e., the time it takes for a satellite to go back to the original spatial point.
* Inclination: the angle between orbits and the equator. See the visualization.
* Phase shift: the amount of shift of same-index satellites on two adjacent orbits. Usually it is 0. 
* Number of orbits: as name suggests. See the visualization.
* Number of satellites: the number of satellites on each orbit. Therefore, number of orbits × number of satellites = total satellite number in the constellation.

Visualization of Starlink Shell 1 constellation:


<img src="https://github.com/XuyangCaoUCSD/LeoEM/blob/main/constellation_params/starlink_visualization.jpg" width=50% height=50%>

<!-- ![Image: starlink_visualization.jpg](https://github.com/XuyangCaoUCSD/LeoEM/blob/main/constellation_params/starlink_visualization.jpg) -->

Then we can move to the stage 1: `StarPerf_MATLAB_stage/`.

