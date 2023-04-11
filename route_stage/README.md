## Route Computation

We pre-compute the time-varying route between two endpoints using the time-varying spatial data calculated from the previous stage.

### Usage:

```bash
route_stage % python3 precompute_path_15s_isl.py|precompute_path_15s_bp.py constellation output_filename sat_num cycle latitude_1 longitude_1 latitude_2 longitude_2 depression_angle elevation_angle
```

* To use inter-satellite laser link, choose `precompute_path_15s_isl.py`. To use bent-pipe radio link, choose `precompute_path_15s_bp.py`.
* `constellation`: the LEO constellation name. The program will seek spatial data in `../constellation_outputs/$constellation/`. 
* `output_filename`: the output filename. The file will be generated in `../precomputed_paths/`.
* `sat_num`: total satellite number in the constellation. You should know it in stage 1.
* `cycle`: the orbital period length (in seconds). You should know it in stage 1.
* `latitude_1`: the latitude of the first endpoint you choose. In degree.
* `longitude_1`: the longitude of the first endpoint you choose. In degree.
* `latitude_2`: the latitude of the second endpoint you choose. In degree.
* `longitude_2`: the longitude of the second endpoint you choose. In degree.
* `depression_angle`: please refer to the figure in Principle subsection. In degree.
* `elevation_angle`: please refer to the figure in Principle subsection. In degree.

Also specify all the rely ground stations' locations in `../ground_stations.xlsx`, if you use bent-pipe links. The given one has Starlink's *discovered* ground stations from [here](https://satellitemap.space/).

For example, to compute the dynamic ISL routes between San Diego and New York City using Starlink Shell 1 (whose spatial data has been computed in stage 1):

```bash
route_stage % python3 precompute_path_15s_isl.py Starlink Starlink_SD_NY_15_ISL_path.log 1584 5731 32.881 -117.237 40.845 -73.932 44.85 40
```

To compute the dynamic bent-pipe routes between San Diego and Seattle using Starlink Shell 1:

```bash
route_stage % python3 precompute_path_15s_bp.py Starlink Starlink_SD_SEA_15_BP_path.log 1584 5731 32.881 -117.237 47.608 -122.335 44.85 40
```

### Principle

Explanation of mathematical function `getCoverageLimitL` in `utility.py`:

<p align="center">
<img src="https://github.com/XuyangCaoUCSD/LeoEM/blob/main/route_stage/cover.jpg" width=50% height=50%>
</p>

* $\beta: \text{depression angle}$
* $\alpha: \text{(maximum) elevation angle}$
* $H: \text{satellite altitude}$
* $R: \text{Earth's radius}$
* Objective: to derive $L$, the maximum distance within which this satellite shall communicate.

$$\gamma = \frac{\pi}{2} - (\alpha + \beta)$$

$$\theta = \frac{\pi - \gamma}{2}$$

$$d_1 = R * \sin(\gamma)$$

$$d_2 = \frac{d_1}{\tan(\theta)}$$

$$L = \sqrt{(H + d_2)^2 + (d_1)^2}$$

<p align="center">
<img src="https://github.com/XuyangCaoUCSD/LeoEM/blob/main/route_stage/elevation.jpg" width=50% height=50%>
</p>

From the ground perspective, smaller maximum elevation angle, greater circular coverage yet easier line-of-sight blockage will be. 

How we compute the routes? 

We follow the Starlink's official description, [that handoff is considered on a 15-second interval](https://www.globalsecurity.org/space/systems/starlink.htm). Indeed, instead of constantly switching, a reasonable pace reduces the network dynamics.

Therefore, we use the following procedure:
* $counter \gets 0$
* For every moment:
  * If there is no connectivity between two endpoints:
    * Re-seek ingress satellite(s) on two ends. Use the ones that can form the shortest path.
    * $counter \gets 0$
  * Else:
    * If $counter = 15$:
      * Re-seek ingress satellite(s) on two ends. Use the ones that can form the shortest path.
      * $counter \gets 0$
    * $counter \gets counter + 1$



