import numpy as np
import matplotlib.pyplot as plt
from heterodyning.Hardware.APEX_OSA import APEX_OSA_with_additional_features
from heterodyning.Hardware import keopsys,yokogawa,ThorlabsPM100

import time
import pickle


__date__='2023.04.07'

folder='data\\'
type_of_meas='single'
# type_of_meas='hold'


# folder='data 100 max_hold sens Normal\\'
# type_of_meas='hold'

P_thresh=319
minimum_output_power=0.002 #  W

pump_min=310
pump_max=323
pump_step=1



N_averaged=30
N_repeat=1

osa = APEX_OSA_with_additional_features('10.2.60.25')
osa.SetScaleXUnit(ScaleXUnit=1)
osa.change_range(1550.0,1550.6)
osa.SetWavelengthResolution('High')

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
            [x, y]=osa.acquire_spectrum()
            x=x/1e9
        
        with open(folder+str(p)+'.pkl', 'wb') as f:
            pickle.dump([x,y,time_measured,N_repeat,PM.get_power()],f)
        output_powers.append(PM.get_power())
    pump.APCoff()
except Exception as e:
    pump.APCoff()
    print(e)
    
with  open('Powers measured.pkl', 'wb') as f:
            pickle.dump([np.arange(pump_min,pump_max,pump_step),output_powers],f)

del osa
del pump
