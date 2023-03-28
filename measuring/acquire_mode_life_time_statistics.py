import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from heterodyning.Hardware import scope,itla,keopsys
import matplotlib.pyplot as plt
import time
import pickle

__version__='3'
__date__='2023.03.28'

scope=scope.Scope('WINDOWS-E76DLEM')
#%%
trigger_channel=4
wavelength = 1550.35e-9 #no balance
LO_power=1400
pump_power=297


N_max=500

# trigger='AUTO'
trigger='TRIG'

scope.macro_setup(channels_displayed=(4,),
                 trace_points=80e6,
                 sampling_rate=2e9,
                 trigger=trigger,
                 trigger_channel=trigger_channel)

#%%
# trace=scope.acquire_and_return(1)
# plt.plot(trace.data)


#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(4)

#%%

#%%


folder='spectrogram_examples\\'
file_name='wavelength={} pump={} triggered={}'.format(wavelength*1e9,pump_power,trigger_channel)

#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
pump.set_power(pump_power)

#%%
LO.on()
pump.APCon()
LO.mode('whisper')
pump.set_power(pump_power)
#%%
'''
get statistics
'''

life_times=[]
acqusition_times=[]
n=0


win_time=1e-6
average_time_window=100e-6
average_freq_window=3e6

max_life_time=0
try:
    while n<N_max:
        print(n)
        time1=time.time()
        scope.acquire()
        time2=time.time()
        trace_1=scope.get_data(4)
        spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=True,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window)
        acqusition_times.append(time2-time1)
        print('acqisition time ', time2-time1)
        spec1.find_modes(prominance_factor=3,height=2e-4,rel_height=0.9)
    
        if len(spec1.modes)>0:
            for i,mode in enumerate(spec1.modes):
                life_times.append(mode.life_time)
                print(' life time, microseconds' ,mode.life_time)
                n+=1
                if mode.life_time>max_life_time:
                    max_life_time=mode.life_time
                    with open(folder+'p={} wl={} max.pkl'.format(int(pump_power),(wavelength*1e9)), 'wb') as f:
                        pickle.dump(spec1, f)       
                    
        if n%10==0:
            with open('p={} wl={}.pkl'.format(int(pump_power),(wavelength*1e9)), 'wb') as f:
                pickle.dump([acqusition_times, life_times], f)  
        
except:
    with open('p={} wl={}.pkl'.format(int(pump_power),(wavelength*1e9)), 'wb') as f:
        pickle.dump([acqusition_times, life_times], f)

#trace_stokes, trace_init = get_data(scp4)


#%%
LO.off()
pump.APCoff()

