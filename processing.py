# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 11:37:33 2020

@author: ilyav
"""


from matplotlib import pyplot as plt
from matplotlib.ticker import EngFormatter
formatter1 = EngFormatter()
import matplotlib
import numpy as np
import scipy.signal
import scipy.fft as fft
import bottleneck as bn

import heterodyning.agilent_bin_beta as b_reader





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
                 averaging=True,
                 average_time_window=50e-6,    
                 average_freq_window=10e6,
                 channels=[1,3],
                 extract_power_spectrogram=True):
           
        self.f_name=f_name
        
        self.win_time=win_time
        self.overlap_time=overlap_time
        self.averaging=averaging
        self.average_time_window=average_time_window
        self.average_freq_window=average_freq_window
        
        
        self.dt=None
        self.freq=None
        self.time=None
        self.spec=None
        self.need_to_update_spec=True
        
        self.fig_spec=None
        self.ax_spec=None
        
        self.modes=None
        self.channels=channels
               
        self._process_spectrogram(extract_power_spectrogram)
        
        
        
        
    def set_params(self,win_time,overlap_time,
                   averaging,average_time_window,average_freq_window):
        self.averaging=averaging
        self.win_time=win_time
        self.overlap_time=overlap_time
        self.average_time_window=average_time_window
        self.average_freq_window=average_freq_window
        
        self.needToUpdateSpec=True
    
    def _get_heterodyning_spectrogram(self,data_dict,win_time,overlap_time):
        Chan='Channel_'+str(self.channels[0])
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
    
        
        
    def _get_power_spectrogram(self,data_dict,win_time,overlap_time):
        Chan='Channel_'+str(self.channels[1])
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
    
    
    def _process_spectrogram(self,extract_power_spectrogram):
        data_dict=b_reader.read(self.f_name)
        freq, time, spec_1=self._get_heterodyning_spectrogram(data_dict,self.win_time,self.overlap_time)
        if extract_power_spectrogram==True:
            m1=np.mean(spec_1)
            s1=np.std(spec_1)
            freq, time, spec_2=self._get_power_spectrogram(data_dict,self.win_time,self.overlap_time)
            m3=np.mean(spec_2)
            s3=np.std(spec_2)
            mask=spec_2>m3+2*s3
            spec_1[mask]=m1-s1*np.random.ranf(mask[mask==True].size)

    
        average_factor_for_freq=int(self.average_freq_window/(freq[1]-freq[0]))
        average_factor_for_times=int(self.average_time_window/(self.win_time-self.overlap_time))
        
        if self.averaging:
            spec_1=bn.move_mean(spec_1,average_factor_for_times,1,axis=0)
            spec_1=bn.move_mean(spec_1,average_factor_for_freq,1,axis=1)
        
        self.freq=freq
        self.time=time
        self.spec=spec_1-(bn.nanmean(spec_1,axis=1)).reshape(len(self.time),1)
        self.need_to_update_spec=False
        return freq, time, self.spec
    
    def plot_spectrogram(self,font_size=11,title=True,vmin=None,vmax=None,cmap='jet',extract_power_spectrogram=True):
        if self.need_to_update_spec:
            self._process_spectrogram(extract_power_spectrogram)
        matplotlib.rcParams.update({'font.size': font_size})
        fig, ax=plt.subplots()
        im=ax.pcolorfast(self.freq, self.time, self.spec, cmap=cmap,vmin=vmin,vmax=vmax)
        ax.xaxis.set_major_formatter(formatter1)
        ax.yaxis.set_major_formatter(formatter1)
        plt.xlabel('Frequency detuning, Hz')
        plt.ylabel('Time, s')
        cbar=plt.colorbar(im)
        cbar.set_label('Intensity, arb.u.')
        if title:
            if self.channels==[1,3]:
                plt.title('forward')
            elif self.channels==[2,4]:
                plt.title('backward')
            else:
                plt.title(str(self.channels))           
        self.fig_spec=fig
        self.ax_spec=ax
        plt.tight_layout()
        
        return fig,ax
        
    def find_modes(self,indicate_modes_on_spectrogram=False):
        self.modes=[]
        signal_shrinked=np.nanmax(self.spec,axis=0)
        mode_indexes,_=scipy.signal.find_peaks(signal_shrinked, height=bn.nanstd(signal_shrinked),prominence=bn.nanstd(signal_shrinked))#distance=self.average_freq_window/(1/2/self.dt/len(self.freq)))
        for p in mode_indexes:
            self.modes.append(Mode(p,self.freq[p]))
            if self.fig_spec is not None and indicate_modes_on_spectrogram:
                self.fig_spec.axes[0].axvline(self.freq[p],color='white')
            
        return self.modes
   
    def get_mode_number(self,frequency,resolution=0):
        if resolution==0:
            resolution=self.average_freq_window*3
        for ii,m in enumerate(self.modes):
            if abs(frequency-m.freq)<resolution:
                return ii
        return False
   
    def get_mode_dynamics(self,mode_number,normed=False):
        mode_index=self.modes[mode_number].ind
        signal=self.spec[:,mode_index]
        if normed:
            signal=signal/max(signal)
        return self.time,signal
    
    def plot_mode_dynamics(self,mode_number,NewFigure=True):
        time,signal=self.get_mode_dynamics(mode_number)
        if NewFigure:
            fig=plt.figure()
        plt.plot(time,signal)
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        plt.xlabel('Time, s')      
        plt.ylabel('Intensity, arb.u.')
        plt.title('Mode at {:.1f} MHz detuning'.format(self.modes[mode_number].freq/1e6))
        plt.tight_layout()
        return fig, plt.gca()
        
    def plot_mode_lowfreq_spectrum(self,mode_number):
        mode_index=self.modes[mode_number].ind
        signal=self.spec[:,mode_index]
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
        plt.title('RF spectrum for mode at {:.1f} MHz detuning'.format(self.modes[mode_number].freq/1e6))
        plt.tight_layout()
        return fig, plt.gca()

    def get_mode_lifetime(self,mode_number:int):
        mode_index=self.modes[mode_number].ind
        signal=self.spec[:,mode_index]
        average_factor_for_times=int(self.average_time_window/(self.win_time-self.overlap_time))
        signal=bn.move_mean(signal,100)
        peak=np.nanargmax(signal)
        # peaks,_=scipy.signal.find_peaks(signal, height=3*bn.nanstd(signal),width=average_factor_for_times,prominence=3*np.nanstd(signal))
        widths,width_heights,left_ips, right_ips=scipy.signal.peak_widths(signal,[peak],rel_height=0.8)
        self.modes[mode_number].birth_time=self.time[int(left_ips[0])]
        self.modes[mode_number].death_time=self.time[int(right_ips[0])]
        self.modes[mode_number].life_time=self.modes[mode_number].death_time-self.modes[mode_number].birth_time
        
        # plt.hlines(0,xmin=self.modes[mode_number].birth_time,xmax=self.modes[mode_number].death_time,color='red')
        return self.modes[mode_number].life_time,self.modes[mode_number].birth_time,self.modes[mode_number].death_time
    
    def get_lifetime_hist(self, plot_hist=False,indicate_lifetimes=False):
        life_times=[]
        if self.modes is not None:
            for p,mode in enumerate(self.modes):
                life_times.append(self.get_mode_lifetime(p))
        if indicate_lifetimes:
            if self.fig_spec is None:
                self.plot_spectrogram()
            for mode in self.modes:
                self.ax_spec.vlines(mode.freq,ymin=mode.birth_time, ymax=mode.death_time,color='red')
        if plot_hist:
            plt.figure(33)
            plt.hist(life_times)
            plt.xlabel('Time, s')
            plt.ylabel('Number of modes')       
            plt.gca().xaxis.set_major_formatter(formatter1)    
        return life_times
            
    
# =============================================================================
#     
# =============================================================================

def get_total_spectrum(f_name,channel=1):
    from scipy.fft import fft
    data_dict=b_reader.read(f_name)
    Chan='Channel_'+str(channel)
    data=data_dict[Chan]['data']-np.mean(data_dict[Chan]['data'])
    spectrum=fft(data)
    N=len(data)
    dT=data_dict[Chan]['x_increment']
    freqs = np.linspace(0.0, 1.0/(2.0*dT), N//2)
    spectrum=2.0/N * np.abs(spectrum[0:N//2])
    return freqs, spectrum

def get_power_dynamics(f_name,channel=3):
    data_dict=b_reader.read(f_name)
    Chan='Channel_'+str(channel)
    data=data_dict[Chan]['data']
    dT=data_dict[Chan]['x_increment']
    times = np.arange(0,len(data))*dT
    return times, data

def get_power_spectrogram(f_name,win_time,overlap_time,channel=3):
    data_dict=b_reader.read(f_name)
    Chan='Channel_'+str(channel)
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
    


        
if __name__=='__main__':
    print()
    