'''
Measuring modes in two channels and calculate those ratio
'''

import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,Mode,get_ratio
from heterodyning.Hardware import scope,itla,keopsys
import matplotlib.pyplot as plt
import pickle

__date__='2023.04.24'

folder='setup 2 two modes\\'
pump_power=297
wavelength = 1550.35e-9 #no balance
LO_power=1500
N=1000

trigger_channel=4
trace_points=10e6
sampling_rate=2e9

average_freq_window=1e6
average_time_window=100e-6
IsAveraging=True
win_time=3e-6

scope=scope.Scope('WINDOWS-E76DLEM')
scope.macro_setup(channels_displayed=(1,2,4),
                 trace_points=trace_points,
                 sampling_rate=sampling_rate,
                 trigger='TRIG',trigger_channel=trigger_channel)

pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(19)
LO.off()

#%%

#freq3 = itla.m_Hz(wl3)
pump.set_power(pump_power)
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
LO.on()

LO.mode('no dither')

pump.APCon()


#%%
file_name='wavelength={} pump={} triggered={}.pkl'.format(wavelength*1e9,pump_power,trigger_channel)

  #%%        
    

Ratio_arr=[]
Ratio_error_arr=[]

errors_rate=0
n=0
while n<N:
    try:
        #%%
        scope.acquire()
        trace_1=scope.get_data(1)
        trace_2=scope.get_data(2)
        
        offset_1=np.mean(trace_1.data)
        offset_2=np.mean(trace_2.data)
        
        scope.set_channel_offset(1, offset_1)
        scope.set_channel_offset(2, offset_2)
        
        spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,win_time=win_time,IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window)
        spec2=create_spectrogram_from_data(trace_2.data,trace_2.xinc,win_time=win_time,IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window)
            
        spec1.find_modes(prominance_factor=2)
        spec2.find_modes(prominance_factor=2)
        
        all_modes_list=spec1.modes.copy()
        spec1_freqs=spec1.get_modes_freqs()
        for m in spec2.modes:
            if m.freq not in spec1_freqs:
                all_modes_list.append(m)
        
        if len(all_modes_list)>1:
            mode1=all_modes_list[0]
            mode2=all_modes_list[1]
            Ratio1, Ratio_error1=get_ratio(spec1,spec2,mode1)
            Ratio2, Ratio_error2=get_ratio(spec1,spec2,mode2)
            Ratio=Ratio2/Ratio1
            if Ratio!=np.nan and Ratio_error1<0.3 and Ratio_error2<0.3 :
                n+=1
                Ratio_arr.append(Ratio)
                Ratio_error_arr.append((Ratio_error1*Ratio1+Ratio_error2*Ratio2)/(Ratio))
           
        print(n)
                  
                    
       
        if n%10==0:
            with open(folder+file_name,'wb') as f:
                pickle.dump([Ratio_arr,Ratio_error_arr],f)
                print('saved')
        if n%10==0:
            if Ratio>10:
                spec1.save_to_file('Two modes with different polarizations 1 {:.2f}.spec'.format(Ratio))
                spec2.save_to_file('Two modes with different polarizations 2 {:.2f}.spec'.format(Ratio))
                
                trace_4=scope.get_data(4)
                spec4=create_spectrogram_from_data(trace_4.data,trace_4.xinc,win_time=win_time,IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window)
                spec4.save_to_file('Two modes with different polarizations 4 {:.2f}.spec'.format(Ratio))
                
                
            if abs(Ratio-1)<0.1:
                spec1.save_to_file('Two modes with same polarizations 1 {:.2f}.spec'.format(Ratio))
                spec2.save_to_file('Two modes with same polarizations 2 {:.2f}.spec'.format(Ratio))
         
                trace_4=scope.get_data(4)
                spec4=create_spectrogram_from_data(trace_4.data,trace_4.xinc,win_time=win_time,IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window)
                spec4.save_to_file('Two modes with different polarizations 4 {:.2f}.spec'.format(Ratio))
#%%        
    except Exception as e:
        print('ERROR:'+str(e))
        LO.off()
        pump.APCoff()
                

LO.off()
pump.APCoff()


       
with open(folder+file_name,'wb') as f:
    pickle.dump([Ratio_arr,Ratio_error_arr],f)
    print('saved')

    

        

    