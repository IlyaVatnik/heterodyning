import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,get_mode_ratio
from heterodyning.Hardware import scope_rigol,itla,keopsys,yokogawa
import matplotlib.pyplot as plt
import pickle

#%%


scope_IP='10.2.60.112'


scope_scale = 0.1
scope_offset = -0.00
trigger_channel=1
scope_acq_time_set = 5e-3
sampling_rate=10e8
scope_trace_points_set = scope_acq_time_set*sampling_rate
scope=scope_rigol.Scope(scope_IP)
memory_depth, sampling_rate=scope.macro_setup(channels_displayed=(1,),
                                              acq_time=scope_acq_time_set,trace_points=scope_trace_points_set,
                                              channels_impedances={1:'FIFTy'},
                                              trigger='SINGLE')

scope.set_channel_scale(1,scope_scale)
scope.set_channel_offset(1, scope_offset)
scope.set_trigger_high_level()
# scope.set_channel_offset(1, -2.26)
scope.wait()

#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(5)

# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%
wavelength = 1550.36e-9 #no balance
LO_power=1600

#%%
pump_power=301
pump.set_power(pump_power)
folder='spectrogram_examples\\'
file_name='wavelength={} pump={} triggered={}'.format(wavelength*1e9,pump_power,trigger_channel)

#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
LO.on()
LO.mode('whisper')

pump.on()
#%%

plot_everything=True
success=False

scope.set_trigger_mode('SINGLE')
scope.trigger='SINGLe'
    # print(1)
    # scope.wait()
    # scope.force_trigger()
scope.acquire()
while True:
    trace_1=scope.get_data(1)
    if len(trace_1[0])>1:
        break




win_time=10e-6
# IsAveraging=False
IsAveraging=True
average_freq_window=2e6
average_time_window=10e-6


real_power_ch1=160*2*1e-3



spec1=create_spectrogram_from_data(trace_1[0],trace_1[1],IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   real_power_coeff=real_power_ch1,high_cut_off=2e9)

                                  
if plot_everything: 
    spec1.plot_spectrogram(scale='lin')



mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,
                 prominance_factor=1,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=plot_everything)
# spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=10,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=True)





spec1.print_all_modes()
spec1.plot_mode_dynamics(0)

#%%
LO.off()
pump.off() 

#%%
with open('example_trace 1 {}.pkl'.format(wavelength),'wb') as f:
    pickle.dump(trace_1,f)
    
#%%
spec1.save_to_file('example ch1 real power.spec',as_object=False)

