# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 13:07:47 2022

@author: ilyav
"""

import numpy as np
import matplotlib.pyplot as plt

import time
import pickle
import os

__date__='2023.03.21'

folder='data\\'
# folder='data 100 max_hold sens Normal\\'


#%%


f_list=os.listdir(folder)

# plt.figure(3)
# figs, axes=plt.subplots(3,5)
# axes=axes.flatten()

plt.figure(1)
axis=plt.gca()
pump_array=[]
gen_power_array=[]

def dBm2W(x):
    return 10**(x/10)/1000


def W2dBm(x):
    return 10*np.log10(1000*x)

for i,f in enumerate(f_list):
    with open(folder+f,'rb') as file:
        [x,y,time_measured,N_repeat]=pickle.load(file)
    p=int(f.split('.')[0])/10
    x=x*1e9
    # axes[i].plot(x,y,label='{:.1f}'.format(p))
    # axes[i].set_title(p)
    plt.plot(x,y,label='{:.1f}'.format(p))
    pump_array+=[dBm2W(p)]
    gen_power_array+=[np.sum(10**(y/10))]
    # print(f,time_measured)
    
plt.xlabel('Wavelength, nm')
plt.ylabel('Spectral power density, dBm/nm')
axis.set_ylim(bottom=-75)
axis.set_xlim(((1549,1552)))

# plt.tight_layout()
plt.legend()
# plt.show()
plt.savefig('PICS\\Spectra {}.png'.format(folder.split('\\')[0]))

# figs.tight_layout()

plt.figure(20)
plt.plot(np.array(pump_array),np.array(gen_power_array))
plt.xlabel('Pump power, W')
plt.ylabel('Generation power, arb.u')
secax = plt.gca().secondary_xaxis('top', functions=(W2dBm,dBm2W))
secax.set_xlabel('Pump power, dBm')
plt.tight_layout()
plt.show()
plt.savefig('PICS\\Powers {}.png'.format(folder.split('\\')[0]))


