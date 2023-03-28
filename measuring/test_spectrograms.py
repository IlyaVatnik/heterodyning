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
                 trigger='TRIG',
                 trigger_channel=trigger_channel)
#%%


#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(4)

# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()

#%%

#%%
wavelength = 1550.35e-9 #no balance
LO_power=1400
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
#%%
pump_power=295
pump.set_power(pump_power)
folder='spectrogram_examples\\'
file_name='wavelength={} pump={} triggered={}'.format(wavelength*1e9,pump_power,trigger_channel)

#%%
LO.on()
LO.mode('whisper')
pump.APCon()
#%%

average_freq_window=3e6
average_time_window=100e-6

scope.acquire()
trace_1=scope.get_data(4)


spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=True,average_freq_window=average_freq_window,average_time_window=average_time_window)

                                  

spec1.plot_spectrogram(title='1')


mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=False,prominance_factor=3)
spec1.plot_all_modes()
spec1.print_all_modes()


#%%
LO.off()
pump.APCoff()
#%%
with open('example_trace.pkl','wb') as f:
    pickle.dump(trace_1,f)
