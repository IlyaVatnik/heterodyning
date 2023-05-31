import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,get_mode_ratio
from heterodyning.Hardware import scope,itla,keopsys,yokogawa
import matplotlib.pyplot as plt
import pickle

#%%

scope=scope.Scope('WINDOWS-E76DLEM')
#%%
trigger_channel=4
scope.macro_setup(channels_displayed=(1,2,4),
                 trace_points=0.2e6,
                 sampling_rate=10e9,
                 trigger='AUTO',
                 bandwidth='2E9',
                 trigger_channel=trigger_channel)




#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(3)

# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%
wavelength = 1550.36e-9 #no balance
LO_power=1500

#%%
pump_power=298
pump.set_power(pump_power)
folder='spectrogram_examples\\'
file_name='wavelength={} pump={} triggered={}'.format(wavelength*1e9,pump_power,trigger_channel)

#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
LO.on()
LO.mode('no dither')

pump.APCon()
#%%

plot_everything=True
scope.acquire()
trace_1=scope.get_data(1)
trace_2=scope.get_data(2)



win_time=10e-6
# IsAveraging=False
IsAveraging=True
average_freq_window=10e6
average_time_window=10e-6


real_power_ch1=160*2*1e-3
real_power_ch2=2*21*1e-3


spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   real_power_coeff=real_power_ch1,high_cut_off=2e9)
spec2=create_spectrogram_from_data(trace_2.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   real_power_coeff=real_power_ch2,high_cut_off=2e9)

                                  
if plot_everything:
    spec1.plot_spectrogram(scale='lin')
    spec2.plot_spectrogram(scale='lin')


mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=5,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=plot_everything)
# spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=10,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=True)
spec2.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=5,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=plot_everything)

all_modes_list=[]
if len(spec1.modes)>0 and len(spec2.modes)>0:
    all_modes_list=spec1.modes.copy()
    spec1_freqs=spec1.get_modes_freqs()
    for m in spec2.modes:
        if np.min(np.abs(m.freq-spec1_freqs))>average_freq_window:
            all_modes_list.append(m)
elif len(spec1.modes)>0:
    all_modes_list=spec1.modes.copy()
elif len(spec2.modes)>0:
    all_modes_list=spec2.modes.copy()
    


print('\n')
spec1.print_all_modes()
print('\n')
spec2.print_all_modes()
print('\n')
for i,mode in enumerate(all_modes_list):
    print('Mode {}, detuning={:.0f} MHz, life time={:.2f} ms, max power={:.3e} W\n'.format(i,mode.freq/1e6,mode.life_time*1e3,mode.max_power))
    
if len(all_modes_list)>0:
    all_modes_list.sort(key=lambda x:-x.max_power)
    for m in all_modes_list:
        power,Ratio1, Ratio_error1,_,_=get_mode_ratio(spec1,spec2,m)
        phi1=np.arctan(np.sqrt(Ratio1))
    # Ratio2, Ratio_error2,_,_=get_mode_ratio(spec1,spec2,mode2)
    # Ratio=Ratio1/Ratio2
    # phi2=np.arctan(np.sqrt(Ratio2))
    # phi_diffference=phi1-phi2
        print('mode at {:.0f} MHz, phi1={:.3f}, Ratio1={:.2f},'.format(m.freq/1e6,phi1,Ratio1))

#%%
LO.off()
pump.APCoff()

#%%
with open('example_trace 1 {}.pkl'.format(wavelength),'wb') as f:
    pickle.dump(trace_1,f)
with open('example_trace 2 {}.35.pkl'.format(wavelength),'wb') as f:
    pickle.dump(trace_2,f)
    
#%%
spec1.save_to_file('example ch1 real power.spec',as_object=False)
spec2.save_to_file('example ch2 real power.spec',as_object=False)
