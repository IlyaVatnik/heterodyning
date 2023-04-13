import pickle
import numpy as np
from heterodyning.spectrograms import create_spectrogram_from_data
import matplotlib.pyplot as plt

with open('example_trace.pkl','rb') as f:
    trace=pickle.load(f)


spec=create_spectrogram_from_data(trace.data, trace.xinc,win_time=1e-6,
                                                            IsAveraging=True,
                                                            average_freq_window=5e6,
                                                            average_time_window=100e-6)
spec.plot_spectrogram()
spec.find_modes(indicate_modes_on_spectrogram=True,
                prominance_factor=0.9,threshold=2e-9,
                rel_height=1,plot_shrinked_spectrum=True)
spec.plot_all_modes()
spec.print_all_modes()
