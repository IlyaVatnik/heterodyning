from heterodyning.processing.process_spectra_yokogawa import process_spectra_from_folder
import matplotlib.pyplot as plt
import numpy as np
folders=['trans 51%',
         'trans 58%',
         'trans 73%',
         'trans 80%',
         'trans 100%']


def dBm2W(x):
    return 10**(x/10)/1000
    
    
def W2dBm(x):
    return 10*np.log10(1000*x)
    
plt.figure(100)
ax1=plt.gca()
plt.xlabel('Pump power, W')
plt.ylabel('Generation power, arb.u')
ax2 = ax1.secondary_xaxis('top', functions=(W2dBm,dBm2W))
ax2.set_xlabel('Pump power, dBm')

prop_cycle = plt.rcParams['axes.prop_cycle']
colors = prop_cycle.by_key()['color']
i=0
for folder in folders:
    print(folders)
    
    pump_array,gen_power_array,Pumps_with_modes=process_spectra_from_folder(folder+'\\data\\', plot_graphs=False)
    ax1.plot(np.array(pump_array),np.array(gen_power_array),color=colors[i])
    for pump in Pumps_with_modes:
       ax1.axvspan(dBm2W(W2dBm(pump)-0.049), dBm2W(W2dBm(pump)+0.049), alpha=0.1, color=colors[i])
    i+=1
# plt.tight_layout()
# plt.show()
    