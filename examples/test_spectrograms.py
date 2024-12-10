import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,get_mode_ratio
from heterodyning.Hardware import scope,itla,keopsys,yokogawa,scope_rigol
from heterodyning.Hardware.APEX_OSA import APEX_OSA_with_additional_features
import matplotlib.pyplot as plt
import pickle

#%%

# scope=scope.Scope('WINDOWS-E76DLEM')
scope=scope_rigol.Scope('169.254.146.7') # подключение осцил.
 #%%
scope.macro_setup(trace_points=8e6, # Кол-во точек для графика с осцил.
                  acq_time=12e-4) # временная развёртка для просмотра сигнала




#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(3)  # USB-порт подключения локального лазера

# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%
wavelength = 1550.3e-9 #no balance
LO_power=1300

#%%
pump_power=286
pump.set_power(pump_power)
folder='spectrogram_examples\\'
file_name='wavelength={} pump={} '.format(wavelength*1e9,pump_power)

#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
LO.on()
# LO.mode('no dither')
LO.mode('whisper')
LO.set_FTFrequency(0e6)

pump.APCon()

#%% APEX init
osa = APEX_OSA_with_additional_features('10.2.60.25')
osa.SetScaleXUnit(ScaleXUnit=1)
osa.change_range(1553.0,1555.0) # разрешение
osa.SetWavelengthResolution('low')

[x, y]=osa.acquire_spectrum()
plt.plot(x,y)
#%%
# scope.set_channel_offset(1, -0.349)
# scope.set
#%%
# блок записи для построения график

plot_everything=True
scope.trigger='SINGLe'
trace_1=scope.acquire_and_return(1)

#%%
# блок построения графиков



win_time=1e-6
# IsAveraging=False
IsAveraging=True
average_freq_window=1e6
average_time_window=30e-6


real_power_ch1=0




spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   real_power_coeff=real_power_ch1,high_cut_off=1e9,low_cut_off=100e6)

                                 
if plot_everything:
    spec1.plot_spectrogram(scale='log')


mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=plot_everything)
spec1.print_all_modes()

# spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=10,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=True)

# all_modes_list=[]
# if len(spec1.modes)>0 and len(spec2.modes)>0:
#     all_modes_list=spec1.modes.copy()
#     spec1_freqs=spec1.get_modes_freqs()
#     for m in spec2.modes:
#         if np.min(np.abs(m.freq-spec1_freqs))>average_freq_window:
#             all_modes_list.append(m)
# elif len(spec1.modes)>0:
#     all_modes_list=spec1.modes.copy()
# elif len(spec2.modes)>0:
#     all_modes_list=spec2.modes.copy()
    


# print('\n')
# spec1.print_all_modes()
# print('\n')
# spec2.print_all_modes()
# print('\n')
# for i,mode in enumerate(all_modes_list):
#     print('Mode {}, detuning={:.0f} MHz, life time={:.2f} ms, max power={:.3e} W\n'.format(i,mode.freq/1e6,mode.life_time*1e3,mode.max_power))
    
# if len(all_modes_list)>0:
#     all_modes_list.sort(key=lambda x:-x.max_power)
#     for m in all_modes_list:
#         power,Ratio1, Ratio_error1,_,_=get_mode_ratio(spec1,spec2,m)
#         phi1=np.arctan(np.sqrt(Ratio1))
#     # Ratio2, Ratio_error2,_,_=get_mode_ratio(spec1,spec2,mode2)
#     # Ratio=Ratio1/Ratio2
#     # phi2=np.arctan(np.sqrt(Ratio2))
#     # phi_diffference=phi1-phi2
#         print('mode at {:.0f} MHz, phi1={:.3f}, Ratio1={:.2f},'.format(m.freq/1e6,phi1,Ratio1))

#%%
LO.off()
pump.APCoff()

#%%
# with open('example_trace 1 {}.pkl'.format(wavelength),'wb') as f:
#     pickle.dump(trace_1,f)
# with open('example_trace 2 {}.35.pkl'.format(wavelength),'wb') as f:
#     pickle.dump(trace_2,f)
    
#%%
spec1.save_to_file('example.spec',as_object=False)
with open('example 1.trace','wb') as f:
    pickle.dump(trace_1,f)

