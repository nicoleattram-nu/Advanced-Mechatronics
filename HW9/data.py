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

# FFT Sample Code 

Fs = len(t) / t[-1]  # sample rate
Ts = 1.0/Fs; # sampling interval
ts = np.arange(0,t[-1],Ts) # time vector
y = iir # the data to make the fft from (MAF or IIF--changed to make plots)
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
ax1.set_title(f"SigD IIF A = {A}") # changed to make plots
ax2.loglog(frq, Y_data, color="black")
ax2.loglog(frq,abs(Y),'b', color="red") # plotting the fft
ax2.set_xlabel('Freq (Hz)')
ax2.set_ylabel('|Y(freq)|')
plt.show()