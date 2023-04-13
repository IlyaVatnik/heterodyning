import numpy as np
import matplotlib.pyplot as plt
from heterodyning.Hardware import keopsys,yokogawa,ThorlabsPM100
import time
import pickle


__date__='2023.04.07'

folder='data\\'
type_of_meas='single'
# type_of_meas='hold'


# folder='data 100 max_hold sens Normal\\'
# type_of_meas='hold'

P_thresh=322
minimum_output_power=-0.001 #  W

pump_min=290
pump_max=305
pump_step=1



N_averaged=30
N_repeat=1

osa = yokogawa.Yokogawa(timeout=1e7)
osa.set_average_count(N_averaged)
osa.set_sensitivity('Normal')
osa.set_span(1546,1556)

PM=ThorlabsPM100.PowerMeter()

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
output_powers=[]

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
                if p>P_thresh and PM.get_power()<minimum_output_power:
                    raise Exception('something went wrong! No output power')
                continue
            osa.abort()
        elif type_of_meas=='single':
            if p>P_thresh and PM.get_power()<minimum_output_power:
                raise Exception('something went wrong! No output power')
            osa.acquire()
            
        x, y = osa.query_trace()
        with open(folder+str(p)+'.pkl', 'wb') as f:
            pickle.dump([x,y,time_measured,N_repeat],f)
        output_powers.append(PM.get_power())
    pump.APCoff()
except Exception as e:
    pump.APCoff()
    print(e)
    osa.set_average_count(1)
    osa.abort()
    osa.set_trace_mode('A','WRITE')
    osa.set_measurement_mode('SINGLE')
    
with  open('Powers measured.pkl', 'wb') as f:
            pickle.dump([np.arange(pump_min,pump_max,pump_step),output_powers],f)

osa.set_average_count(1)
osa.set_trace_mode('A','WRITE')   
osa.set_measurement_mode('SINGLE') 
del osa
del pump
