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
__version__='5.3'
__date__='2025.04.01'

from matplotlib import pyplot as plt
from matplotlib.ticker import EngFormatter
formatter1 = EngFormatter()
import matplotlib
import numpy as np
import scipy.signal
import scipy.fft as fft
from scipy.interpolate import interp1d
import bottleneck as bn
import pickle
import heterodyning.agilent_bin_beta as b_reader
import warnings
warnings.filterwarnings("error")




def create_spectrogram_from_data(amplitude_trace,dt,
                                 win_time=1e-6,
                                 overlap_time=0,
                                 IsAveraging=False,
                                 average_time_window=0.1e-6 ,    
                                 average_freq_window=10e6,
                                 window='hamming',
                                 cut_off=True,
                                 low_cut_off=00e6,
                                 high_cut_off=100e9,
                                 real_power_coeff=0,
                                 calibration_curve=None):
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
        
    real_power_coeff: 
        if not zero, then spec is power in W !!!!!!
        ratio of real power to acquired in spectrogram
        
    calibration curve:
        real_power coefficient taking into account dependence on frequency detuning
        
    Returns
    -------
    s : Spectrogram
        Instance of Spectrogram class, Spectral power =|E_nu|**2 
        
        
        
        
        

    '''
    if win_time==0:
        win_time=dt*len(amplitude_trace)
    freqs, times, spec=scipy.signal.spectrogram(
        amplitude_trace,
        1/dt,
        window=window,
        nperseg=int(win_time/dt),
        noverlap=int(overlap_time/dt),          
        #detrend=False,
        detrend='constant',
        # scaling='density',
        scaling='spectrum',
        mode='psd')
    
    if IsAveraging:
        average_factor_for_freq=int(average_freq_window/(freqs[1]-freqs[0])+1)
        average_factor_for_times=int(average_time_window/(times[1]-times[0])+1)
        # print(average_time_window,times[1],times[0])
        spec=bn.move_mean(spec,average_factor_for_times,1,axis=1)
        spec=bn.move_sum(spec,average_factor_for_freq,1,axis=0)
    
    params=[win_time,
            overlap_time,
            IsAveraging,
            average_time_window,    
            average_freq_window]
    
    
    s=Spectrogram(times,freqs, spec,params)
    if calibration_curve is not None:
        s.spec/=calibration_curve.reshape((len(s.spec),1))*np.ones((np.shape(s.spec)))
        s.real_power_mode=True
    elif real_power_coeff!=0:
        s.spec/=real_power_coeff
        s.real_power_mode=True
        
    if cut_off:
        s.cut_off_low_freqs(low_cut_off)
        s.cut_off_high_freqs(high_cut_off)
    
    return s
    

def create_calibration_curve(device_calibration_file_names, LO_power,dt,win_time,R_osc=50,balanced=True):
    '''
    device_calibration_file_names=[device1_calibraion_file,device2_calibration_file,...]
    LO_power - in mW
    R_osc - in Om
    '''
    freqs, _,_=scipy.signal.spectrogram(
        np.zeros(int(win_time/dt)*10),
        1/dt,
        nperseg=int(win_time/dt), # to match the number of points with difinition in 'create_spectrogram_from_data'
        noverlap=0)
    
    K_product=np.ones(len(freqs))
    for file in device_calibration_file_names:
        data=np.genfromtxt(file,delimiter='\t',skip_header=2)
        freqs_device=data[:,0]
        Koefficient_device=data[:,1]
        
        interp_func = interp1d(freqs_device*1e6, Koefficient_device, fill_value = "extrapolate")
        K_product=K_product*interp_func(freqs)
    if balanced:
        calibration_curve=(K_product**2*2*R_osc**2*(LO_power*1e-3))
    else:
        calibration_curve=(K_product**2*R_osc**2*(LO_power*1e-3))
    return calibration_curve



    

class Mode():
    def __init__(self,ind,freq,power=None,power_dynamics=None):
        self.ind=ind
        self.freq=freq
        
        self.life_spans=None
        
        self.birth_times=None
        self.death_times=None
        
        self.life_time=None
        self.max_power=power
        self.power_dynamics=None
        

        


class Spectrogram():
    def __init__(self,times=None,freqs=None,spec=None,params=None):

        
        self.freqs=freqs
        self.times=times
        self.spec=spec
        
        self.real_power_mode=False
        
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
                im=ax.pcolorfast(self.times*1e3,self.freqs/1e6,self.spec,cmap=cmap,vmin=vmin,vmax=vmax)
                if lang=='en':
                    plt.ylabel('Frequency detuning, MHz')
                    plt.xlabel('Time, ms')
                elif lang=='ru':
                    plt.ylabel('Отстройка, МГц')
                    plt.xlabel('Время, мс')
            elif formatter=='none':
                im=ax.pcolorfast(self.times,self.freqs,self.spec,cmap=cmap,vmin=vmin,vmax=vmax)
                ax.xaxis.set_major_formatter(formatter1)
                ax.yaxis.set_major_formatter(formatter1)
                
    
            if show_colorbar:
                cbar=plt.colorbar(im)
                if formatter=='sci':
                    cbar.ax.yaxis.set_major_formatter(formatter1)
                if lang=='ru':
                    if self.real_power_mode:
                        cbar.set_label('Спектральная мощность, Вт')
                    else:
                        cbar.set_label('Интенсивность, отн. ед.')
                elif lang=='en':
                    if self.real_power_mode:
                        cbar.set_label('Spectral power, W')
                    else:
                        cbar.set_label('Intensity, arb.u.')
                elif formatter=='none':
                    pass
            
        elif scale=='log':
            if formatter=='sci':
                im=ax.pcolorfast(self.times,self.freqs,10*np.log10(self.spec/1e-3),cmap=cmap,vmin=vmin,vmax=vmax)
                ax.xaxis.set_major_formatter(formatter1)
                ax.yaxis.set_major_formatter(formatter1)
                if lang=='en':
                    plt.ylabel('Frequency detuning, Hz')
                    plt.xlabel('Time, s')
                elif lang=='ru':
                    plt.ylabel('Отстройка, Гц')
                    plt.xlabel('Время, сек')
            elif formatter=='normal':
                im=ax.pcolorfast(self.times*1e3,self.freqs/1e6,10*np.log10(self.spec/1e-3),cmap=cmap,vmin=vmin,vmax=vmax)
                if lang=='en':
                    plt.ylabel('Frequency detuning, MHz')
                    plt.xlabel('Time, ms')
                elif lang=='ru':
                    plt.ylabel('Отстройка, МГц')
                    plt.xlabel('Время, мс')
                    
            elif formatter=='none':
                im=ax.pcolorfast(self.times,self.freqs,10*np.log10(self.spec/1e-3),cmap=cmap,vmin=vmin,vmax=vmax)
                ax.xaxis.set_major_formatter(formatter1)
                ax.yaxis.set_major_formatter(formatter1)
                    
                    
            if show_colorbar:
                cbar=plt.colorbar(im)
                if formatter=='sci':
                    cbar.ax.yaxis.set_major_formatter(formatter1)
                if lang=='ru':
                    if self.real_power_mode:
                        cbar.set_label('Интенсивность, дБм') 
                    else:
                        cbar.set_label('Интенсивность, дБ') 
                elif lang=='en':
                    if self.real_power_mode:
                        cbar.set_label('Intensity, dBm')
                        
                    else:
                        cbar.set_label('Intensity, dB')

            
        
            
            
            
        self.fig_spec=fig
        self.ax_spec=ax
        self.fig_format=formatter
        

            
        
        plt.title(title)
        plt.tight_layout()
        
        return fig,ax
        
    
    def plot_instant_spectrum(self,time:float,scale='log',**plot_params):
        ind=np.argmin(abs(self.times-time))
        fig=plt.figure()
        if self.real_power_mode:
            if scale=='lin':
                plt.plot(self.freqs,self.spec[:,ind],**plot_params)
                plt.ylabel('Spectral power, W')
            elif scale=='log':
                plt.plot(self.freqs,10*np.log10(self.spec[:,ind]/1e-3),**plot_params)
                plt.ylabel('Spectral power, dBm')
        else:
            if scale=='lin':
                plt.plot(self.freqs,self.spec[:,ind],**plot_params)
                plt.ylabel('Spectral power, arb.u.')
            elif scale=='log':
                plt.plot(self.freqs,10*np.log10(self.spec[:,ind]/1e-3),**plot_params)
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
        
        
    def find_modes(self,indicate_modes_on_spectrogram=False,prominance_factor=4,height=None,min_freq_spacing=1e5,rel_height=0.99,plot_shrinked_spectrum=False):
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
            power=signal_shrinked[p]
            self.modes.append(Mode(p,self.freqs[p],power=power))
            signal=self.spec[p,:]
            peak=np.nanargmax(signal)
            temp=scipy.signal.find_peaks(signal, height=None,prominence=prominance_factor*np.mean(signal))#distance=self.average_freq_window/(1/2/self.dt/len(self.freqs)))
            peak=temp[0]
            # peaks,_=scipy.signal.find_peaks(signal, height=3*bn.nanstd(signal),width=average_factor_for_times,prominence=3*np.nanstd(signal))
            try:
                widths,width_heights,left_ips, right_ips=scipy.signal.peak_widths(signal,peak,rel_height=rel_height)
                # print(self.times[int(left_ips)])
                
                indexes_sorted=np.argsort(left_ips)
                left_ips=left_ips[indexes_sorted]
                right_ips=right_ips[indexes_sorted]
                segments=[[left_ips[i],right_ips[i]] for i in range(len(left_ips))]
                '''
                remove intervals that are the same 
                '''
                # plt.figure()
                # y=0
                # for number,s in enumerate(segments):
                #     plt.plot([s[0],s[1]],[y,y],linewidth=4,label=number)
                #     y+=1
                # plt.legend()
                    
                
                def __remove_intesections(segments:list):
                    for i in np.arange(1,len(segments)):
                        if segments[i][0]<segments[i-1][1]:
                            if segments[i][1]>segments[i-1][1]:
                                segments[i-1][1]=segments[i][1]
                            
                            del segments[i]
                            # segments=np.delete(segments,i)
                            __remove_intesections(segments)
                            break
                    return segments
                
                segments=__remove_intesections(segments)    
                
                # plt.figure()
                # y=0
                # for number,s in enumerate(segments):
                #     plt.plot([s[0],s[1]],[y,y],linewidth=4,label=number)
                #     y+=1
                # plt.legend()
                    
                # indexes_to_delete=[]
                # for i in np.arange(1,len(left_ips)):
                #     if left_ips[i]<right_ips[i-1]:
                #         indexes_to_delete.append(i)
                # left_ips=np.delete(left_ips,indexes_to_delete)
                # right_ips=np.delete(right_ips,np.array(indexes_to_delete)-1)
                
                self.modes[mode_number].birth_times=np.array([self.times[np.int32(s[0])] for s in segments])
                self.modes[mode_number].death_times=np.array([self.times[np.int32(s[1])] for s in segments])
                
                self.modes[mode_number].life_spans=[[self.modes[mode_number].birth_times[i],self.modes[mode_number].death_times[i]] for i in range(len(self.modes[mode_number].birth_times))]
                
                
                # self.modes[mode_number].birth_times=self.times[np.int32(left_ips)]
                # self.modes[mode_number].death_times=self.times[np.int32(right_ips)]
                
                
                
                
                
            except RuntimeWarning:
                self.modes[mode_number].birth_times=[self.times[0]]
                self.modes[mode_number].death_times=[self.times[-1]]
            self.modes[mode_number].life_time=np.sum(self.modes[mode_number].death_times-self.modes[mode_number].birth_times)
      
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
        self.modes.sort(key=lambda x:-x.max_power)
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
            for j,_ in enumerate(self.modes[i].birth_times):
                plt.gca().axvspan(self.modes[i].birth_times[j], self.modes[i].death_times[j], alpha=0.1, color='green')
            # plt.axvline(self.modes[i].birth_time)
            # plt.axvline(self.modes[i].death_time)
            
    def print_all_modes(self):
        if self.N_modes>0:
            for i,_ in enumerate(self.modes):
                if self.real_power_mode:
                    print('Mode {}, detuning={:.0f} MHz, life time={:.2f} ms, max power={:.3e} W'.format(i,self.modes[i].freq/1e6,self.modes[i].life_time*1e3,self.modes[i].max_power))
                else:
                    print('Mode {}, detuning={:.0f} MHz, life time={:.2f} ms, max power={:.3e} arb.u.'.format(i,self.modes[i].freq/1e6,self.modes[i].life_time*1e3,self.modes[i].max_power))
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
    
    def _get_freq_index(self, freq):
        return np.argmin(abs(self.freqs-freq))
            
   
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
        return self.times,self.spec[freq_index,:]
    
    def plot_mode_dynamics(self,mode_number,NewFigure=True,show_lifespan=True):
        time,signal=self.get_mode_dynamics(mode_number)
        if NewFigure:
            fig=plt.figure()
        plt.plot(time,signal)
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        plt.xlabel('Time, s')      
        plt.ylabel('Intensity, W')
        plt.title('Mode at {:.1f} MHz detuning'.format(self.modes[mode_number].freq/1e6))
        if show_lifespan:
            for i,_ in enumerate(self.modes[mode_number].birth_times):
                plt.gca().axvspan(self.modes[mode_number].birth_times[i], self.modes[mode_number].death_times[i], alpha=0.1, color='green')
        plt.tight_layout()
        # plt.show()
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
    
    def get_mode_snaking(self):
        indexes_maxima=np.argmax(self.spec,axis=0)
        powers=self.spec[indexes_maxima,np.arange(self.spec.shape[1])]
        freqs=self.freqs[indexes_maxima]
        return self.times,freqs, powers
    
    
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
    i1=int(np.argwhere(t==mode.birth_times[0]))
    i2=int(np.argwhere(t==mode.death_times[0]))
    
    I1=spec1.spec[mode.ind,:]
    I2=spec2.spec[mode.ind,:]
    t,I1,I2=t[i1:i2],I1[i1:i2],I2[i1:i2]
    Ratio_dependence=I2/I1
    Ratio,Ratio_error=np.mean(Ratio_dependence),np.std(Ratio_dependence)/np.mean(Ratio_dependence)
    return (I1+I2),Ratio, Ratio_error,t,Ratio_dependence
        
if __name__=='__main__':
    
    
    win_time=1e-6
    IsAveraging=False
    # IsAveraging=True
    average_freq_window=10e6
    average_time_window=5e-6
    
    # file=r"\\?\F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\2023-2022 different fibers and different data\SMF-28 32 km\2023.04.03 Testing mode width at different wavelengths\raw data\wavelength=1550.35 pump=299 triggered=4 LO only 14 dBm.trace"
    # with open(file,'rb') as f:
    #     trace=pickle.load(f)
    # sp1=create_spectrogram_from_data(trace.data, trace.xinc,high_cut_off=700e6,win_time=win_time,
                                      # IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window,calibration_curve=None)
    
    
    '''
    '''
    # dt=1e-9
    # amplitude_trace=10*np.sin(2*np.pi*200e6*np.arange(0,0.1e-3,dt))
    # calibration_curve=None
    # sp1=create_spectrogram_from_data(amplitude_trace, dt,high_cut_off=210e6,low_cut_off=190e6,
    #                                  win_time=win_time,
    #                                  IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window,
    #                                  calibration_curve=calibration_curve)
    
    
    '''
    '''
    file=r"F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\2025.02 calibration of the system\test.trace_1350_1300"
    with open(file,'rb') as f:
        trace=pickle.load(f)
    LO_power=2 
    R_osc=50
    plt.figure()
    plt.plot(trace.data)
    calibration_curve=create_calibration_curve([r"F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\heterodyning\Hardware\calibrations\InGaAs_Balanced_Photorecelver_PNKY_BPRM_20G_I_FA_SN221731255.txt",
                                                r"F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\heterodyning\Hardware\calibrations\Rigol MSO8104 50 Om.txt"], LO_power, R_osc, trace.xinc, win_time)
    sp1=create_spectrogram_from_data(trace.data, trace.xinc,high_cut_off=9000e6,win_time=win_time,
                                           IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                           calibration_curve=calibration_curve)
    
  
    '''
    '''
    
    
    
    sp1.plot_spectrogram()
    sp1.find_modes()
    sp1.print_all_modes()
    sp1.plot_instant_spectrum(0,scale='log')
    
    
    
    # win_time=4e-6
    # # IsAveraging=False
    # IsAveraging=True
    # average_freq_window=5e6
    # average_time_window=5e-6
    
    # file2=r"F:\Equipment\2023.09.07 testing heterodyning signal for diff freqs\example 3mW.trace"
    # with open(file2,'rb') as f:
    #     trace2=pickle.load(f)
    # sp2=create_spectrogram_from_data(trace2.data, trace2.xinc,high_cut_off=700e6,win_time=win_time,
    #                                  IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window)
    # sp2.plot_spectrogram()
    # sp2.find_modes()
    # sp2.print_all_modes()
    
    
    # file2=r"F:\Equipment\2023.09.07 testing heterodyning signal for diff freqs\example 2mW.trace"
    # with open(file2,'rb') as f:
    #     trace2=pickle.load(f)
    # sp2=create_spectrogram_from_data(trace2.data, trace2.xinc,high_cut_off=700e6,win_time=win_time,
    #                                  IsAveraging=IsAveraging,average_freq_window=average_freq_window,average_time_window=average_time_window)
    # sp2.plot_spectrogram()
    # sp2.find_modes()
    # sp2.print_all_modes()