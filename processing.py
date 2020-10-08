# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 11:37:33 2020

@author: ilyav
"""


from matplotlib import pyplot as plt
from matplotlib.ticker import EngFormatter
import numpy as np
import scipy.signal
import scipy.fft as fft
import bottleneck as bn

import heterodyning.agilent_bin_beta as b_reader

formatter1 = EngFormatter(places=2)


class Mode():
    def __init__(self,ind,freq):
        self.ind=ind
        self.freq=freq
        
        self.birth_time=None
        self.death_time=None
        
        self.life_time=None

class Spectrogram():
    def __init__(self,f_name,
                 win_time=3e-6,
                 overlap_time=2.5e-6,
                 IsAveraging=True,
                 average_time_window=50e-6,    
                 average_freq_window=10e6,
                 channels=[1,3]):
           
        self.win_time=win_time
        self.overlap_time=overlap_time
        self.IsAveraging=IsAveraging
        self.average_time_window=average_time_window
        self.average_freq_window=average_freq_window
        
        
        self.dt=None
        self.freq=None
        self.time=None
        self.processed_spec=None
        self.need_to_update_spec=True
        
        self.fig_spec=None
        self.ax_spec=None
        
        self.modes=None
        
               
        self.process_spectrogram(f_name,channels)
        
        
        
        
    def set_params(self,win_time,overlap_time,
                   IsAveraging,average_time_window,average_freq_window):
        self.IsAveraging=IsAveraging
        self.win_time=win_time
        self.overlap_time=overlap_time
        self.average_time_window=average_time_window
        self.average_freq_window=average_freq_window
        
        self.needToUpdateSpec=True
    
    def _get_heterodyning_spectrogram(self,data_dict,win_time,overlap_time,ch_number):
        Chan='Channel_'+str(ch_number)
        dt=data_dict[Chan]['x_increment']
        freq, time, spec=scipy.signal.spectrogram(data_dict[Chan]['data']-np.mean(data_dict[Chan]['data']),
                                                  1/dt,
                                                  window='triang',
                                                  nperseg=int(win_time/dt),
                                                  noverlap=int(overlap_time/dt),
                                                  detrend=False,
                                                  scaling='spectrum',
                                                  mode='magnitude')
        spec=np.rot90(spec)
        return freq,time,spec
    
    def _get_power_spectrogram(self,data_dict,win_time,overlap_time,ch_number):
        Chan='Channel_'+str(ch_number)
        dt=data_dict[Chan]['x_increment']
        freq, time, spec=scipy.signal.spectrogram(data_dict[Chan]['data']-np.mean(data_dict[Chan]['data']),
                                                  1/dt,
                                                  window='triang',
                                                  nperseg=int(win_time/dt),
                                                  noverlap=int(overlap_time/dt),
                                                  detrend=False,
                                                  scaling='spectrum',
                                                  mode='magnitude')
        spec=np.rot90(spec)
        return freq,time,spec
    
    def process_spectrogram(self,f_name,channels):
        data_dict=b_reader.read(f_name)
        freq, time, spec_1=self._get_heterodyning_spectrogram(data_dict,self.win_time,self.overlap_time,channels[0])
        m1=np.mean(spec_1)
        s1=np.std(spec_1)
        freq, time, spec_2=self._get_power_spectrogram(data_dict,self.win_time,self.overlap_time,channels[1])
        m3=np.mean(spec_2)
        s3=np.std(spec_2)
        mask=spec_2>m3+2*s3
        spec_1[mask]=m1-s1*np.random.ranf(mask[mask==True].size)

    
        average_factor_for_freq=int(self.average_freq_window/(freq[1]-freq[0]))
        average_factor_for_times=int(self.average_time_window/(self.win_time-self.overlap_time))
        
        if self.IsAveraging:
            spec_1=bn.move_mean(spec_1,average_factor_for_times,1,axis=0)
            spec_1=bn.move_mean(spec_1,average_factor_for_freq,1,axis=1)
        
        self.freq=freq
        self.time=time
        self.processed_spec=spec_1-(bn.nanmean(spec_1,axis=1)).reshape(len(self.time),1)
        self.need_to_update_spec=False
        return freq, time, spec_1
    
    def plot_processed_spectrogram(self):
        if self.need_to_update_spec:
            self.process_spectrogram()
        self._plot_spectrogram(self.freq,self.time,self.processed_spec)

    def _plot_spectrogram(self,freq,time,spec):
        fig, ax=plt.subplots()
        im=ax.pcolorfast(freq, time, spec, cmap='jet')
        ax.xaxis.set_major_formatter(formatter1)
        ax.yaxis.set_major_formatter(formatter1)
        plt.xlabel('Frequency, Hz')
        plt.ylabel('Time, s')
        plt.tight_layout()
        plt.colorbar(im)
        self.fig_spec=fig
        self.ax_spec=ax
        
    def find_modes(self,indicate_modes_on_spectrogram=False):
        self.modes=[]
        signal_shrinked=np.nanmax(self.processed_spec,axis=0)
        mode_indexes,_=scipy.signal.find_peaks(signal_shrinked, height=bn.nanstd(signal_shrinked),prominence=bn.nanstd(signal_shrinked))#distance=self.average_freq_window/(1/2/self.dt/len(self.freq)))
        for p in mode_indexes:
            self.modes.append(Mode(p,self.freq[p]))
            if self.fig_spec is not None and indicate_modes_on_spectrogram:
                plt.axvline(self.freq[p],color='white')
            
        return self.modes
    
    def plot_mode_dynamics(self,mode_number):
        mode_index=self.modes[mode_number].ind
        signal=self.processed_spec[:,mode_index]
        fig=plt.figure()
        plt.plot(self.time,signal)
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        plt.xlabel('Time, s')      
        plt.ylabel('Intensity, arb.u.')
        plt.title('Mode at {:.1f} MHz detuning'.format(self.freq[mode_index]/1e6))
        plt.tight_layout()
        return fig, plt.gca()
        
    def plot_mode_lowfreq_spectrum(self,mode_number):
        mode_index=self.modes[mode_number].ind
        signal=self.processed_spec[:,mode_index]
        fig=plt.figure()  
        N=len(self.time)
        dT=self.time[1]-self.time[0]
        yf = fft.fft(signal)
        xf = np.linspace(0.0, 1.0/(2.0*dT), N//2)
        plt.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
        plt.xlabel('Frequency, Hz')      
        plt.ylabel('Intensity,arb.u.')
        plt.tight_layout()
        plt.gca().set_xlim((100,10e3))
        plt.gca().set_ylim((0,5e-6))
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        plt.title('RF spectrum for mode at {:.1f} MHz detuning'.format(self.freq[mode_index]/1e6))
        plt.tight_layout()
        return fig, plt.gca()

    def get_mode_lifetime(self,mode_number):
        mode_index=self.modes[mode_number].ind
        signal=self.processed_spec[:,mode_index]
        average_factor_for_times=int(self.average_time_window/(self.win_time-self.overlap_time))
        signal=bn.move_mean(signal,100)
        peak=np.nanargmax(signal)
        # peaks,_=scipy.signal.find_peaks(signal, height=3*bn.nanstd(signal),width=average_factor_for_times,prominence=3*np.nanstd(signal))
        widths,width_heights,left_ips, right_ips=scipy.signal.peak_widths(signal,[peak],rel_height=0.9)
        self.modes[mode_number].birth_time=self.time[int(left_ips[0])]
        self.modes[mode_number].death_time=self.time[int(right_ips[0])]
        self.modes[mode_number].life_time=self.modes[mode_number].death_time-self.modes[mode_number].birth_time
        
        # plt.hlines(0,xmin=self.modes[mode_number].birth_time,xmax=self.modes[mode_number].death_time,color='red')
        return self.modes[mode_number].life_time,self.modes[mode_number].birth_time,self.modes[mode_number].death_time
    
    def get_lifetime_hist(self):
        life_times=[]
        if self.modes is not None:
            for p,_ in enumerate(self.modes['ind']):
                life_times.append(self.get_mode_lifetime(p))
            plt.hist(life_times)
            plt.xlabel('Time, s')
            plt.ylabel('Number of modes')       
            plt.gca().xaxis.set_major_formatter(formatter1)
            

        
if __name__=='__main__':
    print()
    