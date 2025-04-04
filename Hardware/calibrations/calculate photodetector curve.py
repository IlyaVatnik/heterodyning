#%%
import numpy as np
import os
import matplotlib.pyplot as plt
import pickle
import scipy.signal as signal
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
import pickle
from scipy.interpolate import interp1d

folder=r"F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\2025.02-04 calibration of the system\data\\"
file_K1=r"F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\heterodyning\Hardware\calibrations\Rigol MSO8104 50 Om.txt"

P_LO=0.038e-3 # W
P_s=0.258e-3 # W
R_osc=50 # Ohm


data_K1=np.genfromtxt(file_K1,skip_header=2)
K1_spline=interp1d(data_K1[:,0], data_K1[:,1])
files=os.listdir(folder)

freqs=[]
K2=[]
for file in files:
    print(file)
    with open(folder+file,'rb') as f:
        trace=pickle.load(f)
    spec=create_spectrogram_from_data(trace.data,trace.xinc, IsAveraging=True,average_freq_window=10e6,win_time=2e-6)
    spec.find_modes()
    freq=spec.modes[0].freq*1e-6
    if freq>1200:
        continue
    freqs.append(freq)
    S_w=spec.modes[0].max_power
    K=np.sqrt(S_w)/(np.sqrt(2)*K1_spline(freq)*R_osc*np.sqrt(P_LO*P_s))
    K2.append(K)
    # spec.plot_spectrogram()

freqs=np.array(freqs)
ind=np.argsort(freqs)
freqs=freqs[ind]
K2=np.array(K2)
K2=K2[ind]
    
plt.figure()
plt.plot(freqs,K2)
plt.xlabel('Frequency, MHz')
plt.ylabel('Photodetector responce, A/W')
plt.savefig('Photodetector.png')

np.savetxt('photodetector.txt',np.column_stack((freqs,K2)),delimiter='\t')


