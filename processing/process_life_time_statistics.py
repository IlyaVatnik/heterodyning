import numpy as np
import matplotlib.pyplot as plt
import pickle
from matplotlib.ticker import EngFormatter
from pathlib import Path
formatter1 = EngFormatter()



def process_life_times_from_file(file,label_size=10,data_in_mks=False):
    f=Path(file)
    pic_folder=(f.parent.parent/'PICS\\')
    
    with open(file,'rb') as open_file:
        [acqusition_times, life_times]=pickle.load(open_file)
    if data_in_mks:
        life_times=np.array(life_times)*1e-6
    plt.figure()
    plt.hist(life_times,bins=30)
    plt.title(f.stem)
    plt.xlabel('Life time, s')
    plt.ylabel('Number of events')
    plt.gca().xaxis.set_major_formatter(formatter1)
    plt.gca().yaxis.set_major_formatter(formatter1)
    plt.savefig(pic_folder/(f.stem+' Life times.png'))
    
    plt.figure()
    plt.hist(acqusition_times,bins=30)
    plt.title(f.stem)
    plt.xlabel('Acqusition time, s')
    plt.ylabel('Number of events')
    plt.gca().xaxis.set_major_formatter(formatter1)
    plt.gca().yaxis.set_major_formatter(formatter1)
    plt.savefig(pic_folder/(f.stem+' Acqusition times.png'))


if __name__=='__main__':
    file=r"F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\2023-2022 different fibers and different data\Metrocore 25 km\2022.11.17 Metrocore mode life_time staticstics\data\p=293 wl=1551 2.pkl"
    process_life_times_from_file(file)

