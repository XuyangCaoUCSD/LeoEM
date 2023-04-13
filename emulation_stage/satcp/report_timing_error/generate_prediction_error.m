fileinfos = dir('comparsion_1_2/*.tle');
latency_deltas = [];
for file_idx = 1:numel(fileinfos)
    try
        filename = strcat('comparsion_1_2/', fileinfos(file_idx).name);
        latency_delta = compare_locations(filename);
        latency_deltas = [latency_deltas, latency_delta];
    catch exception
       continue
    end

end
% remove 0 (no-update) cases
latency_deltas = latency_deltas(latency_deltas~=0);
% remove outliers
latency_deltas = latency_deltas(latency_deltas<prctile(latency_deltas, 95));
% get a sense of how the mean looks like
latency_deltas_mean = mean(latency_deltas)
cdfplot(latency_deltas);





