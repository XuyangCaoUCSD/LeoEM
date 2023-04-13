function [latency_delta] = compare_locations(tle_filename)
earth_radius = 6378;
startTime = datetime(2021,11,22,10,57,50);
stopTime = datetime(2021,11,22,10,57,59);
sampleTime = 1;
sc = satelliteScenario(startTime,stopTime,sampleTime);
sat = satellite(sc, tle_filename);
for idx = 1:numel(sat)
    name = sat(idx).Name + " Camera";
    conicalSensor(sat(idx),"Name",name,"MaxViewAngle",90);
end
cam = [sat.ConicalSensors];
name = "Geographical Site";
minElevationAngle = 30; % degrees
geoSite = groundStation(sc, ...
    "Name",name, ...
    "MinElevationAngle",minElevationAngle);
for idx = 1:numel(cam)
    access(cam(idx),geoSite);
end
% ac = [cam.Accesses];
% v = satelliteScenarioViewer(sc);
% fov = fieldOfView(cam());
% ecef_sat_location1 = states(sat(1), 'CoordinateFrame', 'ecef');
% ecef_sat_location2 = states(sat(2), 'CoordinateFrame', 'ecef');
% lla_sat_location1 = states(sat(1), 'CoordinateFrame', 'geographic');
% lla_sat_location2 = states(sat(2), 'CoordinateFrame', 'geographic');
format long g

current_ecef = states(sat(1), 'CoordinateFrame', 'ecef');
diff_m = [];
for idx = 2:numel(sat)
    ecef = states(sat(idx), 'CoordinateFrame', 'ecef');
    diff = abs((current_ecef - ecef));
    mean_diff = mean(diff,2);
    diff_m = [diff_m, mean_diff];
end

col_size = size(diff_m, 2);

dist_m = [];
for i = 1:col_size
    current_col = diff_m(:,i);
    dist = sqrt(current_col(1)^2 + current_col(2)^2 + current_col(3)^2) * ((earth_radius)/(earth_radius + 548));
    dist_m = [dist_m, dist];
end

% distance / Starlink LEO satellite travel speed
latency_delta = dist_m / 7000;
end

