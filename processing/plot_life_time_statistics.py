import numpy as np
import matplotlib.pyplot as plt
import pickle
from matplotlib.ticker import EngFormatter
from pathlib import Path
formatter1 = EngFormatter()



def plot_life_time_statistics(file,label_size=10,data_in_mks=False):
    f=Path(file)
    pic_folder=(f.parent.parent/'PICS\\')
    
    with open(file,'rb') as open_file:
        [acqusition_times, life_times,powers,freqs,life_spans]=pickle.load(open_file)
    if data_in_mks:
        life_times=np.array(life_times)*1e-6
    
    freqs=np.array(freqs)
        
        
    plt.figure()
    plt.hist(acqusition_times,bins=30)
    plt.title(f.stem)
    plt.xlabel('Acqusition time, s')
    plt.ylabel('Number of events')
    plt.gca().xaxis.set_major_formatter(formatter1)
    plt.gca().yaxis.set_major_formatter(formatter1)
    plt.savefig(pic_folder/(f.stem+' Acqusition times.png'))
    
    plt.figure()
    plt.hist(life_times,bins=40)
    plt.title(f.stem)
    plt.xlabel('Life time, s')
    plt.ylabel('Number of events')
    plt.gca().xaxis.set_major_formatter(formatter1)
    plt.gca().yaxis.set_major_formatter(formatter1)
    plt.savefig(pic_folder/(f.stem+' Life times.png'))
    

    
    plt.figure()
    plt.hist(powers,bins=50)
    plt.title(f.stem)
    plt.xlabel('Power, W')
    plt.ylabel('Number of events')
    plt.gca().xaxis.set_major_formatter(formatter1)
    plt.gca().yaxis.set_major_formatter(formatter1)
    plt.savefig(pic_folder/(f.stem+' Powers.png'))
    
    
    plt.figure()
    plt.plot(powers,life_times,'o')
    plt.gca().set_xscale('log')
    plt.gca().set_yscale('log')
    plt.title(f.stem)
    plt.xlabel('Power, W')
    plt.ylabel('life times, s')
    plt.gca().xaxis.set_major_formatter(formatter1)
    plt.gca().yaxis.set_major_formatter(formatter1)
    plt.savefig(pic_folder/(f.stem+' LT vs Powers.png'))
    
    plt.figure()
    plt.plot(freqs/1e6,life_times,'o')
    plt.gca().set_xscale('log')
    plt.gca().set_yscale('log')
    plt.title(f.stem)
    plt.xlabel('Frequency, MHz')
    plt.ylabel('life times, s')
    plt.gca().xaxis.set_major_formatter(formatter1)
    plt.gca().yaxis.set_major_formatter(formatter1)
    plt.savefig(pic_folder/(f.stem+' LT vs Freqs.png'))
    
    
    plt.figure()
    plt.plot(powers,freqs/1e6,'o')
    plt.gca().set_xscale('log')
    plt.gca().set_yscale('log')
    plt.title(f.stem)
    plt.xlabel('Power, W')
    plt.ylabel('Frequency, MHz')
    plt.gca().xaxis.set_major_formatter(formatter1)
    plt.gca().yaxis.set_major_formatter(formatter1)
    plt.savefig(pic_folder/(f.stem+' Freqs vs Powers.png'))
    
    
    



if __name__=='__main__':
    # file=r"p=349 wl=1550.3 mean=0.375 trigger=0.372 sr=125.0.pkl"
    file=r'stacked p=349 wl=1550.3 mean=0.375 trigger=0.387 sr=125.0.pkl'
    plot_life_time_statistics(file)

