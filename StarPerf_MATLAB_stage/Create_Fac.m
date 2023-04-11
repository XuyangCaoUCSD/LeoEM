function Create_Fac(conid)
disp('settings of Fac');
global No_fac Lat Long;
% San Diego, New York, London, Santiago, sydney, ground station 1, ground station 2,...
Lat = [32.88 40.74 51.51 -33.45, -33.89];
Long = [-117.23 -74.10 -0.11 -70.65, 151.20];

% add Starlink ground stations
ground_stations = readtable('../../Starlink_ground_stations.xlsx');
num_ground_stations = height(ground_stations)

for j=1:num_ground_stations
    Lat = [Lat ground_stations{j, 1}];
    Long = [Long ground_stations{j, 2}];
end
    
No_fac=length(Long)
for i=7:No_fac
    info_facility=strcat('Fac',num2str(i));
    stkNewObj('*/','Facility',info_facility);
    lat=Lat(i);
    long=Long(i);
    info_facility=strcat('Scenario/Matlab_Basic/Facility/',info_facility);
    stkSetFacPosLLA(info_facility, [lat*pi/180; long*pi/180; 0]);
    stkConnect(conid,'SetConstraint',info_facility,'ElevationAngle Min 20');
    num_fac(i)=i;
    
end
save('Num_fac.mat','num_fac');
end