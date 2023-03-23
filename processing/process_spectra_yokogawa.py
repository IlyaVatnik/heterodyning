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



def process_spectra_from_folder(folder,label_size=10,wavelength_min=1549,wavelength_max=1552,indicate_peaks=False):
    folder+='\\'
    pic_folder=Path(folder).parent/'PICS\\'
    f_list=os.listdir(folder)
    plt.figure(1)
    N_f=len(f_list)
    N_plots=int(np.sqrt(N_f))
    figs, axes=plt.subplots(N_plots,N_plots+1,figsize=(12,8))
    axes=axes.flatten()
    f, axis = plt.subplots()
    # axis=pl t.gca()
    pump_array=[]
    gen_power_array=[]
    mpl.rcParams['xtick.labelsize'] = label_size 
    
    min_noise_level=2000


    Pumps_with_modes=[]

    def dBm2W(x):
        return 10**(x/10)/1000
    
    
    def W2dBm(x):
        return 10*np.log10(1000*x)
    
    for i,f in enumerate(f_list):
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
        indx,_=find_peaks(y-noise_level,threshold=0.5,height=10,prominence=3,width=(0,40))
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
        gen_power_array+=[np.sum(10**(y/10))]
        # print(f,time_measured)
        
    figs.savefig(pic_folder.__str__()+'\\Spectra layout {}.png'.format(folder.split('\\')[-1]))
    
    axis.set_xlabel('Wavelength, nm')
    axis.set_ylabel('Spectral power density, dBm/nm')
    axis.set_ylim(bottom=min_noise_level)
    axis.set_xlim(((wavelength_min,wavelength_max)))
    
    # plt.tight_layout()
    # plt.legend()
    # plt.show()
    plt.savefig(pic_folder.__str__()+'\\Spectra {}.png'.format(folder.split('\\')[-1]))
    
    
    # figs.tight_layout()
    
    plt.figure(4)
    plt.plot(np.array(pump_array),np.array(gen_power_array))
    plt.xlabel('Pump power, W')
    plt.ylabel('Generation power, arb.u')
    secax = plt.gca().secondary_xaxis('top', functions=(W2dBm,dBm2W))
    secax.set_xlabel('Pump power, dBm')
    for pump in Pumps_with_modes:
       plt.gca().axvspan(dBm2W(W2dBm(pump)-0.049), dBm2W(W2dBm(pump)+0.049), alpha=0.1, color='green')
    plt.tight_layout()
    plt.show()
    plt.savefig(pic_folder.__str__()+'\\Powers {}.png'.format(folder.split('\\')[-1]))

if __name__=='__main__':
    folder=r"F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\2023-2022 different fibers and different data\SMF-28 32 km\2022.11.29 yokogawa spectra test\data"
    process_spectra_from_folder(folder)
