import numpy as np
import matplotlib.pyplot as plt
from heterodyning.Hardware import keopsys,yokogawa
import time
import pickle

folder='data\\'
type_of_meas='single'


# folder='data 200 max_hold try2\\'
# type_of_meas='hold'


pump_min=296
pump_max=297
pump_step=1




N_repeat=1

osa = yokogawa.Yokogawa(timeout=1e7)
osa.set_average_count(1)


if type_of_meas=='hold':
    time1=time.time()
    osa.set_measurement_mode('SINGLE')
    osa.acquire()
    time2=time.time()
    time_measured=time2-time1
    osa.set_trace_mode('A','MAX')
    osa.set_measurement_mode('REPEAT')
else:
    time_measured=0
        

pump = keopsys.Keopsys('10.2.60.244')


pump.set_power(pump_min)
pump.APCon()
time.sleep(2)

try:
    for p in np.arange(pump_min,pump_max,pump_step):
        print(p)
        pump.set_power(p)
        time.sleep(1)
        if type_of_meas=='hold':
            time1=time.time()
            osa.clear_trace()
            osa.start_measurements()
            while time.time()-time1<time_measured*N_repeat:
                continue
            osa.abort()
        elif type_of_meas=='single':
            osa.acquire()
            
        x, y = osa.query_trace()
        with open(folder+str(p)+'.pkl', 'wb') as f:
            pickle.dump([x,y,time_measured,N_repeat],f)
    pump.APCoff()
except Exception as e:
    print(e)
    pump.APCoff()
    osa.set_average_count(1)
    osa.abort()
    osa.set_trace_mode('A','WRITE')
    osa.set_measurement_mode('SINGLE')
    
    

osa.set_average_count(1)
osa.set_trace_mode('A','WRITE')   
osa.set_measurement_mode('SINGLE') 
