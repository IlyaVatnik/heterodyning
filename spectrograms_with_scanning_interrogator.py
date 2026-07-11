# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 19:27:44 2026

@author: Илья
"""

import pickle
import numpy as np
from scipy.signal import hilbert, butter, sosfiltfilt, find_peaks
from scipy.ndimage import gaussian_filter1d
import scipy.signal
import scipy.fft as fft 
# from scipy.interpolate import interp1d
import bottleneck as bn

from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib.ticker import EngFormatter
formatter1 = EngFormatter()
import matplotlib


__date__='2026.06.19'
__version__='1.1'

current_dir = Path(__file__).resolve()
STRFRWD_STEP_SIGNAL_FILE = current_dir.parent / 'Hardware' / 'calibrations'/ 'Interrogator measurement signal' / 'strfrwd_step_signal_oscillogram.pkl'
BALANCE_SCHEME_STEP_SIGNAL_FILE = current_dir.parent / 'Hardware' / 'calibrations'/ 'Interrogator measurement signal' / 'balance_scheme_step_signal_oscillogram.pkl'



class TraceAnalyzer2D:
    def __init__(self, 
                 sweep_period=0.50000305e-3,
                 sweep_speed=9.73e4,
                 sweep_accel=6.4e6,
                 sleep_time=0.0000961,
                 start_wavelength=1528,
                 stop_wavelength=1568,
                 wavelength_step=0.001,
                 balanced_measurement_scheme=True,
                 trigger_by='balanced_channel',
                 calibration_factor=1/20):
        '''
        balanced_measurement_scheme=True -  используется балансный фотодетектор, запуск по второму каналу, который измеряет мощность с интеррогатора, которая имеет скачок, запускающий триггер
        '''
        
        
        self.sweep_period = sweep_period
        self.sweep_speed = sweep_speed
        self.sweep_accel = sweep_accel
        
        self.interrogator_start_wavelength=1528
        self.start_wavelength=start_wavelength
        self.stop_wavelength=stop_wavelength
        self.sleep_time=sleep_time
        self.wavelength_step=wavelength_step
        self.wavelength_resolution=0.02
        self.balanced_measurement_scheme=balanced_measurement_scheme
        self.calibration_factor=calibration_factor
        if trigger_by=='balanced_channel':
            self.step_signal_filepath=BALANCE_SCHEME_STEP_SIGNAL_FILE    
        elif trigger_by=='ax_channel':
            self.step_signal_filepath=STRFRWD_STEP_SIGNAL_FILE
        
        if self.calibration_factor!=None:
            self.real_power_mode=True
        else:
            self.real_power_mode=False
        
        
        self.fig_spec=None
        self.ax_spec=None
        self.fig_format=None
        
        self.modes=None
        self.N_modes=0
        
        self.filepath=None
        
        
    
        with open(self.step_signal_filepath, 'rb') as f:
            t_tpl , y_tpl = pickle.load(f)
            self.t_tpl = np.asarray(t_tpl, dtype=float)
            y_tpl = np.asarray(y_tpl, dtype=float)

            self.y_tpl0 = y_tpl - np.mean(y_tpl)
            self.tpl_norm = np.linalg.norm(self.y_tpl0)
        
  

    def load_and_process(self,filepath): 
    
        self.filepath=filepath
        with open(filepath, 'rb') as f:
            raw_signal, xinc, xorigin = pickle.load(f)
            
        self.process(raw_signal, xinc,xorigin)
        
        

    
    def process(self,raw_signal, xinc,xorigin,start_time=None):
        

        
        if len(raw_signal)*xinc>self.sweep_period:

            raw_times=xorigin+np.arange(len(raw_signal))*xinc
        # print('start detecting jump')
        
            
            if start_time==None:
                detect_jump_results=detect_jump_by_template(raw_times, raw_signal, self.t_tpl, self.y_tpl0,self.tpl_norm,searching_time=self.sweep_period*1.3)
            # print('jump detected')
            
                self.start_time=detect_jump_results['jump_time']
            else:
                self.start_time=start_time
            # else:
                # start_time=xorigin//self.sweep_period
            ind_global_start=int((self.start_time-xorigin)/xinc)
            
            self.N_periods=int(np.floor((raw_times[-1]-self.start_time)/self.sweep_period))
            
            self.sampling_rate=1/xinc
            
            # highpass_cutoff_hz=50e3
            # nyq = 0.5 * self.sampling_rate
            # normal_cutoff = highpass_cutoff_hz / nyq
            
            array=np.arange(int((self.sweep_period-self.sleep_time)/xinc))
            init_wavelengths=array*self.sweep_speed*xinc+(array*xinc)**2*self.sweep_accel +self.interrogator_start_wavelength
            
            # init_wavelengths_test=array*self.sweep_speed*xinc+self.start_wavelength
            # plt.figure()
            # plt.plot(array,init_wavelengths)
            # plt.plot(array,init_wavelengths_test)
            
            self.N_points_in_period=len(init_wavelengths)
            # self.stop_wavelength=np.max(init_wavelengths)
            self.wavelengths=np.arange(self.start_wavelength,self.stop_wavelength,self.wavelength_step)
            self.N_wavelengths=len(self.wavelengths)
           
            
            self.times=np.arange(self.N_periods)*self.sweep_period
            
            self.intensity_2d=np.zeros((self.N_wavelengths,self.N_periods))
            
            for ii in range(self.N_periods):
                # print(f'Step {ii} of {self.N_periods}')
                ind_period_start=ind_global_start+int((ii*self.sweep_period+self.sleep_time)/xinc)
                ind_period_stop=ind_period_start+self.N_points_in_period
                
                fragment=raw_signal[ind_period_start:ind_period_stop]
                # sos = butter(N=4, Wn=normal_cutoff, btype='highpass', output='sos')
                # filtered_fragment = sosfiltfilt(sos, fragment)
                
                analytic_signal = hilbert(fragment)
                raw_envelope = np.abs(analytic_signal)**2
                # self.intensity_2d[:,ii]=np.interp(self.wavelengths,init_wavelengths,gaussian_filter1d(raw_envelope, sigma=5))
                envelope=moving_average(raw_envelope, int(self.wavelength_resolution/(self.sweep_speed*xinc)))
  
                self.intensity_2d[:,ii]=np.interp(self.wavelengths,init_wavelengths,envelope)
                
        else:
            # короткий трейс: меньше одного периода
            if start_time is None and not hasattr(self, 'start_time'):
                print('Error. Start time not specified and trace is shorter then sweep period')
                return

            if start_time is not None:
                self.start_time = start_time

            self.sampling_rate = 1/xinc

            ind_global_start = int((self.start_time - xorigin) / xinc)

            # старт внутри массива (обрезаем если <0)
            ind_start = ind_global_start + int(self.sleep_time / xinc)
            
            # если старт до начала сигнала — сдвигаем
            shift_points = 0
            if ind_start < 0:
                shift_points = -ind_start
                ind_start = 0
            
            if ind_start >= len(raw_signal):
                print('Error: start is outside the signal')
                return
            
            max_available_points = len(raw_signal) - ind_start
            
            # сколько реально используем
            N = max_available_points
            
            # локальное "время внутри свипа" С УЧЁТОМ СДВИГА
            array = np.arange(N) + shift_points
            times_local = array * xinc
            
            init_wavelengths = (
                times_local * self.sweep_speed
                + (times_local ** 2) * self.sweep_accel
                + self.interrogator_start_wavelength
            )

            self.N_points_in_period = len(init_wavelengths)

            # формируем сетку длин волн (только доступный кусок!)
            wl_min = max(self.start_wavelength, np.min(init_wavelengths))
            wl_max = min(self.stop_wavelength, np.max(init_wavelengths))

            if wl_max <= wl_min:
                print('Error: no wavelength overlap in short trace')
                return

            self.wavelengths = np.arange(wl_min, wl_max, self.wavelength_step)
            self.N_wavelengths = len(self.wavelengths)

            self.times = np.array([0.0])  # один "кадр"

            self.intensity_2d = np.zeros((self.N_wavelengths, 1))

            fragment = raw_signal[ind_start:ind_start + self.N_points_in_period]

            analytic_signal = hilbert(fragment)
            raw_envelope = np.abs(analytic_signal) ** 2

            window = int(self.wavelength_resolution / (self.sweep_speed * xinc))
            window = max(window, 1)

            envelope = moving_average(raw_envelope, window)

            # self.intensity_2d[:, 0] = np.interp(
            #     self.wavelengths,
            #     init_wavelengths,
            #     envelope
            # )
            
            min_len = min(len(init_wavelengths), len(envelope))

            init_wavelengths_cut = init_wavelengths[:min_len]
            envelope_cut = envelope[:min_len]
            
            self.intensity_2d[:, 0] = np.interp(
                self.wavelengths,
                init_wavelengths_cut,
                envelope_cut
            )
            
        
        if self.calibration_factor!=None:
            self.intensity_2d*=self.calibration_factor/0.04*self.wavelength_resolution
        return self.times,self.wavelengths,self.intensity_2d
        




    def plot_signal_vs_time(self, mode='raw', t_start=None, t_end=None,find_start=False):
        """
        1. Отрисовка непрерывного 1D сигнала от абсолютного времени эксперимента.
        :param mode: 'envelope' (огибающая биений) или 'raw' (сырой сигнал с осциллографа)
        :param t_start: Начало окна отрисовки в секундах (опционально)
        :param t_end: Конец окна отрисовки в секундах (опционально)
        """
        if self.filepath!=None:
            plt.figure(figsize=(12, 4))
            with open(self.filepath, 'rb') as f:
                raw_signal, xinc, xorigin = pickle.load(f)
            
            total_samples = len(raw_signal)
            continuous_time=xorigin+np.arange(len(raw_signal))*xinc
            
            if mode == 'envelope':
                signal = self.intensity_2d.flatten()
                ylabel = 'Интенсивность огибающей (у.е.)'
            elif mode == 'raw':
                signal = raw_signal
                ylabel = 'Сырой сигнал (В)'
            else:
                raise ValueError("Параметр mode должен быть 'envelope' или 'raw'")

        # Обрезка по времени, если заданы t_start и t_end
        # mask = np.ones(total_samples, dtype=bool)
        # if t_start is not None:
        #     mask &= (continuous_time >= t_start)
        # if t_end is not None:
        #     mask &= (continuous_time <= t_end)
            
        # plt.plot(continuous_time[mask], signal[mask], color='blue' if mode=='envelope' else 'gray', linewidth=0.8)
            plt.plot(continuous_time, signal, color='blue' if mode=='envelope' else 'gray', linewidth=0.8)
            if find_start:
                ind=int((self.sweep_period*1.3)/xinc)
                with open(self.step_signal_filepath, 'rb') as f:
                    t_tpl , y_tpl = pickle.load(f)
                detect_jump_results=detect_jump_by_template(continuous_time[:ind], raw_signal[:ind], self.t_tpl, self.y_tpl0,self.tpl_norm,searching_time=self.sweep_period*1.3)
                start_time=detect_jump_results['jump_time']
            plt.axvline(start_time,linestyle='--',color='red')
            
            plt.xlabel('Абсолютное время (с)')
            plt.ylabel(ylabel)
            plt.title(f'Полный временной трейс ({mode})')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            print(len(raw_signal))
        
        
        
    def plot_spectrogram(self,figsize=(8,6),font_size=11,title='',
                         vmin=None,vmax=None,cmap='jet',lang='en',
                         formatter='sci',scale='lin',
                         show_colorbar=True,
                         start_wavelength=None,
                         stop_wavelength=None):
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
                im=ax.pcolorfast(self.times,self.wavelengths,self.intensity_2d,cmap=cmap,vmin=vmin,vmax=vmax)
                ax.xaxis.set_major_formatter(formatter1)
                # ax.yaxis.set_major_formatter(formatter1)
                if lang=='en':
                    plt.ylabel('Wavelength, nm')
                    plt.xlabel('Time, s')
                elif lang=='ru':
                    plt.ylabel('Длина волны, нм')
                    plt.xlabel('Время, сек')
            elif formatter=='normal':
                im=ax.pcolorfast(self.times*1e3,self.wavelengths,self.intensity_2d,cmap=cmap,vmin=vmin,vmax=vmax)
                if lang=='en':
                    plt.ylabel('Wavelength, nm')
                    plt.xlabel('Time, ms')
                elif lang=='ru':
                    plt.ylabel('Длина волны, нм')
                    plt.xlabel('Время, мс')
            elif formatter=='none':
                im=ax.pcolorfast(self.times,self.wavelengths,self.intensity_2d,cmap=cmap,vmin=vmin,vmax=vmax)
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
                im=ax.pcolorfast(self.times,self.wavelengths,10*np.log10(self.intensity_2d/1e-3),cmap=cmap,vmin=vmin,vmax=vmax)
                ax.xaxis.set_major_formatter(formatter1)
                # ax.yaxis.set_major_formatter(formatter1)
                if lang=='en':
                    plt.ylabel('Wavelength, nm')
                    plt.xlabel('Time, s')
                elif lang=='ru':
                    plt.ylabel('Длина волны, нм')
                    plt.xlabel('Время, сек')
            elif formatter=='normal':
                im=ax.pcolorfast(self.times*1e3,self.wavelengths,10*np.log10(self.intensity_2d/1e-3),cmap=cmap,vmin=vmin,vmax=vmax)
                if lang=='en':
                    plt.ylabel('Wavelength, nm')
                    plt.xlabel('Time, ms')
                elif lang=='ru':
                    plt.ylabel('Длина волны, нм')
                    plt.xlabel('Время, мс')
                    
            elif formatter=='none':
                im=ax.pcolorfast(self.times,self.wavelengths,10*np.log10(self.intensity_2d/1e-3),cmap=cmap,vmin=vmin,vmax=vmax)
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
        if stop_wavelength!=None:
            plt.ylim(top=stop_wavelength)
        else:
            plt.ylim(top=self.stop_wavelength)
        if start_wavelength!=None:
            plt.ylim(bottom=start_wavelength)
        else:
            plt.ylim(bottom=self.start_wavelength)
        
        return fig,ax
                
    
    def get_instant_spectrum(self,time:float):
        ind=np.argmin(abs(self.times-time))
        return self.wavelengths, self.intensity_2d[:,ind]
    
    
    def plot_instant_spectrum(self,time:float,scale='log',**plot_params):
        waves,signal=self.get_instant_spectrum(time)
        fig=plt.figure()
        if self.real_power_mode:
            if scale=='lin':
                plt.plot(waves,signal,**plot_params)
                plt.ylabel('Spectral power, W')
            elif scale=='log':
                plt.plot(waves,10*np.log10(signal/1e-3),**plot_params)
                plt.ylabel('Spectral power, dBm')
        else:
            if scale=='lin':
                plt.plot(waves,signal,**plot_params)
                plt.ylabel('Spectral power, arb.u.')
            elif scale=='log':
                plt.plot(waves,10*np.log10(signal/1e-3),**plot_params)
                plt.ylabel('Spectral power, dB')
        # plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        
        plt.xlabel('Wavelength, nm')
        return fig
        
    def get_average_spectrum(self,start_time,stop_time):
        ind_start=np.argmin(abs(self.times-start_time))
        ind_stop=np.argmin(abs(self.times-stop_time))
        return self.wavelengths, np.mean(self.intensity_2d[:,ind_start:ind_stop],axis=1)
    
    def plot_average_spectrum(self,start_time,stop_time, scale='log',**plot_params):
        waves,signal=self.get_average_spectrum(start_time,stop_time)
        fig=plt.figure()
        if self.real_power_mode:
            if scale=='lin':
                plt.plot(waves,signal,**plot_params)
                plt.ylabel('Spectral power, W')
            elif scale=='log':
                plt.plot(waves,10*np.log10(signal/1e-3),**plot_params)
                plt.ylabel('Spectral power, dBm')
        else:
            if scale=='lin':
                plt.plot(waves,signal,**plot_params)
                plt.ylabel('Spectral power, arb.u.')
            elif scale=='log':
                plt.plot(waves,10*np.log10(signal/1e-3),**plot_params)
                plt.ylabel('Spectral power, dB')
        # plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        
        plt.xlabel('Wavelength, nm')
        return fig
    
       
    def find_modes(self,indicate_modes_on_spectrogram=False,prominance_factor=1,height=None,min_wavelength_spacing=0.05,rel_height=0.2,plot_shrinked_spectrum=False):
        self.modes=[]
        signal_shrinked=np.nanmax(self.intensity_2d,axis=1)
        dv=self.wavelengths[1]-self.wavelengths[0]
        mode_indexes,_=scipy.signal.find_peaks(signal_shrinked, height=height,distance=int(min_wavelength_spacing/dv)+1,prominence=prominance_factor*bn.nanstd(signal_shrinked))#distance=self.average_freq_window/(1/2/self.dt/len(self.wavelengths)))
        if plot_shrinked_spectrum:
            plt.figure()
            plt.title('Shrinked spectrum')
            plt.plot(self.wavelengths,signal_shrinked)
            plt.plot(self.wavelengths[mode_indexes],signal_shrinked[mode_indexes],'o')
        for mode_number,p in enumerate(mode_indexes):
            power=signal_shrinked[p]
            self.modes.append(Mode(p,self.wavelengths[p],power=power))
            signal=self.intensity_2d[p,:]
            # peak=np.nanargmax(signal)
            # temp=scipy.signal.find_peaks(signal, height=None,prominence=prominance_factor*np.mean(signal))#distance=self.average_freq_window/(1/2/self.dt/len(self.wavelengths)))
            # peak=temp[0]
            peaks,_=scipy.signal.find_peaks(signal, height=bn.nanstd(signal),prominence=np.nanstd(signal))
            if len(peaks)!=0:
                try:
                    widths,width_heights,left_ips, right_ips=scipy.signal.peak_widths(signal,peaks,rel_height=rel_height)
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
                except RuntimeWarning as e:
                    print(e, '; error while calculating mode life times')
                    self.modes[mode_number].birth_times=np.array([self.times[0]])
                    self.modes[mode_number].death_times=np.array([self.times[-1]])
                
            else:
                self.modes[mode_number].birth_times=np.array([self.times[0]])
                self.modes[mode_number].death_times=np.array([self.times[-1]])
            
            self.modes[mode_number].life_time=np.sum(self.modes[mode_number].death_times-self.modes[mode_number].birth_times)
      
        if self.fig_spec is not None and indicate_modes_on_spectrogram:
            if self.fig_format=='normal':
                extraticks=[x.wavelength/1e6 for x in self.modes]
            elif self.fig_format=='sci':
                extraticks=[x.wavelength for x in self.modes]
            loc=matplotlib.ticker.FixedLocator(extraticks)
            self.fig_spec.axes[0].yaxis.set_minor_locator(loc)
            self.fig_spec.axes[0].tick_params(which='minor', length=10, color='r',width=5)
            for i,m in enumerate(self.modes):
                plt.text(self.times[0]*0.9,m.wavelength,i,color='r')
            # plt.yticks(minor=True)
            # self.fig_spec.axes[0].axhline(self.wavelengths,color='yellow',linewidth=2)
            
        self.N_modes=len(self.modes)
        self.modes.sort(key=lambda x:-x.max_power)
        return self.modes
    
    def print_all_modes(self):
        if self.N_modes is None:
            self.find_modes()
        if self.N_modes>0:
            for i,_ in enumerate(self.modes):
                if self.real_power_mode:
                    print('Mode {}, Wavelength={:.3f} nm, life time={:.2f} ms, max power={:.3e} W'.format(i,self.modes[i].wavelength,self.modes[i].life_time*1e3,self.modes[i].max_power))
                else:
                    print('Mode {}, Wavelength={:.3f} nm, life time={:.2f} ms, max power={:.3e} arb.u.'.format(i,self.modes[i].wavelength,self.modes[i].life_time*1e3,self.modes[i].max_power))
        else:
            print('No mode found on spectrogram')
            
    def create_params(self):
        self.params={}
        self.params['balanced_measurement_scheme']=self.balanced_measurement_scheme
        self.params['calibration_factor']=self.calibration_factor
        
    def save_to_file(self,file,as_object=False):
        self.create_params()
        with open(file, 'wb') as f:
            if as_object:
                pickle.dump(self,f)
            else:
                pickle.dump([self.times,self.wavelengths,self.intensity_2d,self.params],f)
                
    def load_from_file(self,file,as_object=False):
        with open(file, 'rb') as f:
            obj=pickle.load(f)

        self.times,self.wavelengths, self.intensity_2d,self.params=obj
            
    def get_dynamics_at_wavelength(self,wavelength):
        wave_index=np.argmin(abs((self.wavelengths-wavelength)))
        return self.times,self.intensity_2d[wave_index,:]
        
 
    def plot_dynamics_at_wavelengths(self,wavelength,NewFigure=True):
        time,signal=self.get_dynamics_at_wavelength(wavelength)
        if NewFigure:
            fig=plt.figure()
        plt.plot(time,signal)
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.gca().yaxis.set_major_formatter(formatter1)
        plt.xlabel('Time, s')      
        plt.ylabel('Intensity, W')
        plt.title('Mode at {:.2f} nm'.format(wavelength))

        plt.tight_layout()
        # plt.show()
        return fig, plt.gca()
    
    

class Mode():
    def __init__(self,ind,wavelength,power=None,power_dynamics=None):
        self.ind=ind
        self.wavelength=wavelength
        
        self.life_spans=None
        
        self.birth_times=None
        self.death_times=None
        
        self.life_time=None
        self.max_power=power
        self.power_dynamics=None      


def _prepare_template(t_tpl, y_tpl):
    # Нормализация шаблона для корреляции
    y0 = y_tpl - np.mean(y_tpl)
    norm = np.linalg.norm(y0)
    if norm == 0:
        raise ValueError("шаблон имеет нулевую вариацию")

    return t_tpl, y_tpl, y0, norm





def _normalized_corr(a, b):
    """
    Нормированная корреляция двух векторов одинаковой длины.
    Инвариантна к смещению уровня и масштабу.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    a0 = a - np.mean(a)
    b0 = b - np.mean(b)

    na = np.linalg.norm(a0)
    nb = np.linalg.norm(b0)

    if na == 0 or nb == 0:
        return 0.0

    return float(np.dot(a0, b0) / (na * nb))


