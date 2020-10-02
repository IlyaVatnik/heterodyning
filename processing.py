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

# import heterodyning.scope_bin_parser as b_reader
import heterodyning.agilent_bin_beta as b_reader

formatter1 = EngFormatter(places=2)

class Data():
    def __init__(self,f_name,
                 win_time=3e-6,
                 overlap_time=2.5e-6,
                 average_time_window=50e-6,    
                 average_freq_window=10e6):
        self.dict=b_reader.read(f_name)
        self.win_time=win_time
        self.overlap_time=overlap_time
        self.average_time_window=average_time_window
        self.average_freq_window=average_freq_window
        
        self.freq=None
        self.time=None
        self.processed_spec=None
        self.dt=self.dict['Channel_1']['x_increment']
        self.need_to_update_spec=True
        
        self.fig_spec=None
        self.ax_spec=None
        self.mode_indexes=None
        
        
    def set_params(self,win_time,overlap_time,
                   IsAveraging,average_time_window,average_freq_window):
        self.IsAveraging=IsAveraging
        self.win_time=win_time
        self.overlap_time=overlap_time
        self.average_time_window=average_time_window
        self.average_freq_window=average_freq_window
        
        self.needToUpdateSpec=True
    
    def get_heterodyning_spectrogram(self,win_time,overlap_time):
        Chan='Channel_1'
        dt=self.dict[Chan]['x_increment']
        freq, time, spec=scipy.signal.spectrogram(self.dict[Chan]['data']-np.mean(self.dict[Chan]['data']),
                                                  1/dt,
                                                  window='triang',
                                                  nperseg=int(win_time/dt),
                                                  noverlap=int(overlap_time/dt),
                                                  detrend=False,
                                                  scaling='spectrum',
                                                  mode='magnitude')
        spec=np.rot90(spec)
        return freq,time,spec
    
    def get_power_spectrogram(self,win_time,overlap_time):
        Chan='Channel_3'
        dt=self.dict[Chan]['x_increment']
        freq, time, spec=scipy.signal.spectrogram(self.dict[Chan]['data']-np.mean(self.dict[Chan]['data']),
                                                  1/dt,
                                                  window='triang',
                                                  nperseg=int(win_time/dt),
                                                  noverlap=int(overlap_time/dt),
                                                  detrend=False,
                                                  scaling='spectrum',
                                                  mode='magnitude')
        spec=np.rot90(spec)
        return freq,time,spec
    
    def process_spectrogram(self):
        freq, time, spec_1=self.get_heterodyning_spectrogram(self.win_time,self.overlap_time)
        m1=np.mean(spec_1)
        s1=np.std(spec_1)
        freq, time, spec_2=self.get_power_spectrogram(self.win_time,self.overlap_time)
        m3=np.mean(spec_2)
        s3=np.std(spec_2)
        mask=spec_2>m3+2*s3
        spec_1[mask]=m1-s1*np.random.ranf(mask[mask==True].size)

    
        average_factor_for_freq=int(self.average_freq_window/(1/2/self.dt/len(freq)))
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
        self.plot_spectrogram(self.freq,self.time,self.processed_spec)

    def plot_spectrogram(self,freq,time,spec):
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
        signal_shrinked=np.nanmax(self.processed_spec,axis=0)
        mode_indexes,_=scipy.signal.find_peaks(signal_shrinked, height=bn.nanstd(signal_shrinked),prominence=bn.nanstd(signal_shrinked))#distance=self.average_freq_window/(1/2/self.dt/len(self.freq)))
        if self.fig_spec is not None and indicate_modes_on_spectrogram:
            for p in mode_indexes:
                plt.axvline(self.freq[p],color='white')
        self.mode_indexes=mode_indexes
        return mode_indexes 
    
    def plot_mode_dynamics(self,mode_index):
        signal=self.processed_spec[:,mode_index]
        fig=plt.figure()
        plt.plot(self.time,signal)
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        plt.xlabel('Time, s')      
        plt.ylabel('Intensity, arb.u.')
        plt.title('Mode at {:.3f} MHz'.format(self.freq[mode_index]/1e6))
        plt.tight_layout()
        return fig
        
    def plot_mode_lowfreq_spectrum(self,mode_index):
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
        plt.title('Mode spectrum at {:.3f} MHz'.format(self.freq[mode_index]/1e6))
        plt.tight_layout()
        return fig

    def get_mode_lifetime(self,mode_index):
        signal=self.processed_spec[:,mode_index]
        average_factor_for_times=int(self.average_time_window/(self.win_time-self.overlap_time))
        peaks,_=scipy.signal.find_peaks(signal, height=5*bn.nanstd(signal),width=average_factor_for_times,prominence=3*np.nanstd(signal))
        widths,width_heights,left_ips, right_ips=scipy.signal.peak_widths(signal,peaks,rel_height=0.9)
        return self.time[int(right_ips[0])]-self.time[int(left_ips[0])]
    
    def get_lifetime_hist(self):
        life_times=[]
        if self.mode_indexes is not None:
            for p in self.mode_indexes:
                life_times.append(self.get_mode_lifetime(p))
            

        
if __name__=='__main__':
    print('')
    