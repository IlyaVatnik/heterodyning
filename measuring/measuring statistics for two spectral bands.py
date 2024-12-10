# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 18:10:36 2024

@author: Илья
"""

import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,get_mode_ratio
from heterodyning.Hardware import scope_rigol,itla,keopsys,yokogawa
from heterodyning.Hardware.APEX_OSA import APEX_OSA_with_additional_features
import matplotlib.pyplot as plt
import pickle
from heterodyning import study_correlations
import time


# scope=scope.Scope('WINDOWS-E76DLEM')

#%%
osa = APEX_OSA_with_additional_features('10.2.60.25')
osa.SetScaleXUnit(ScaleXUnit=1)
osa.change_range(1550.3,1550.5) # 
osa.SetWavelengthResolution('High')
 #%%
scope=scope_rigol.Scope('10.2.60.149') # подключение осцил.
#%%
scope.macro_setup(channels_displayed = (1,2),
                  trace_points=1e6, # Кол-во точек для графика с осцил.
                  acq_time=1e-3) # временная развёртка для просмотра сигнала




#%%
pump = keopsys.Keopsys('10.2.60.244')
#%%
LO1= itla.PPCL550(3)  # USB-порт подключения локального лазера
LO2= itla.PPCL550(4)  # USB-порт подключения локального лазера

# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%
stokes_number=1
wavelength_1 = 1550.3e-9 #no balance
LO1_power=1500
wavelength_2 = wavelength_1+stokes_number*study_correlations.stokes_detuning/125e9*1e-9 #no balance
LO2_power=1300
LO2_detuning=0e6
#%%
pump_power=297
pump.set_power(pump_power)


#%%
LO1.off()
LO1.set_wavelength(wavelength_1)
LO1.set_power(LO1_power)
LO1.on()
# LO.mode('no dither')
LO1.mode('whisper')
LO1.set_FTFrequency(0e6)

LO2.off()
LO2.set_wavelength(wavelength_2)
LO2.set_power(LO2_power)
LO2.on()
LO2.mode('no dither')
# LO2.mode('whisper')
#%%
LO1.set_FTFrequency(-1e9)
LO2.set_FTFrequency(2e9)

#%%
pump.APCon()

#%% APEX init
def get_detuning():
    try:
        [x, y]=osa.acquire_spectrum()
        # plt.plot(x,y)
        detuning=study_correlations.get_detuning_of_two_LO(x,y)
        print('detuning={:.3f} GHz'.format(detuning/1e9))
    except IndexError:
        print('no sufficient peaks found in the spectrum')
        return 0
    return detuning
detuning=get_detuning()
#%%
def single_test():
    
    plot_everything=True
    scope.trigger='SINGLe'
    trace_init=scope.acquire_and_return(2)
    trace_stokes=scope.get_data(1)
    
    win_time=1e-6
      # IsAveraging=False
    IsAveraging=True
    average_freq_window=4e6
    average_time_window=10e-6
    
    real_power_ch1=0
    
    spec1=create_spectrogram_from_data(trace_init.data,trace_init.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                        real_power_coeff=real_power_ch1,high_cut_off=4e9,low_cut_off=50e6)
    spec2=create_spectrogram_from_data(trace_stokes.data,trace_stokes.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                        real_power_coeff=real_power_ch1,high_cut_off=4e9,low_cut_off=50e6)
    
    spec1.plot_spectrogram(scale='log')
    spec2.plot_spectrogram(scale='log')
    spec1.find_modes(indicate_modes_on_spectrogram=True,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=False)
    spec2.find_modes(indicate_modes_on_spectrogram=True,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=False)
     
    spec1.print_all_modes()
    spec2.print_all_modes()
    pair_list=study_correlations.create_list_of_simult_stokes_modes(spec1.modes, spec2.modes,detuning,stokes_number,
                                                  print_lists=True)
    print(pair_list)

        
    # for l in pair_list:
        # correlation_shift,error_of_stokes_freq,error_time=study_correlations.get_correlation_time(spec1,spec2,detuning,stokes_number,l[2],l[3],l[4],plot=True)
        # print('{:.2f} mks, error = {:.2f} MHz, error_time={:.2f} mks'.format(correlation_shift*1e6,error_of_stokes_freq/1e6,error_time*1e6))
    
def acquire_data():
    try:
        scope.trigger='SINGLe'
        stability_time_of_laser_wavelengths=30 #s            
        win_time=1e-6
          # IsAveraging=False
        IsAveraging=True
        average_freq_window=4e6
        average_time_window=10e-6
        real_power_ch1=0
        detuning=get_detuning()
        for i in range(30):
            time1=time.time()
            while True:
                if (time.time()-time1)>stability_time_of_laser_wavelengths:
                    detuning=get_detuning()
                    time1=time.time()
                trace_init=scope.acquire_and_return(2)
                trace_stokes=scope.get_data(1)
                
                spec1=create_spectrogram_from_data(trace_init.data,trace_init.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                                    real_power_coeff=real_power_ch1,high_cut_off=4e9,low_cut_off=50e6)
                spec2=create_spectrogram_from_data(trace_stokes.data,trace_stokes.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                                    real_power_coeff=real_power_ch1,high_cut_off=4e9,low_cut_off=50e6)
                
                
                spec1.find_modes(indicate_modes_on_spectrogram=False,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=False)
                spec2.find_modes(indicate_modes_on_spectrogram=False,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=False)
                 
                pair_list=study_correlations.create_list_of_simult_stokes_modes(spec1.modes, spec2.modes,detuning,stokes_number,
                                                              print_lists=True,acceptable_time_error=500e-6)
                if len(pair_list)>0:
                    print(pair_list)
                    
                    with open('data\\{} detuning={:.3f} GHz.pkl'.format(i,detuning/1e9),'wb') as f:
                        pickle.dump([trace_init,trace_stokes],f)
                    print('saved to file')
                    break
    except Exception as e:
        print(e)
        pump.APCoff()
        LO1.off()
        LO2.off()
        

#%%
detuning=get_detuning()
#%%
single_test()
#%%
acquire_data()
pump.APCoff()
LO1.off()
LO2.off()
#%%
pump.APCoff()
LO1.off()
LO2.off()
