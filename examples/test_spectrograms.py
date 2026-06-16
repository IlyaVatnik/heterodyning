import numpy as np
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data,get_mode_ratio
from heterodyning.Hardware import scope_rigol,itla,keopsys,yokogawa
import matplotlib.pyplot as plt
import pickle

#%%


#%%


scope_IP='10.2.60.119'
scope_scale = 0.14
scope_offset = -0.0
scope_acq_time_set = 2e-3
scope_trace_points_set = 1e6

scope=scope_rigol.Scope(scope_IP)

memory_depth, sampling_rate=scope.macro_setup(channels_displayed=(1,),
                                              acq_time=scope_acq_time_set,trace_points=scope_trace_points_set,
                                              channels_impedances={1:'FIFTy'},
                                              trigger='SINGLE')

scope.set_channel_scale(1,scope_scale)
scope.set_channel_offset(1, scope_offset)



#%%
pump = keopsys.Keopsys('10.2.60.244')
LO = itla.PPCL550(5)

# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%
wavelength = 1550.36e-9 #no balance
LO_power=1500


pump_power=306
pump.set_power(pump_power)
folder='spectrogram_examples\\'
file_name='wavelength={} pump={} '.format(wavelength*1e9,pump_power)

#%%
LO.off()
LO.set_wavelength(wavelength)
LO.set_power(LO_power)
LO.on()
#%%
LO.mode('no dither')
#%%
pump.on()
N=0
#%%
for N in np.arange(1,500):
    print(N)
    
    while True:
        scope.trigger='SINGLe'
        scope.set_trigger_mode('SINGLE')
            # print(1)
        scope.wait()
        scope.acquire()
        trace_1=scope.get_data(1)
        if len(trace_1[0])>1:
            break
    
    win_time=10e-6
    # IsAveraging=False
    IsAveraging=True
    average_freq_window=2e6
    average_time_window=10e-6
    
    
    real_power_ch1=160*2*1e-3
    
    
    spec1=create_spectrogram_from_data(trace_1[0],trace_1[1],IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                       real_power_coeff=real_power_ch1,high_cut_off=2e9)
    
                                      
    fig,ax=spec1.plot_spectrogram(scale='lin')
    
    
    
    mode_index=0
    # spec1.find_modes(indicate_modes_on_spectrogram=False,prominance_factor=2,height=1e-15,min_freq_spacing=2e6,
                     # rel_height=1)
    # spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=10,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=True)
    # spec1.print_all_modes()
    # spec1.plot_mode_dynamics(0)




    file_name=f'example_trace {N}'
    with open(file_name+'.pkl','wb') as f:
        pickle.dump(trace_1,f)
    fig.savefig(file_name+'.png')
    plt.close(fig)
    

LO.off()
pump.off()

#%%
LO.off()
pump.off()

spec1.save_to_file('example ch1 real power.spec',as_object=False)

