import numpy as np
import matplotlib.pyplot as plt
from heterodyning.Hardware.APEX_OSA import APEX_OSA_with_additional_features

#%%
OSA = APEX_OSA_with_additional_features('10.2.60.25')
OSA.SetScaleXUnit(ScaleXUnit=1)
OSA.change_range(1549.98,1550.02)
OSA.SetWavelengthResolution('High')
# OSA.SetScaleXUnit(ScaleXUnit=0) #highres only

#%%
spectrum=OSA.acquire_spectrum()
# plt.plot(spectrum)
plt.figure()
plt.plot(spectrum[0],spectrum[1])
