import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,get_mode_ratio
from heterodyning.Hardware import scope,itla,keopsys,yokogawa,scope_rigol
import matplotlib.pyplot as plt
import pickle

#%%

# scope=scope.Scope('WINDOWS-E76DLEM')
scope=scope_rigol.Scope('10.2.60.108')
 #%%
scope.macro_setup(trace_points=100e3,
                  acq_time=1e-5)




#%%

LO = itla.PPCL550(4)
LOax=itla.PPCL550(3)
# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%
wavelength= 1550.31e-9 #no balance
LO_power=1400

wavelength_ax= 1550.305e-9 #no balance
LO_power_ax=1800

#%%
LOax.off()
LOax.set_wavelength(wavelength)
LOax.set_power(LO_power_ax)
LOax.on()
LOax.mode('no dither')
# LOax.mode('whisper')

#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
LO.on()
# LO.mode('no dither')
LO.mode('whisper')
#%%
# scope.set_channel_offset(1, -0.349)
# scope.set
scope.set_channel_scale(1, 1)

real_power_ch1=0
scope.trigger='AUTO'
trace_1=scope.acquire_and_return(1)
mean_level=np.mean(trace_1.data)
print('Mean level is {:.3f} V'.format(mean_level))

scope.set_channel_scale(1, 0.01)
scope.set_channel_offset(1, -mean_level)
#%%
LO.set_FTFrequency(-400e6)
#%%
real_power_coeff=70
plot_everything=True
scope.trigger='SINGLe'
trace_1=scope.acquire_and_return(1)

win_time=1e-6
# IsAveraging=False
IsAveraging=True
average_freq_window=5e6
average_time_window=5e-6




spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   real_power_coeff=real_power_coeff,high_cut_off=1e9,low_cut_off=00e6)
                                  
if plot_everything:
    spec1.plot_spectrogram(scale='lin')

mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=plot_everything)
spec1.print_all_modes()

#%%

real_power=40e-6 # W
real_power_coeff=0
# real_power_coeff=0.6254

N_average=20
powers_array=[]
freqs_array=[]
for i in range(N_average):
    trace_1=scope.acquire_and_return(1)
    spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   real_power_coeff=real_power_coeff,high_cut_off=1e9,low_cut_off=00e6)
    spec1.find_modes(indicate_modes_on_spectrogram=False,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=False)
    spec1.print_all_modes()
    powers_array.append(spec1.modes[0].max_power)
    freqs_array.append(spec1.modes[0].freq)

powers_array=np.array(powers_array)
freqs_array=np.array(freqs_array)
print('\nPower is {:.3e} with std {:.3e} '.format(np.mean(powers_array),np.std(powers_array)))
print('Freqs changed from {:.4e} to {:.4e}'.format(np.min(freqs_array),np.max(freqs_array)))

print('coeff is {:.3f} with std {:.3f}'.format(real_power/np.mean(powers_array), real_power/np.mean(powers_array)**2*np.std(powers_array) ))   # real power divided by measured arb.u.
    
#%%
LO.off()
LOax.off() 

#%%
# with open('example_trace 1 {}.pkl'.format(wavelength),'wb') as f:
#     pickle.dump(trace_1,f)
# with open('example_trace 2 {}.35.pkl'.format(wavelength),'wb') as f:
#     pickle.dump(trace_2,f)
    
#%%
spec1.save_to_file('example 9.spec',as_object=False)
with open('example odd.trace','wb') as f:
    pickle.dump(trace_1,f)

