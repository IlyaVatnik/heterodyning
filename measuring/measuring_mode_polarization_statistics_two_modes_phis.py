'''
Measuring modes in two channels and calculate those ratio
'''

import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,Mode,get_mode_ratio
from heterodyning.Hardware import scope,itla,keopsys
import matplotlib.pyplot as plt
import pickle

__date__='2023.05.23'

folder='setup 1 two modes try 2\\'
folder_for_raw_data=folder+'Spectrograms and raw data\\'
pump_power=298
wavelength = 1550.36e-9 
LO_power=1500
N=2000

SensRatio=1.29 # ratio of second channel to first


trigger_channel=4
trace_points=0.1e6
sampling_rate=2e9

win_time=3e-6
# IsAveraging=False
IsAveraging=True
average_freq_window=3e6
average_time_window=20e-6

scope=scope.Scope('WINDOWS-E76DLEM')
scope.macro_setup(channels_displayed=(1,2,4),
                 trace_points=trace_points,
                 sampling_rate=sampling_rate,
                 trigger='TRIG',trigger_channel=trigger_channel)

pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(3)
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
    

phi1_arr=[]
phi2_arr=[]
phi_error_arr=[]

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
            
        spec1.spec*=SensRatio    
    
        spec1.find_modes(prominance_factor=5,height=5e-15)
        spec2.find_modes(prominance_factor=5,height=5e-15)
        
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
            

        
        if len(all_modes_list)>1:
            all_modes_list.sort(key=lambda x:-x.max_intensity)
            mode1=all_modes_list[0]
            mode2=all_modes_list[1]
            Ratio1, Ratio_error1,_,_=get_mode_ratio(spec1,spec2,mode1)
            phi1=np.arctan(np.sqrt(Ratio1))
            Ratio2, Ratio_error2,_,_=get_mode_ratio(spec1,spec2,mode2)
            Ratio=Ratio1/Ratio2
            phi2=np.arctan(np.sqrt(Ratio2))
            phi_diffference=phi1-phi2
            if phi_diffference!=np.nan and Ratio_error1<0.3 and Ratio_error2<0.3 :
                n+=1
                phi1_arr.append(phi1)
                phi2_arr.append(phi2)
                phi_error_arr.append((Ratio_error1*Ratio1+Ratio_error2*Ratio2)/(Ratio))
           
        print(n)
                  
                    
       
        if n%10==0:
            with open(folder+file_name,'wb') as f:
                pickle.dump([phi1_arr,phi2_arr,phi_error_arr],f)
                print('saved')
        if n%10==0:
            if Ratio>10:
                
                np.savetxt(folder_for_raw_data+'Two modes with different polarizations 1 {:.2f}.txt'.format(Ratio), trace_1.data)
                np.savetxt(folder_for_raw_data+'Two modes with different polarizations 2 {:.2f}.txt'.format(Ratio), trace_2.data)
                spec1.save_to_file(folder_for_raw_data+'Two modes with different polarizations 1 {:.2f}.spec'.format(Ratio))
                spec2.save_to_file(folder_for_raw_data+'Two modes with different polarizations 2 {:.2f}.spec'.format(Ratio))
                
                trace_4=scope.get_data(4)
                spec4=create_spectrogram_from_data(trace_4.data,trace_4.xinc,win_time=win_time,IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window)
                spec4.save_to_file(folder_for_raw_data+'Two modes with different polarizations 4 {:.2f}.spec'.format(Ratio))
                
                
            if abs(Ratio-1)<0.1:
                np.savetxt(folder_for_raw_data+'Two modes with same polarizations 1 {:.2f}.txt'.format(Ratio), trace_1.data)
                np.savetxt(folder_for_raw_data+'Two modes with same polarizations 2 {:.2f}.txt'.format(Ratio), trace_2.data)
                spec1.save_to_file(folder_for_raw_data+'Two modes with same polarizations 1 {:.2f}.spec'.format(Ratio))
                spec2.save_to_file(folder_for_raw_data+'Two modes with same polarizations 2 {:.2f}.spec'.format(Ratio))
         
                trace_4=scope.get_data(4)
                spec4=create_spectrogram_from_data(trace_4.data,trace_4.xinc,win_time=win_time,IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window)
                spec4.save_to_file(folder_for_raw_data+'Two modes with different polarizations 4 {:.2f}.spec'.format(Ratio))
#%%        
    except Exception as e:
        print('ERROR:'+str(e))
        LO.off()
        pump.APCoff()
                

LO.off()
pump.APCoff()

del LO
del pump
del scope
       
with open(folder+file_name,'wb') as f:
    pickle.dump([phi1_arr,phi2_arr,phi_error_arr],f)
    print('saved')

    

        

    