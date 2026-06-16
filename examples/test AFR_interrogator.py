# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 18:41:56 2026

@author: Илья
"""

from AFR_interrogator.interrogator import Interrogator

it = Interrogator('10.2.60.38','10.2.60.235')
#%%
it.start_freq_stream()
it.stop_freq_stream()
