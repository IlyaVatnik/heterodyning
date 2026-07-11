# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 13:36:16 2026

@author: Thorlabs Redstone
"""

import numpy as np
import matplotlib.pyplot as plt
from heterodyning.interrogator_osa import Interrogator_OSA
from heterodyning.Hardware import scope_rigol
from heterodyning.spectrograms_with_scanning_interrogator import TraceAnalyzer2D
import pickle
import time

#%%
timeout=50

IP='10.2.15.238'


scope=scope_rigol.Scope(IP)
osa=Interrogator_OSA(scope,1,2,1532,1534,14.08e-6,
                     sampling_rate=1000e6,
                     scope_acqusition_time=100e-6)
osa.configure_scope()

#%%
osa.acquire()
waves,spectrum,_=osa.query_trace()
plt.figure()
plt.plot(waves,spectrum)
#%%
centers=[]
powers=[]
for i in range(1000):
    osa.acquire()
    waves,spectrum,_=osa.query_trace()
    print(waves[np.argmax(spectrum)],np.max(spectrum))
    centers.append(waves[np.argmax(spectrum)])
    powers.append(np.max(spectrum))

fig,axes=plt.subplots(2,1)
axes[0].plot(centers)
axes[0].set_ylabel('Wavelength, nm')
axes[1].plot(powers)
axes[1].set_ylabel('Power, dBm')
plt.title(f'{np.std(centers)} nm, {np.std(powers)} dB')

#%%
with open('response_heterodyning.pkl', 'wb') as f:
    pickle.dump([waves,spectrum],f)