import numpy as np
import matplotlib.pyplot as plt
import pickle
import os
from heterodyning import spectrograms
from matplotlib.ticker import EngFormatter
formatter1 = EngFormatter()



folder_statistics='Statistics\\'
file_statistics='p=325 wl=1550.35 1.pkl'
# folder_examples='spectrogram_examples\\1\\'
pic_folder='PICS\\'


with open(folder_statistics+file_statistics,'rb') as f:
    [acqusition_times, life_times]=pickle.load(f)

plt.figure()
plt.hist(life_times,bins=30)
plt.title(file_statistics)
plt.xlabel('Life time, s')
plt.ylabel('Number of events')
plt.gca().xaxis.set_major_formatter(formatter1)
plt.gca().yaxis.set_major_formatter(formatter1)
plt.savefig(pic_folder+file_statistics+' Life times.png')

plt.figure()
plt.hist(acqusition_times,bins=30)
plt.title(file_statistics)
plt.xlabel('Acqusition time, s')
plt.ylabel('Number of events')
plt.gca().xaxis.set_major_formatter(formatter1)
plt.gca().yaxis.set_major_formatter(formatter1)
plt.savefig(pic_folder+file_statistics+' aquisition times.png')




     
# f_list=os.listdir(folder_examples)
# file1=f_list[0]
# mode_index=0
# spec1=spectrograms.load_from_file(folder_examples+file1)
# fig,axes=spec1.plot_spectrogram(title=file1)
# spec1.find_modes(indicate_modes_on_spectrogram=False,prominance_factor=3)
# # axes.axhline(spec1.modes[mode_index].freq,color='yellow')
# plt.savefig(pic_folder+file1+' Ch 1.png')
