import csv
import matplotlib.pyplot as plt
import numpy as np

t = [] # column 0
data = [] # column 1

with open('sigD.csv') as f:
    # open the csv file
    reader = csv.reader(f)
    for row in reader:
        # read the rows 1 one by one
        t.append(float(row[0])) # leftmost column
        data.append(float(row[1])) # second column

for i in range(len(t)):
    # print the data to verify it was read
    print(str(t[i]) + ", " + str(data[i]))

# Moving Average
X = 500  # window size to tune
maf = []
for i in range(len(data)):
    window = data[max(0, i-X+1) : i+1]  # last X points (or fewer at the start)
    maf.append(sum(window) / len(window))

# IIR 
A = 0.5 
B = 1 - A

iir = []

for i in range(len(data)):
    iir.append( A * maf[i-1] + B * data[i])

# FIR 
weights = [
    0.000000000000000000,
-0.000011466433343440,
-0.000048159680438716,
-0.000070951498745996,
0.000000000000000000,
0.000226394896924650,
0.000570593070542985,
0.000843882357908127,
0.000742644459879189,
-0.000000000000000001,
-0.001387330856962112,
-0.002974017320060804,
-0.003876072294410999,
-0.003078546062261788,
0.000000000000000002,
0.004911281747189231,
0.009897689392343489,
0.012239432700612913,
0.009302643950572093,
-0.000000000000000005,
-0.013947257358995015,
-0.027649479941983943,
-0.034045985830080311,
-0.026173578588735643,
0.000000000000000007,
0.043288592274982135,
0.096612134128292462,
0.148460098539443669,
0.186178664190551207,
0.199977588313552862,
0.186178664190551235,
0.148460098539443669,
0.096612134128292462,
0.043288592274982128,
0.000000000000000007,
-0.026173578588735653,
-0.034045985830080325,
-0.027649479941983936,
-0.013947257358995019,
-0.000000000000000005,
0.009302643950572094,
0.012239432700612920,
0.009897689392343489,
0.004911281747189235,
0.000000000000000002,
-0.003078546062261790,
-0.003876072294411004,
-0.002974017320060808,
-0.001387330856962112,
-0.000000000000000001,
0.000742644459879189,
0.000843882357908127,
0.000570593070542984,
0.000226394896924650,
0.000000000000000000,
-0.000070951498745996,
-0.000048159680438716,
-0.000011466433343440,
0.000000000000000000
]

fir = []
for i in range(len(data)):
    val = 0
    for j in range(len(weights)):
        if i - j >= 0:
            val += weights[j] * data[i - j]
    fir.append(val)

samp_rate = 500
cut_off = 50
trans_band = 40

# FFT Sample Code 

Fs = len(t) / t[-1]  # sample rate
Ts = 1.0/Fs; # sampling interval
ts = np.arange(0,t[-1],Ts) # time vector
y = fir # the data to make the fft from (MAF or IIF--changed to make plots)
n = len(y) # length of the signal
k = np.arange(n)
T = n/Fs
frq = k/T # two sides frequency range
frq = frq[range(int(n/2))] # one side frequency range
Y = np.fft.fft(y)/n # fft computing and normalization
Y = Y[range(int(n/2))]
Y_data = np.fft.fft(data)/n
Y_data = abs(Y_data[range(int(n/2))])

fig, (ax1, ax2) = plt.subplots(2, 1)
ax1.plot(t,data, color = "black", label=f"IIR")
ax1.plot(t,y,'b', color = "red", label="original")
ax1.set_xlabel('Time')
ax1.set_ylabel('Amplitude')
ax1.set_title(f"SigD FIR Sampling Rate = {samp_rate}, Cutoff = {cut_off}, Transition Bandwidth = {trans_band}") # changed to make plots
ax2.loglog(frq, Y_data, color="black")
ax2.loglog(frq,abs(Y),'b', color="red") # plotting the fft
ax2.set_xlabel('Freq (Hz)')
ax2.set_ylabel('|Y(freq)|')
plt.show()