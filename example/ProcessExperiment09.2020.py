import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter
import scipy.fft as fft
import scipy
import bottleneck as bn

from heterodyning.processing import Spectrogram


folder='G:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\heterodyning\example\\'
file_name='pulse 10mks edge 3 ns 4 V.bin'
formatter1 = EngFormatter(places=2)  # U+2009


win_time=5e-6
win_time_step=1e-6

overlap_time=win_time-win_time_step

IsAveraging=True
average_time_window=4e-6    
average_freq_window=4e6



time0=time.time()
spec=Spectrogram(folder+file_name,win_time,overlap_time,IsAveraging,average_time_window,average_freq_window)
spec.plot_processed_spectrogram()

spec.find_modes(indicate_modes_on_spectrogram=True)



for p,_ in enumerate(spec.modes):
    fig,ax=spec.plot_mode_dynamics(p)
#     life_time,l,r=spec.get_mode_lifetime(p)
#     ax.set_xlim((l-2e-3,r+2e-3))
#     spec.plot_mode_lowfreq_spectrum(p)


time1=time.time()
print(time1-time0)