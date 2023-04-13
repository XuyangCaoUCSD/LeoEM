new_sat_tle_map = dict();
old_sat_tle_map = dict();

new_snapshot_filename = "raw/starlink_new.txt";
old_snapshot_filename = "raw/starlink_old.txt";

new_snapshot_file = open(new_snapshot_filename, "r")
old_snapshot_file = open(old_snapshot_filename, "r")
current_sat = None

for line in new_snapshot_file:
    # if this is the satellite name line
    if len(line.split()) == 1 and "STARLINK" in line:
        current_sat = (line.split())[0]
        new_sat_tle_map[current_sat] = []
    # else this is the data line for the current satellite
    else:
        new_sat_tle_map[current_sat].append(line)

for line in old_snapshot_file:
    # if this is the satellite name line
    if len(line.split()) == 1 and "STARLINK" in line:
        current_sat = (line.split())[0]
        old_sat_tle_map[current_sat] = []
    # else this is the data line for the current satellite
    else:
        old_sat_tle_map[current_sat].append(line)

# collide and form snapshot comparsion tle
for sat in new_sat_tle_map:
    if sat not in old_sat_tle_map:
        continue
    sat_new_tle = new_sat_tle_map[sat]
    sat_old_tle = old_sat_tle_map[sat]
    if sat_new_tle == sat_old_tle:
        continue
    # since the new and old cannot have the same satellite identifier, change them
    sat_new_tle[0] = sat_new_tle[0][:2] + "1" + sat_new_tle[0][3:]
    sat_new_tle[1] = sat_new_tle[1][:2] + "1" + sat_new_tle[1][3:]
    sat_old_tle[0] = sat_old_tle[0][:2] + "2" + sat_old_tle[0][3:]
    sat_old_tle[1] = sat_old_tle[1][:2] + "2" + sat_old_tle[1][3:]
    f = open("comparsion_1_2/%s.tle" % sat, "w")
    f.write(sat + "_new")
    f.write("\n")
    f.write(sat_new_tle[0])
    f.write(sat_new_tle[1])
    f.write(sat + "_old")
    f.write("\n")
    f.write(sat_old_tle[0])
    f.write(sat_old_tle[1])

    f.close()
# for sat in old_sat_tle_map:
#     print(sat)

new_snapshot_file.close()
old_snapshot_file.close()

