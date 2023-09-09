import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,get_mode_ratio
from heterodyning.Hardware import scope,itla,keopsys,yokogawa,scope_rigol
import matplotlib.pyplot as plt
import pickle
import time

#%%

# scope=scope.Scope('WINDOWS-E76DLEM')
scope=scope_rigol.Scope('10.2.60.108')
 #%%
scope.macro_setup(trace_points=10e3,
                  acq_time=1e-6)




#%%

LO = itla.PPCL550(4)
LOax=itla.PPCL550(3)
# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%
wavelength= 1550.30e-9 #no balance
LO_power=1600

wavelength_ax= 1550.300e-9 #no balance
LO_power_ax=1500

#%%
LOax.off()
LOax.set_wavelength(wavelength_ax)
LOax.set_power(LO_power_ax)
LOax.set_FTFrequency(0)
LOax.on()
LOax.mode('no dither')
# LOax.mode('whisper')

#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
LO.set_FTFrequency(0)
LO.on()
# LO.mode('no dither')
LO.mode('whisper')

#%%
initial_freq_shift=00e6
LOax.set_FTFrequency(initial_freq_shift)
#%%
real_power_coeff=0
plot_everything=False
# scope.trigger='AUTO'
scope.trigger='SINGLe'

trace_1=scope.acquire_and_return(1)

win_time=1e-6
# IsAveraging=False
IsAveraging=True
average_freq_window=10e6
average_time_window=1e-6




spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   real_power_coeff=real_power_coeff,high_cut_off=1e9,low_cut_off=00e6)
                                  
if plot_everything:
    spec1.plot_spectrogram(scale='lin')

mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=plot_everything)
spec1.print_all_modes()

#%%

LO_real_power=0.72 # mW
LOax_real_power=1.8 # mW
real_power_coeff=0
# real_power_coeff=0.6254

N_average=50
freq_shift_step=10e6
powers_array=[]
freqs_array=[]
modes=[]
freq_shift=initial_freq_shift
#%%

for i in range(N_average):
    LOax.set_FTFrequency(freq_shift)
    freq_shift+=freq_shift_step
    time.sleep(0.2)
    trace_1=scope.acquire_and_return(1)
    spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   real_power_coeff=real_power_coeff,high_cut_off=1e9,low_cut_off=00e6)
    spec1.find_modes(indicate_modes_on_spectrogram=False,prominance_factor=3,height=1e-7,min_freq_spacing=2e6,plot_shrinked_spectrum=False)
    spec1.print_all_modes()
    if len(spec1.modes)>0:
        powers_array.append(spec1.modes[0].max_power)
        freqs_array.append(spec1.modes[0].freq)
        modes.append(spec1.modes[0])

# powers_array=np.array(powers_array)
# freqs_array=np.array(freqs_array)
print('\nPower is {:.3e} with std {:.3e} '.format(np.mean(powers_array),np.std(powers_array)))
print('Freqs changed from {:.4e} to {:.4e}'.format(np.min(freqs_array),np.max(freqs_array)))


plt.figure()
plt.plot(freqs_array,powers_array,'o')
plt.xlabel('Frequency, MHz')
plt.ylabel('Power measured, arb.u.')
plt.gca().set_xscale('log')
plt.gca().set_yscale('log')
#%%
np.savetxt('Balanced LO {:.2f} mW, LOax {:.2f} mW.txt'.format(LO_real_power, LOax_real_power),[freqs_array,powers_array])
    
#%%
LO.off() 
LOax.off()  

#%%
# with open('example_trace 1 {}.pkl'.format(wavelength),'wb') as f:
#     pickle.dump(trace_1,f)
# with open('example_trace 2 {}.35.pkl'.format(wavelength),'wb') as f:
#     pickle.dump(trace_2,f)
    