import pickle
import numpy as np
import heterodyning
import matplotlib.pyplot as plt

with open('example_trace.pkl','rb') as f:
    trace=pickle.load(f)


spec=heterodyning.spectrograms.create_spectrogram_from_data(trace.data, trace.xinc,win_time=1e-6,
                                                            IsAveraging=True,
                                                            average_freq_window=3e6,
                                                            average_time_window=100e-6)
spec.plot_spectrogram()
spec.find_modes(indicate_modes_on_spectrogram=True,prominance_factor=3,height=2e-4,rel_height=0.9)
spec.plot_all_modes()
spec.print_all_modes()
