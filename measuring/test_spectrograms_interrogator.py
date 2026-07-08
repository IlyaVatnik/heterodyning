import numpy as np
import heterodyning
from heterodyning.spectrograms_with_scanning_interrogator import TraceAnalyzer2D
from heterodyning.Hardware import scope_rigol,keopsys
from AFR_interrogator.interrogator import Interrogator
import matplotlib.pyplot as plt
import pickle
import socket

#%%



SCOPE_IP = '10.2.60.212'           # IP Осциллографа Tektronix
INTERROGATOR_IP = '10.2.60.38'     # IP Интеррогатора

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Пытаемся "соединиться" с внутренней сетью, чтобы узнать свой рабочий IP
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

PC_IP = get_local_ip()



scope_scale = 0.1
scope_offset = -0.00
trigger_channel=1
scope_acq_time_set = 500e-3
sampling_rate=50e6
scope_trace_points_set = scope_acq_time_set*sampling_rate

scope=scope_rigol.Scope(SCOPE_IP)
memory_depth, sampling_rate=scope.macro_setup(channels_displayed=(1,),
                                              acq_time=scope_acq_time_set,trace_points=scope_trace_points_set,
                                              channels_impedances={1:'FIFTy'},
                                              trigger='SINGLE')

scope.set_channel_scale(1,scope_scale)
scope.set_channel_offset(1, scope_offset)
# scope.set_trigger_high_level()
# scope.set_channel_offset(1, -2.26)
scope.wait()

#%%
pump = keopsys.Keopsys('10.2.60.244')
it = Interrogator(INTERROGATOR_IP, PC_IP)

# osa = yokogawa.Yokogawa(timeout=1e7)
# osa.acquire()


#%%


#%%
pump_power=300
pump.set_power(pump_power)
folder='spectrogram_examples\\'


#%%
it.start_freq_stream()

pump.on()
#%%

plot_everything=True
success=False

scope.set_trigger_mode('SINGLE')
scope.trigger='SINGLe'
    # print(1)
    # scope.wait()
    # scope.force_trigger()
scope.acquire()
while True:
    trace_1=scope.get_data(1)
    if len(trace_1[0])>1:
        break

#%%
spec1=TraceAnalyzer2D()
spec1.process(trace_1[0], trace_1[1], trace_1[2])

                                  
if plot_everything: 
    spec1.plot_spectrogram(scale='lin')



mode_index=0
spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,
                 prominance_factor=1,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=plot_everything)
# spec1.find_modes(indicate_modes_on_spectrogram=plot_everything,prominance_factor=10,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=True)





spec1.print_all_modes()
spec1.plot_mode_dynamics(0)

#%%
it.stop_freq_stream()
pump.off() 

#%%
i=1
with open('example_trace {}.pkl'.format(i),'wb') as f:
    pickle.dump(trace_1,f)
    
#%%


