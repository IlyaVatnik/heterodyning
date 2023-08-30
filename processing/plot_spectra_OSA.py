# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 13:07:47 2022

@author: ilyav
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.signal import find_peaks
from pathlib import Path


import time
import pickle
import os

__version__='2'
__date__='2023.03.23'


def plot_spectra_OSA(folder,label_size=10,wavelength_min=1520,wavelength_max=1580,indicate_peaks=False, plot_graphs=True,
                                threshold=None,height=None,prominence=20,widths=(0,40)):
    folder+='\\'
    pic_folder=Path(folder).parent/'PICS\\'
    f_list=os.listdir(folder)
    plt.figure(1)
    N_f=len(f_list)
    N_plots=int(np.sqrt(N_f))
    figs, axes=plt.subplots(N_plots+1,N_plots+1,figsize=(12,8))
    axes=axes.flatten()
    f, axis = plt.subplots()
    # axis=pl t.gca()
    pump_array=[]
    gen_power_array=[]
    mpl.rcParams['xtick.labelsize'] = label_size 
    
    min_noise_level=2000


    Pumps_with_modes=[]
    measured_output_power=None
    def dBm2W(x):
        return 10**(x/10)/1000
    
        
    def W2dBm(x):
        return 10*np.log10(1000*x)
    
    for i,f in enumerate(f_list):
        try:
            with open(folder+f,'rb') as file:
                [x,y,time_measured,N_averaged,measured_output_power]=pickle.load(file)
        except ValueError as e:
            try:
                with open(folder+f,'rb') as file:
                    [x,y,time_measured,N_averaged]=pickle.load(file)
            except ValueError as e:
                try:
                    with open(folder+f,'rb') as file:
                        [x,y,time_measured]=pickle.load(file)
                except ValueError as e:
                    with open(folder+f,'rb') as file:
                        [x,y,time_measured]=pickle.load(file)
        noise_level=np.max(y[:20])
        if min_noise_level>noise_level:
            min_noise_level=noise_level
        p=int(f.split('.')[0])/10
        x=x*1e9
        indx,_=find_peaks(y-noise_level,threshold=threshold,height=height,prominence=prominence,width=widths)
        if len(indx)>1:
            Pumps_with_modes.append(dBm2W(p))
        try:
            axes[i].plot(x,y,label='{:.1f}'.format(p))
            if indicate_peaks:
                axes[i].plot(x[indx],y[indx],'o')
            axes[i].set_title(p)
            axes[i].set_ylim(bottom=min_noise_level)
        except:
            pass
        
        axis.plot(x,y,label='{:.1f}'.format(p))
        pump_array+=[dBm2W(p)]
        if measured_output_power is not None:
            gen_power_array+=[measured_output_power]
        else:
            gen_power_array+=[np.sum(10**(y/10))]
        # print(f,time_measured)
        
        
    if plot_graphs:
        figs.savefig(pic_folder.__str__()+'\\Spectra layout {}.png'.format(folder.split('\\')[-1]))
        
        axis.set_xlabel('Wavelength, nm')
        axis.set_ylabel('Spectral power density, dBm/nm')
        axis.set_ylim(bottom=min_noise_level)
        axis.set_xlim(((wavelength_min,wavelength_max)))
        
        plt.tight_layout()
        plt.legend()
        plt.show()
        plt.savefig(pic_folder.__str__()+'\\Spectra {}.png'.format(folder.split('\\')[-1]))
        
        
        # figs.tight_layout()
        
        plt.figure(4)
        plt.plot(np.array(pump_array),np.array(gen_power_array))
        plt.xlabel('Pump power, W')
        if  measured_output_power is not None:
            plt.ylabel('Generation power, W')
        else:
            plt.ylabel('Generation power, arb.u.')
        secax = plt.gca().secondary_xaxis('top', functions=(W2dBm,dBm2W))
        secax.set_xlabel('Pump power, dBm')
        for pump in Pumps_with_modes:
           plt.gca().axvspan(dBm2W(W2dBm(pump)-0.049), dBm2W(W2dBm(pump)+0.049), alpha=0.1, color='green')
        plt.tight_layout()
        plt.show()
        plt.savefig(pic_folder.__str__()+'\\Powers {}.png'.format(folder.split('\\')[-1]))
    
    return pump_array,gen_power_array,Pumps_with_modes

if __name__=='__main__':
    # folder=r"D:\Ilya\Second round random laser\SMF-28 32 km\2023.08 No FBG\2023.08.29 spectra\data in forward direction"
    folder=r"D:\Ilya\Second round random laser\SMF-28 32 km\2023.08 No FBG\2023.08.29 spectra\hold data in forward direction"
    plot_spectra_OSA(folder)
