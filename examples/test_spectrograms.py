import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from heterodyning.Hardware import scope,itla,keopsys
import matplotlib.pyplot as plt

#%%

scope=scope.Scope('WINDOWS-E76DLEM')
#%%
trigger_channel=1
scope.set_params(channels_displayed=(1),
                 trace_points=5e6,
                 sampling_rate=2e9,
                 trigger='TRIG',
                 trigger_channel=trigger_channel)
#%%
# trace=scope.acquire_and_return(1)
# plt.plot(trace.data)


#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(4)
LO.off()

#%%

#%%
wavelength = 1550.5e-9 #no balance
LO_power=1400
#freq3 = itla.m_Hz(wl3)
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
pump_power=296
pump.set_power(pump_power)
folder='spectrogram_examples\\'
file_name='wavelength={} pump={} triggered={}'.format(wavelength*1e9,pump_power,trigger_channel)

#%%
LO.on()
pump.APCon()
LO.mode('whisper')
#%%

average_freq_window=30e6
average_time_window=10e-6

scope.acquire()
trace_1=scope.get_data(1)


spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=True,average_freq_window=average_freq_window,average_time_window=average_time_window)

                                  

spec1.plot_spectrogram(title='1')


mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=True,prominance_factor=3)
if len(spec1.modes)>0:
    for mode_number,_ in enumerate(spec1.modes):
        spec1.plot_mode_dynamics(mode_number)

#%%
LO.off()
pump.APCoff()
