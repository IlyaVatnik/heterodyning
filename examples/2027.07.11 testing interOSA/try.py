# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 13:36:16 2026

@author: Thorlabs Redstone
"""

import numpy as np
import matplotlib.pyplot as plt

from heterodyning.spectrograms_with_scanning_interrogator import TraceAnalyzer2D
import pickle
import time

#%%
with open('test.pkl','rb') as f:
    trace=pickle.load(f)
#%%

plt.figure()
times=np.arange(len(trace[0]))*trace[1]+trace[2]
plt.plot(times,trace[0])
a=TraceAnalyzer2D(start_wavelength=1530,stop_wavelength=1534)
#%%
a.process(trace[0],trace[1],trace[2],start_time=14.08e-6)
a.plot_instant_spectrum(0)

