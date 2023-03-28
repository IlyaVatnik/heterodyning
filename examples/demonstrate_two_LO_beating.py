import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from heterodyning.Hardware import scope,itla,yokogawa
import matplotlib.pyplot as plt



scope=scope.Scope('WINDOWS-E76DLEM')
#%%
trigger_channel=1
scope.set_params(channels_displayed=(1,),
                 trace_points=80e6,
                 sampling_rate=10e9,
                 trigger='AUTO',
                 trigger_channel=trigger_channel)

#%%
LO1 = itla.PPCL550(4)
LO2 = itla.PPCL550(3)
# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()

#%%
wavelength1= 1550.300e-9 #no balance
wavelength2=1550.301e-9 #no balance
LO1_power=800
LO2_power=800



LO1.off()

LO2.off()
#freq3 = itla.m_Hz(wl3)
LO1.set_wavelength(wavelength1)
LO2.set_wavelength(wavelength1)
LO1.set_power(LO1_power)
LO2.set_power(LO2_power)

#%%
LO1.on()
LO2.on()

LO1.mode('whisper')
LO2.mode('dither')
# osa.acquire()
#%%
win_time=10e-6
overlap_time=win_time*0.8
average_freq_window=10e6
average_time_window=5e-6
IsAveraging=False

scope.acquire()
trace_1=scope.get_data(1)


spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,overlap_time=overlap_time,average_freq_window=average_freq_window,average_time_window=average_time_window)

                                  

spec1.plot_spectrogram(title='1')

#%%
LO1.off()
LO2.off()