import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from heterodyning.Hardware import scope,itla,keopsys,scope_rigol
import matplotlib.pyplot as plt
import time
import pickle

__version__='4'
__date__='2023.04.13'

scope=scope_rigol.Scope('10.2.60.239')
scope.macro_setup(trace_points=5e6,
                  acq_time=5e-3,
                  trigger='SINGLe')

#%%
wavelength = 1551.5e-9 #no balance
LO_power=1300
pump_power=349


N_max=300


#%%
# trace=scope.acquire_and_return(1)
# plt.plot(trace.data)


#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(4)

#%%

#%%


folder='spectrogram examples\\'
file_name='wavelength={} pump={}'.format(wavelength*1e9,pump_power)

#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
pump.set_power(pump_power)

#%%
LO.on()
pump.APCon()
LO.mode('whisper')
#%%
'''
get statistics
'''
def acquire_statistics():
    
    life_times=[]
    acqusition_times=[]
    n=0
    
    
    win_time=1e-6
    IsAveraging=True
    average_freq_window=3e6
    average_time_window=30e-6
     
    max_life_time=0
    min_life_time=1000
    try:
        while n<N_max:
            print(n)
            time1=time.time()
            scope.acquire()
            time2=time.time()
            trace_1=scope.get_data(1)
            if len(trace_1.data)==0: continue
            spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                               low_cut_off=0)
            acqusition_times.append(time2-time1)
            print('acqisition time ', time2-time1)
            spec1.find_modes(prominance_factor=3)
        
            if len(spec1.modes)>0:
                for i,mode in enumerate(spec1.modes):
                    life_times.append(mode.life_time)
                    print(' life time, microseconds' ,mode.life_time*1e6)
                    n+=1
                    if mode.life_time>max_life_time:
                        max_life_time=mode.life_time
                        with open(folder+'p={} wl={} max.pkl'.format(int(pump_power),(wavelength*1e9)), 'wb') as f:
                            pickle.dump(spec1, f)       
                    if mode.life_time<min_life_time:
                        min_life_time=mode.life_time
                        with open(folder+'p={} wl={} min.pkl'.format(int(pump_power),(wavelength*1e9)), 'wb') as f:
                            pickle.dump(spec1, f)       
                        
            if n%10==0:
                with open('p={} wl={}.pkl'.format(int(pump_power),(wavelength*1e9)), 'wb') as f:
                    pickle.dump([acqusition_times, life_times], f)  
            
    except Exception as e:
        print(e)
        with open('p={} wl={}.pkl'.format(int(pump_power),(wavelength*1e9)), 'wb') as f:
            pickle.dump([acqusition_times, life_times], f)
    
    #trace_stokes, trace_init = get_data(scp4)
    with open('p={} wl={}.pkl'.format(int(pump_power),(wavelength*1e9)), 'wb') as f:
        pickle.dump([acqusition_times, life_times], f)  


acquire_statistics()

LO.off()
pump.APCoff()
        