def detect_jump_by_template(
    t_sig,
    y_sig,
    t_tpl,
    y_tpl0,
    tpl_norm,
    searching_time,
    search_times=None,
    threshold=None,
    return_curve=True,
):
    """
Ищет время скачка в сигнале по шаблону.

Параметры
---------
t_sig, y_sig : массивы сигнала
t_tpl, y_tpl0, tpl_norm : массивы шаблона
    В шаблоне момент скачка должен соответствовать t=0.
    t_tpl может содержать отрицательные и положительные времена.
search_times : массив candidate-времен tau, optional
    Если None, используется t_sig в допустимом диапазоне.
threshold : float, optional
    Если задан, то будет флаг found = score >= threshold.
return_curve : bool
    Возвращать ли всю кривую корреляции.

Возвращает
----------
result : dict
    {
        "jump_time": оценка времени скачка,
        "score": максимум корреляции,
        "found": True/False/None,
        "corr_times": времена tau,
        "corr_values": значения корреляции,
        "matched_signal": интерполированный кусок сигнала в точках jump_time + t_tpl
    }
"""
    xinc = t_sig[1] - t_sig[0]
    ind = int(searching_time / xinc)

    y_sig = y_sig[:ind]
    t0 = t_sig[0]

    # переводим t_tpl -> сдвиги в индексах
    tpl_idx = np.round((t_tpl - t_tpl[0]) / xinc).astype(int)
    tpl_len = tpl_idx[-1] + 1

    sig_len = len(y_sig)

    # допустимые позиции (в индексах)
    max_start = sig_len - tpl_len
    if max_start <= 0:
        raise ValueError("шаблон длиннее сигнала")

    if search_times is None:
        taus_idx = np.arange(0, max_start)
        taus = t0 + taus_idx * xinc
    else:
        taus = np.asarray(search_times, dtype=float)
        taus_idx = np.round((taus - t0) / xinc).astype(int)
        mask = (taus_idx >= 0) & (taus_idx <= max_start)
        taus_idx = taus_idx[mask]
        taus = taus[mask]

        if len(taus) == 0:
            raise ValueError("в search_times нет допустимых значений")

    corr_values = np.empty(len(taus_idx), dtype=float)

    for i, start in enumerate(taus_idx):
        y_win = y_sig[start + tpl_idx]

        y_win0 = y_win - np.mean(y_win)
        win_norm = np.linalg.norm(y_win0)

        if win_norm == 0:
            corr_values[i] = 0.0
        else:
            corr_values[i] = np.dot(y_win0, y_tpl0) / (win_norm * tpl_norm)

    best_idx = int(np.argmax(corr_values))
    jump_time = float(taus[best_idx])-t_tpl[0]
    score = float(corr_values[best_idx])

    best_start = taus_idx[best_idx]
    matched_signal = y_sig[best_start + tpl_idx]

    if threshold is None:
        found = None
    else:
        found = bool(score >= threshold)

    result = {
        "jump_time": jump_time,
        "score": score,
        "found": found,
        "matched_signal": matched_signal,
    }

    if return_curve:
        result["corr_times"] = taus
        result["corr_values"] = corr_values

    return result

def moving_average(signal, window):
    signal = np.asarray(signal, dtype=float)
    
    pad_left = window // 2
    pad_right = window - 1 - pad_left
    
    # отражение на краях (лучше, чем нули)
    padded = np.pad(signal, (pad_left, pad_right), mode='edge')
    
    cumsum = np.cumsum(padded)
    cumsum[window:] -= cumsum[:-window]
    
    return cumsum[window - 1:] / window