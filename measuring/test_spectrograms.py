import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from heterodyning.Hardware import scope,itla,keopsys,yokogawa
import matplotlib.pyplot as plt
import pickle

#%%

scope=scope.Scope('WINDOWS-E76DLEM')
#%%
trigger_channel=4
scope.macro_setup(channels_displayed=(4,),
                 trace_points=80e6,
                 sampling_rate=2e9,
                 trigger='Trig',
                 trigger_channel=trigger_channel)



#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(4)

# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%
wavelength = 1550.35e-9 #no balance
LO_power=1500
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
#%%
pump_power=313
pump.set_power(pump_power)
folder='spectrogram_examples\\'
file_name='wavelength={} pump={} triggered={}'.format(wavelength*1e9,pump_power,trigger_channel)

#%%
LO.on()
LO.mode('no dither')
pump.APCon()
#%%

average_freq_window=1e6
average_time_window=100e-6
IsAveraging=True
win_time=3e-6
trace_1=scope.acquire_and_return(4)


spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window)

                                  

spec1.plot_spectrogram(scale='lin')


mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=True,prominance_factor=2,height=0.1e-9)
spec1.plot_all_modes()
spec1.print_all_modes()


#%%
LO.off()
pump.APCoff()
#%%
with open('example_trace.pkl','wb') as f:
    pickle.dump(trace_1,f)
