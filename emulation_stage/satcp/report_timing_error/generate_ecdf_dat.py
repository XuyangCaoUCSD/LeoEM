import scipy.io as scio

data_path = 'comparsion_1_2/f_x_ecdf.mat'
data = scio.loadmat(data_path)

x_raw = data["x"]
y_raw = data["f"]

x = []
y = []

for point in x_raw:
    x.append(point[0])

for point in y_raw:
    y.append(point[0])

f_out = open("timing_err_ecdf.dat", "w")

for i in range(len(x)):
    f_out.write(str(x[i]))
    f_out.write("\t")
    f_out.write(str(y[i]))
    f_out.write("\n")

f_out.close()