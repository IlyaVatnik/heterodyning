import numpy as np
import matplotlib.pyplot as plt
from heterodyning.Hardware import keopsys,ThorlabsPM100
import time
import pickle



pump_min=285
pump_max=310
pump_step=1

N_average=10

pump = keopsys.Keopsys('10.2.60.244')
PM=ThorlabsPM100.PowerMeter()

pump.set_power(pump_min)
pump.APCon()
time.sleep(2)
output_powers=[]



try:
    for p in np.arange(pump_min,pump_max,pump_step):
        print(p)
        pump.set_power(p)
        time.sleep(1)
        power=0
        for n in range(N_average):
            power+=PM.get_power()
        output_powers.append(power/N_average)

    pump.APCoff()
except Exception as e:
    print(e)
    pump.APCoff()

with open('powers.pkl', 'wb') as f:
    pickle.dump([np.arange(pump_min,pump_max,pump_step),output_powers],f)
    
    
    
