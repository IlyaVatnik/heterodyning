# -*- coding: utf-8 -*-
"""
Created on Fri May 26 15:35:59 2023

@author: Ilya
"""
import pickle
import heterodyning
import numpy as np
from heterodyning.spectrograms import create_spectrogram_from_data,get_mode_ratio

T=1

f_s=1e5

f_signal=8e4

times=np.arange(0,T,1/f_s)

data=np.sin(2*np.pi*times*f_signal)


win_time=1e-3

spec=create_spectrogram_from_data(data, 1/f_s,win_time=win_time,overlap_time=0,cut_off=False)
spec.plot_spectrogram()