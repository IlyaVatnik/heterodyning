# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 14:47:27 2023

@author: ilyav
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 11:37:33 2020

@author: ilyav
"""
__version__='3'
__date__='2023.04.13'

from matplotlib import pyplot as plt
from matplotlib.ticker import EngFormatter
formatter1 = EngFormatter()
import matplotlib
import numpy as np
import scipy.signal
import scipy.fft as fft
import bottleneck as bn
import pickle
import heterodyning.agilent_bin_beta as b_reader


win_time=1e-6
overlap_time=0
IsAveraging=False
average_time_window=10e-6    
average_freq_window=5e6

low_cut_off=200e6
high_cut_off=200e6

def create_spectrogram_from_data(amplitude_trace,dt,
                                 win_time=win_time,
                                 overlap_time=overlap_time,
                                 IsAveraging=IsAveraging,
                                 average_time_window=average_time_window,    
                                 average_freq_window=average_freq_window,
                                 window='hamming',
                                 cut_off=True):
    '''
    

    Parameters
    ----------
    amplitude_trace : TYPE
        DESCRIPTION.
    dt : TYPE
        DESCRIPTION.
    win_time : TYPE, optional
        DESCRIPTION. The default is win_time.
    overlap_time : TYPE, optional
        DESCRIPTION. The default is overlap_time.
    IsAveraging : TYPE, optional
        DESCRIPTION. The default is IsAveraging.
    average_time_window : TYPE, optional
        DESCRIPTION. The default is average_time_window.
    average_freq_window : TYPE, optional
        DESCRIPTION. The default is average_freq_window.
    cut_off : TYPE, optional
        DESCRIPTION. The default is True.

    Returns
    -------
    s : Spectrogram
        Instance of Spectrogram class, Spectral power =|E_nu|**2
        (not density!)
        
        

    '''
                                 
    freqs, times, spec=scipy.signal.spectrogram(
        amplitude_trace,
        1/dt,
        window=window,
        nperseg=int(win_time/dt),
        noverlap=int(overlap_time/dt),          
        #detrend=False,
        detrend='constant',
        scaling='density',
        mode='psd')
    
    if IsAveraging:
        average_factor_for_freq=int(average_freq_window/(freqs[1]-freqs[0])+1)
        average_factor_for_times=int(average_time_window/(times[1]-times[0])+1)
        # print(average_time_window,times[1],times[0])
        spec=bn.move_mean(spec,average_factor_for_times,1,axis=1)
        spec=bn.move_mean(spec,average_factor_for_freq,1,axis=0)
    
    params=[win_time,
            overlap_time,
            IsAveraging,
            average_time_window,    
            average_freq_window]
    
    
    s=Spectrogram(times,freqs, spec,params)
    if cut_off:
        s.cut_off_low_freqs(low_cut_off)
        s.cut_off_high_freqs(freqs[-1]-high_cut_off)
    return s
    

class Mode():
    def __init__(self,ind,freq,max_intensity=None):
        self.ind=ind
        self.freq=freq
        
        self.birth_time=None
        self.death_time=None
        
        self.life_time=None
        self.max_intensity=max_intensity
        


class Spectrogram():
    def __init__(self,times=None,freqs=None,spec=None,params=None):

        
        self.freqs=freqs
        self.times=times
        self.spec=spec
        
        self.params=params
        
            
        self.fig_spec=None
        self.ax_spec=None
        self.fig_format=None
        
        self.modes=None
        self.N_modes=0

        
        
        
    def set_params(self,win_time,overlap_time,
                   averaging,average_time_window,average_freq_window):
        self.averaging=averaging
        self.win_time=win_time
        self.overlap_time=overlap_time
        self.average_time_window=average_time_window
        self.average_freq_window=average_freq_window
        
        self.needToUpdateSpec=True
    
 
    def plot_spectrogram(self,figsize=(8,6),font_size=11,title='',
                         vmin=None,vmax=None,cmap='jet',lang='en',
                         formatter='sci',scale='lin',
                         show_colorbar=True):
        '''
        

        Parameters
        ----------
        font_size : TYPE, optional
            DESCRIPTION. The default is 11.
        title : TYPE, optional
            DESCRIPTION. The default is ''.
        vmin : TYPE, optional
            DESCRIPTION. The default is None.
        vmax : TYPE, optional
            DESCRIPTION. The default is None.
        cmap : TYPE, optional
            DESCRIPTION. The default is 'jet'.
        lang : TYPE, optional
            DESCRIPTION. The default is 'en'.
        formatter : TYPE, optional
            DESCRIPTION. The default is 'sci'.
        scale : TYPE, optional
            DESCRIPTION. The default is 'lin'.
        show_colorbar : TYPE, optional
            DESCRIPTION. The default is True.

        Returns
        -------
        fig : TYPE
            DESCRIPTION.
        ax : TYPE
            DESCRIPTION.

        '''
        
        
        matplotlib.rcParams.update({'font.size': font_size})
        fig, ax=plt.subplots(figsize=figsize)
        
        
        
        if scale=='lin':
            if formatter=='sci':
                im=ax.pcolorfast(self.times,self.freqs,self.spec,cmap=cmap,vmin=vmin,vmax=vmax)
                ax.xaxis.set_major_formatter(formatter1)
                ax.yaxis.set_major_formatter(formatter1)
                if lang=='en':
                    plt.ylabel('Frequency detuning, Hz')
                    plt.xlabel('Time, s')
                elif lang=='ru':
                    plt.ylabel('Отстройка, Гц')
                    plt.xlabel('Время, сек')
            elif formatter=='normal':
                im=ax.pcolorfast(self.times*1e3,self.freqs/1e6,self.spec/np.max(self.spec),cmap=cmap,vmin=vmin,vmax=vmax)
                if lang=='en':
                    plt.ylabel('Frequency detuning, MHz')
                    plt.xlabel('Time, ms')
                elif lang=='ru':
                    plt.ylabel('Отстройка, МГц')
                    plt.xlabel('Время, мс')
    
            if show_colorbar:
                cbar=plt.colorbar(im)
                if formatter=='sci':
                    cbar.ax.yaxis.set_major_formatter(formatter1)
                if lang=='ru':
                    cbar.set_label('Интенсивность, отн. ед.')
                elif lang=='en':
                    cbar.set_label('Intensity, arb.u.')
            
        elif scale=='log':
            if formatter=='sci':
                im=ax.pcolorfast(self.times,self.freqs,10*np.log10(self.spec),cmap=cmap,vmin=vmin,vmax=vmax)
                ax.xaxis.set_major_formatter(formatter1)
                ax.yaxis.set_major_formatter(formatter1)
                if lang=='en':
                    plt.ylabel('Frequency detuning, Hz')
                    plt.xlabel('Time, s')
                elif lang=='ru':
                    plt.ylabel('Отстройка, Гц')
                    plt.xlabel('Время, сек')
            elif formatter=='normal':
                im=ax.pcolorfast(self.times*1e3,self.freqs/1e6,10*np.log10(self.spec),cmap=cmap,vmin=vmin,vmax=vmax)
                if lang=='en':
                    plt.ylabel('Frequency detuning, MHz')
                    plt.xlabel('Time, ms')
                elif lang=='ru':
                    plt.ylabel('Отстройка, МГц')
                    plt.xlabel('Время, мс')
                    
                    
            if show_colorbar:
                cbar=plt.colorbar(im)
                if formatter=='sci':
                    cbar.ax.yaxis.set_major_formatter(formatter1)
                if lang=='ru':
                    cbar.set_label('Интенсивность, дБ') 
                elif lang=='eng':
                    cbar.set_label('Intensity, dB')

            
        
            
            
            
        self.fig_spec=fig
        self.ax_spec=ax
        self.fig_format=formatter
        

            
        
        plt.title(title)
        plt.tight_layout()
        
        return fig,ax
        
    
    def plot_instant_spectrum(self,time:float,scale='log'):
        ind=np.argmin(abs(self.times-time))
        fig=plt.figure()
        if scale=='lin':
            plt.plot(self.freqs,self.spec[:,ind])
            plt.ylabel('Spectral power, arb.u.')
        elif scale=='log':
            plt.plot(self.freqs,10*np.log10(self.spec[:,ind]))
            plt.ylabel('Spectral power, dB')
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        
        plt.xlabel('Frequency detuning, Hz')
        return fig
    
    
    def remove_osc_spirious_modes(self):
        '''
        Remove spirious peaks appearing in the spectrogram at the partial frequensies of the oscilloscope sampling rate

        Returns
        -------
        None.

        '''
        return 
    
    def cut_off_low_freqs(self,cut_off):
        '''
         high pass filter egde frequency in Hz
        '''
        ind=np.argmin(abs(self.freqs-cut_off))
        self.freqs=self.freqs[ind:]
        self.spec=self.spec[ind:,:]
        
    def cut_off_high_freqs(self,cut_off):
        '''
         low pass filter egde frequency in Hz
        '''
        ind=np.argmin(abs(self.freqs-cut_off))
        self.freqs=self.freqs[:ind]
        self.spec=self.spec[:ind]
        
        
    def find_modes(self,indicate_modes_on_spectrogram=False,prominance_factor=3,height=0.1e-9,min_freq_spacing=1e5,rel_height=0.99,plot_shrinked_spectrum=False):
        self.modes=[]
        signal_shrinked=np.nanmax(self.spec,axis=1)
        dv=self.freqs[1]-self.freqs[0]
        mode_indexes,_=scipy.signal.find_peaks(signal_shrinked, height=height,distance=int(min_freq_spacing/dv)+1,prominence=prominance_factor*bn.nanstd(signal_shrinked))#distance=self.average_freq_window/(1/2/self.dt/len(self.freqs)))
        if plot_shrinked_spectrum:
            plt.figure()
            plt.title('Shrinked spectrum')
            plt.plot(self.freqs,signal_shrinked)
            plt.plot(self.freqs[mode_indexes],signal_shrinked[mode_indexes],'o')
        for mode_number,p in enumerate(mode_indexes):
            self.modes.append(Mode(p,self.freqs[p],max_intensity=signal_shrinked[p]))
            signal=self.spec[p,:]
            peak=np.nanargmax(signal)
            # peaks,_=scipy.signal.find_peaks(signal, height=3*bn.nanstd(signal),width=average_factor_for_times,prominence=3*np.nanstd(signal))
            widths,width_heights,left_ips, right_ips=scipy.signal.peak_widths(signal,[peak],rel_height=rel_height)
            self.modes[mode_number].birth_time=self.times[int(left_ips[0])]
            self.modes[mode_number].death_time=self.times[int(right_ips[0])]
            self.modes[mode_number].life_time=self.modes[mode_number].death_time-self.modes[mode_number].birth_time
            
        if self.fig_spec is not None and indicate_modes_on_spectrogram:
            if self.fig_format=='normal':
                extraticks=[x.freq/1e6 for x in self.modes]
            elif self.fig_format=='sci':
                extraticks=[x.freq for x in self.modes]
            loc=matplotlib.ticker.FixedLocator(extraticks)
            self.fig_spec.axes[0].yaxis.set_minor_locator(loc)
            self.fig_spec.axes[0].tick_params(which='minor', length=10, color='r',width=5)
            # plt.yticks(minor=True)
            # self.fig_spec.axes[0].axhline(self.freqs,color='yellow',linewidth=2)
            
        self.N_modes=len(self.modes)
        return self.modes
    
    
    def get_mode_freqs(self):
        freqs=[]
        for m in self.modes:
            freqs.append(m.freq)
        return np.array(freqs)
    
    def plot_all_modes(self):
        for i,_ in enumerate(self.modes):
            self.plot_mode_dynamics(i)
            plt.title(r'$\delta \nu$={:.0f} MHz, life time={:.2f} ms'.format(self.modes[i].freq/1e6,self.modes[i].life_time*1e3))
            plt.axvline(self.modes[i].birth_time)
            plt.axvline(self.modes[i].death_time)
            
    def print_all_modes(self):
        if self.N_modes>0:
            for i,_ in enumerate(self.modes):
                print('Mode {}, detuning={:.0f} MHz, life time={:.2f} ms, max intensity={:.3e}'.format(i,self.modes[i].freq/1e6,self.modes[i].life_time*1e3,self.modes[i].max_intensity))
        else:
            print('No mode found on spectrogram')

    
    
    
    def remove_mode_copies(self):
        sz = len(self.modes)
        i = 0
        while i < sz:
            j = i + 1
            while j < sz:
                if self.modes[i].ind == self.modes[j].ind:
                    self.modes.pop(j)
                    sz -= 1
                else:
                    j += 1
            i += 1
            
    def get_modes_freqs(self):
        '''
    
        Returns
        -------
        np.array
            frequensies  of modes found

        '''
        
        freqs=[]
        for m in self.modes:
            freqs.append(m.freq)
        return np.array(freqs)
            
   
    def get_mode_number(self,frequency,resolution=0):
        if resolution==0:
            resolution=self.average_freq_window*3
        for ii,m in enumerate(self.modes):
            if abs(frequency-m.freq)<resolution:
                return ii
        return False
   
    def get_mode_dynamics(self,mode_number,normed=False):
        mode_index=self.modes[mode_number].ind
        signal=self.spec[mode_index,:]
        if normed:
            signal=signal/max(signal)
        return self.times,signal
    
    def get_dynamics_at_freq(self,freq):
        freq_index=np.argmin(abs((self.freqs-freq)))
        return self.spec[freq_index,:]
    
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
        signal=self.spec[mode_index,:]
        fig=plt.figure()  
        N=len(self.times)
        dT=self.times[1]-self.times[0]
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
        signal=self.spec[mode_index,:]
        # average_factor_for_times=int(self.average_time_window/(self.win_time-self.overlap_time))
        # signal=bn.move_mean(signal,100)
        peak=np.nanargmax(signal)
        # peaks,_=scipy.signal.find_peaks(signal, height=3*bn.nanstd(signal),width=average_factor_for_times,prominence=3*np.nanstd(signal))
        widths,width_heights,left_ips, right_ips=scipy.signal.peak_widths(signal,[peak],rel_height=0.8)
        self.modes[mode_number].birth_time=self.times[int(left_ips[0])]
        self.modes[mode_number].death_time=self.times[int(right_ips[0])]
        self.modes[mode_number].life_time=self.modes[mode_number].death_time-self.modes[mode_number].birth_time
        
        # plt.hlines(0,xmin=self.modes[mode_number].birth_time,xmax=self.modes[mode_number].death_time,color='red')
        return int(left_ips[0]),int(right_ips[0]),self.modes[mode_number].life_time,self.modes[mode_number].birth_time,self.modes[mode_number].death_time
    
    def get_lifetime_hist(self, plot_hist=False,indicate_lifetimes=False):
        life_times=[]
        if self.modes is not None:
            for p,mode in enumerate(self.modes):
                life_times.append(self.get_mode_lifetime(p))
        if indicate_lifetimes:
            if self.fig_spec is None:
                self.plot_spectrogram()
            for mode in self.modes:
                self.ax_spec.hlines(mode.freq,xmin=mode.birth_time, xmax=mode.death_time,color='red')
        if plot_hist:
            plt.figure(33)
            plt.hist(life_times)
            plt.xlabel('Time, s')
            plt.ylabel('Number of modes')       
            plt.gca().xaxis.set_major_formatter(formatter1)    
        return life_times
    
    
    def save_to_file(self,file,as_object=False):
        with open(file, 'wb') as f:
            if as_object:
                pickle.dump(self,f)
            else:
                pickle.dump([self.times,self.freqs,self.spec,self.params],f)
                
                
def load_from_file(file):
    with open(file, 'rb') as f:
        obj=pickle.load(f)
    if not isinstance(obj,list):
        return obj
    else:
        times,freqs, spec,params=obj
        return Spectrogram(times,freqs, spec,params)
        
        
    
    


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
                                              mode='psd')
    spec=np.rot90(spec)
    return freq,time,spec
    

def average_spectrogram(spec:Spectrogram,average_freq_window=None,average_time_window=None):
    import copy
    spec_1=copy.copy(spec)
    if average_freq_window is not None:
        average_factor_for_freq=int(average_freq_window/(spec_1.freqs[1]-spec_1.freqs[0]))
        spec_1.spec=bn.move_mean(spec_1.spec,average_factor_for_freq,1,axis=0)
    if average_time_window is not None:                
        average_factor_for_times=int(average_time_window/(spec_1.times[1]-spec_1.times[0]))
        spec_1.spec=bn.move_mean(spec_1.spec,average_factor_for_times,1,axis=1)
    
    return spec_1
    

    
def create_spectrogram_from_file_two_channels_agilent(f_name,
                                                      win_time=3e-6,
                                                      overlap_time=2.5e-6,
                                                      IsAveraging=True,
                                                      average_time_window=50e-6,    
                                                      average_freq_window=10e6,
                                                      channels=[1,3]):
    
    def _get_heterodyning_spectrogram(data_dict,win_time,overlap_time):
        Chan='Channel_'+str(channels[0])
        dt=data_dict[Chan]['x_increment']
        freq, time, spec=scipy.signal.spectrogram(data_dict[Chan]['data']-np.mean(data_dict[Chan]['data']),
                                                  1/dt,
                                                  window='triang',
                                                  nperseg=int(win_time/dt),
                                                  noverlap=int(overlap_time/dt),
                                                  detrend=False,
                                                  scaling='spectrum',
                                                  mode='psd')
        # spec=np.rot90(spec)
        return freq,time,spec
    
    def _get_power_spectrogram(data_dict,win_time,overlap_time):
        Chan='Channel_'+str(channels[1])
        dt=data_dict[Chan]['x_increment']
        freq, time, spec=scipy.signal.spectrogram(data_dict[Chan]['data']-np.mean(data_dict[Chan]['data']),
                                                  1/dt,
                                                  window='triang',
                                                  nperseg=int(win_time/dt),
                                                  noverlap=int(overlap_time/dt),
                                                  detrend=False,
                                                  scaling='spectrum',
                                                  mode='psd')
        # spec=np.rot90(spec)
        return freq,time,spec
    
    
    data_dict=b_reader.read(f_name)
    freq, time, spec_1=_get_heterodyning_spectrogram(data_dict,win_time,overlap_time)
    m1=np.mean(spec_1)
    s1=np.std(spec_1)
    freq, time, spec_2=_get_power_spectrogram(data_dict,win_time,overlap_time)
    m3=np.mean(spec_2)
    s3=np.std(spec_2)
    mask=spec_2>m3+2*s3
    spec_1[mask]=m1-s1*np.random.ranf(mask[mask==True].size)

    if IsAveraging:
        
        average_factor_for_freq=int(average_freq_window/(freq[1]-freq[0]))
        average_factor_for_times=int(average_time_window/(win_time-overlap_time))
    

        spec_1=bn.move_mean(spec_1,average_factor_for_times,1,axis=1)
        spec_1=bn.move_mean(spec_1,average_factor_for_freq,1,axis=0)

    # spec=spec_1-(bn.nanmean(spec_1,axis=0)).reshape(len(time),0)
    params=[win_time,
            overlap_time,
            IsAveraging,
            average_time_window,    
            average_freq_window,
            channels]
    return Spectrogram(time,freq, spec_1,params)

def get_mode_ratio(spec1:Spectrogram,spec2:Spectrogram,mode:Mode):
    t=spec1.times
    i1=int(np.argwhere(t==mode.birth_time))
    i2=int(np.argwhere(t==mode.death_time))
    
    I1=spec1.spec[mode.ind,:]
    I2=spec2.spec[mode.ind,:]
    t,I1,I2=t[i1:i2],I1[i1:i2],I2[i1:i2]
    Ratio_dependence=I2/I1
    Ratio,Ratio_error=np.mean(Ratio_dependence),np.std(Ratio_dependence)/np.mean(Ratio_dependence)
    return Ratio, Ratio_error,t,Ratio_dependence
        
if __name__=='__main__':
    f=r"D:\Ilya\Second round random laser\SMF-28 32 km\2023.03.16-17 testing different polarizations\At 1550.35\spectrogram_examples\1\Large R 1.spec"
    spec=load_from_file(f)
    spec.plot_spectrogram()
    