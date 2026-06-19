# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 14:56:31 2026

@author: Илья
"""

import numpy as np
import heterodyning
from heterodyning.heterodyning_with_interrogator import TraceAnalyzer2D
from heterodyning.Hardware import scope_rigol,keopsys
from AFR_interrogator.interrogator import Interrogator
import matplotlib.pyplot as plt
import pickle
import socket
from pathlib import Path
import os

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


N_repetition=20
pump_power_array=np.arange(297,298)
#%%
it.start_freq_stream()


#%%

plot_everything=True
success=False
pump.on()
for pump_power in pump_power_array:
    
    pump.set_power(pump_power)
    # Проверяем, что папки не существует
    if not os.path.isdir(f'{pump_power}'):
        os.makedirs(f"{pump_power}", exist_ok=True)
    i=0        
    for i in range(N_repetition):
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
        
        with open(f'{pump_power}\\example_trace {i}.pkl','wb') as f:
            pickle.dump(trace_1,f)

it.stop_freq_stream()
pump.off() 

#%%

    
#%%


