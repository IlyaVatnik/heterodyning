import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from heterodyning.Hardware import scope,itla,keopsys,scope_rigol,ThorlabsPM100

 
import matplotlib.pyplot as plt
import time
import pickle

__version__='5'
__date__='2023.04.13'

scope=scope_rigol.Scope('10.2.60.122')
#%%

LO_real_power=2.8 # in mW


[N_points,sampling_rate]=scope.macro_setup(trace_points=1e6,
                  acq_time=5e-3,
                  trigger='SINGLe')

win_time=2e-6
# IsAveraging=False
IsAveraging=True
average_freq_window=2e6
average_time_window=10e-6
    




calibration_file=r"F:\Ilya\heterodyning\Hardware\calibrations\calibration LO 0.72 mW balanced.txt"
# a=np.load(calibration_file)
calibration_curve=heterodyning.spectrograms.create_calibration_curve(calibration_file,LO_real_power,N_points,1/sampling_rate,win_time)
# cal_curve=cal_curve.reshape(-1,1)
losses_in_measurement_line=0.01*0.41
calibration_curve/=losses_in_measurement_line

#%%
wavelength = 1550.3e-9 #no balance
LO_power=1600

    






pump_power=300


N_max=300
minimum_output_power=1e-5


# trace=scope.acquire_and_return(1)
# plt.plot(trace.data)


#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(4)
PM=ThorlabsPM100.PowerMeter()


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
LO.mode('whisper')
pump.APCon()

#%%

test_trace=scope.acquire_and_return(1)
mean=np.mean(test_trace.data)
trigger_level=scope.get_trigger_high_level()
spec1=create_spectrogram_from_data(test_trace.data,test_trace.xinc,IsAveraging=IsAveraging,win_time=win_time,
                                   average_freq_window=average_freq_window,average_time_window=average_time_window,
                                   low_cut_off=0,
                                   calibration_curve=calibration_curve)
times=spec1.times
print('mean={},trigger={}'.format(mean,trigger_level))

file_preamb='p={} wl={} mean={:.3f} trigger={:.3f} sr={}'.format(int(pump_power),(wavelength*1e9),mean,trigger_level,sampling_r иate/1e6)

'''
get statistics
'''
def acquire_statistics():
    
    life_times=[]
    powers=[]
    acqusition_times=[]
    freqs=[]
    mode_dynamics=[]
    n=0
    

     
    max_life_time=0
    min_life_time=1000
    try:
        while n<N_max:
            print(n)
            if PM.get_power()<minimum_output_power:
                raise Exception('something went wrong! No output power')
            time1=time.time()
            scope.acquire()
            time2=time.time()
            trace_1=scope.get_data(1)
            if len(trace_1.data)==0: continue
            spec1=create_spectrogram_from_data(trace_1.data,trace_1.xinc,IsAveraging=IsAveraging,win_time=win_time,
                                               average_freq_window=average_freq_window,average_time_window=average_time_window,
                                               low_cut_off=0,
                                               calibration_curve=calibration_curve)
            acqusition_times.append(time2-time1)
            print('acqisition time ', time2-time1)
            spec1.find_modes(prominance_factor=3)
        
            if len(spec1.modes)>0:
                for i,mode in enumerate(spec1.modes):
                    life_times.append(mode.life_time)
                    powers.append(mode.max_power)
                    freqs.append(mode.freq)
                    mode_dynamics.append(spec1.get_mode_dynamics(i)[1])
                    print(' mode freq {:.3f} MHz,life time {:.3f} mks, power {:.3e} W'.format(mode.freq/1e6,mode.life_time*1e6,mode.max_power))
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
                    pickle.dump([acqusition_times, life_times,powers,freqs,mode_dynamics,times], f)  
            
    except Exception as e:
        print(e)
        with open(file_preamb +'.pkl', 'wb') as f:
            pickle.dump([acqusition_times, life_times,powers,freqs,mode_dynamics,times], f)
        pump.APCoff()
    
    #trace_stokes, trace_init = get_data(scp4)
    with open(file_preamb+'.pkl', 'wb') as f:
        pickle.dump([acqusition_times, life_times,powers,freqs,mode_dynamics,times], f)  



acquire_statistics()
pump.APCoff()
#%%
LO.off()

        
