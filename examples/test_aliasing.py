#%%
import numpy as np
import os
import matplotlib.pyplot as plt
import pickle
import scipy.signal as signal
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
import pickle
from heterodyning import study_correlations


sampling_rate=2e9 # GS/s


signal_frequency=1.2e9 #GHz
signal_duration=100e-6

xinc=1/sampling_rate 
signal=np.sin(2*np.pi*signal_frequency*np.arange(0,signal_duration,xinc))

signal[:len(signal)//4]=0
signal[3*len(signal)//4:]=0


win_time=3e-6
IsAveraging=False
# IsAveraging=True
average_freq_window=5e6
average_time_window=5e-6

spec=create_spectrogram_from_data(signal,xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                    real_power_coeff=0,high_cut_off=4e9,low_cut_off=50e6)


spec.plot_spectrogram()
spec.find_modes()
spec.plot_mode_dynamics(0)
