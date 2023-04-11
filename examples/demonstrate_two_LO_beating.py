import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from heterodyning.Hardware import scope,itla,yokogawa
import matplotlib.pyplot as plt

__version__='2'
__date__='2023.03.29'
#%%

scope=scope.Scope('WINDOWS-E76DLEM')
# scope=scope_rigol.Scope('RIGOL_DS8A2')
# scope=scope_rigol.Scope('168.0.0.1')
#%%
trigger_channel=4
scope.macro_setup(channels_displayed=(4,),
                  trace_points=1e6,
                  sampling_rate=20e9,
                  trigger='AUTO',
                  trigger_channel=trigger_channel)

#%%
LO1 = itla.PPCL550(3)
LO2 = itla.PPCL550(4)
# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()

#%%
wavelength1= 1550.000e-9 # in m 
wavelength2=1550.000e-9 # in m
LO1_power=1500 # in 0.01 dBm
LO2_power=1500 # in 0.01 dBm



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
LO2.mode('no dither')
# LO2.mode('dither')
# osa.acquire()
#%%
win_time=2e-6
overlap_time=win_time*0
average_freq_window=400e6
average_time_window=6e-7
IsAveraging=False

# scope.set_wfm_source(4)
    
trace_1=scope.acquire_and_return(4)

# trace_1 = scope.query_wave_fast()




spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,overlap_time=overlap_time,average_freq_window=average_freq_window,average_time_window=average_time_window)

                                  

spec1.plot_spectrogram()
spec1.find_modes(prominance_factor=2)
plt.ylim((spec1.modes[0].freq-250e6,spec1.modes[0].freq+350e6))
#%%
LO2.set_FTFrequency(1500e6) # fine tune in Hz

#%%
LO1.off()
LO2.off()
