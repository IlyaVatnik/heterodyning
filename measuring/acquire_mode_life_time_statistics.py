import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from heterodyning.Hardware import scope,itla,keopsys,scope_rigol,ThorlabsPM100
import matplotlib.pyplot as plt
import time
import pickle

__version__='5'
__date__='2023.09.05'

scope=scope_rigol.Scope('10.2.60.108')

control_power=True
#%%
scope.macro_setup(trace_points=1e6,
                  acq_time=5e-3,
                  trigger='SINGLe')

sampling_rate=scope.get_sampling_rate()


#%%
wavelength = 1550.30e-9 #no balance
LO_power=1400

    
win_time=1e-6
# IsAveraging=False
IsAveraging=True
average_freq_window=3e6
average_time_window=10e-6

real_power_coeff=35
losses_in_measurement_system=0.01
real_power_coeff=real_power_coeff/losses_in_measurement_system


pump_power=349


N_max=300


control_output_power=5e-5 # W
if control_power:
    PM=ThorlabsPM100.PowerMeter()
# trace=scope.acquire_and_return(1)
# plt.plot(trace.data)


#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(4)



#%%


folder='spectrogram examples\\'


#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
LO.set_FTFrequency(0)
pump.set_power(pump_power)

#%%
LO.on()
time.sleep(20)
LO.mode('whisper')
# LO.mode('no dither')

#%%
pump.APCon()


#%%

scope.acquire()
time.sleep(1)
trace_1=scope.get_data(1)
mean=np.mean(trace_1.data)
trigger_level=scope.get_trigger_high_level()
print('mean={},trigger={}'.format(mean,trigger_level))

file_preamb='p={} wl={} mean={:.3f} trigger={:.3f} sr={}'.format(int(pump_power),(wavelength*1e9),mean,trigger_level,sampling_rate/1e6)

'''
get statistics
'''
    
life_times=[]
powers=[]
acqusition_times=[]
freqs=[]
life_spans=[]
n=0


 
max_life_time=0
min_life_time=1000

try:
    while n<N_max:
        print(n)
        N_points=0
        while N_points==0:
            if control_power:
                p=PM.get_power()
                if p<control_output_power:
                    raise Exception('Too low output power={}'.format(p))
            time1=time.time()
            scope.acquire()
            time2=time.time()
            time.sleep(1)
            trace_1=scope.get_data(1)
            N_points=len(trace_1.data)
        # if len(trace_1.data)==0: continue
        spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,
                                           average_freq_window=average_freq_window,average_time_window=average_time_window,
                                           low_cut_off=10e6,
                                           real_power_coeff=real_power_coeff)
        acqusition_times.append(time2-time1)
        print('acqisition time ', time2-time1)
        spec1.find_modes(prominance_factor=2)
    
        if len(spec1.modes)>0:
            for i,mode in enumerate(spec1.modes):
                life_times.append(mode.life_time)
                powers.append(mode.max_power)
                freqs.append(mode.freq)
                life_spans.append(mode.life_spans)
                print(' mode freq {:.3f} MHz,life time {:.3f} mks, power {:.2e} mW'.format(mode.freq/1e6,mode.life_time*1e6,mode.max_power*1e3))
                n+=1
                if mode.life_time>max_life_time:
                    max_life_time=mode.life_time
                    with open(folder+file_preamb+' max.pkl', 'wb') as f:
                        pickle.dump(spec1, f)       
                if mode.life_time<min_life_time:
                    min_life_time=mode.life_time
                    with open(folder+file_preamb+' min.pkl', 'wb') as f:
                        pickle.dump(spec1, f)       
                    
        if n%10==0:
            with open(file_preamb+'.pkl', 'wb') as f:
                pickle.dump([acqusition_times, life_times,powers,freqs,life_spans], f)  
        
except Exception as e:
    print(e)
    with open(file_preamb +'.pkl', 'wb') as f:
        pickle.dump([acqusition_times, life_times,powers,freqs,life_spans], f)
    LO.off()
    pump.APCoff()

#trace_stokes, trace_init = get_data(scp4)
with open(file_preamb+'.pkl', 'wb') as f:
    pickle.dump([acqusition_times, life_times,powers,freqs,life_spans], f)  




LO.off()
pump.APCoff()
        
