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

current_dir = Path(__file__).resolve().parent
STEP_SIGNAL_FILE = current_dir.parent / "Hardware" / "F:/Ilya/heterodyning/Hardware/step_signal_oscillogram.pkl"



class TraceAnalyzer2D:
    def __init__(self, filepath, 
                 sweep_period=0.5e-3,
                 sweep_speed=8e4,
                 initial_wavelength=1528,
                 sleep_time=0.00011,
                 step_signal_filepath=STEP_SIGNAL_FILE):
        self.filepath = filepath
        self.step_signal_filepath=step_signal_filepath
        self.sweep_period = sweep_period
        self.sweep_speed = sweep_speed
        self.initial_wavelength=initial_wavelength
        self.sleep_time=sleep_time
        
        self.real_power_mode=False
        
        self.fig_spec=None
        self.ax_spec=None
        self.fig_format=None
        
        self.modes=None
        self.N_modes=0
        

    def load_and_process(self): # Снизили до 15 кГц!
    

        with open(self.filepath, 'rb') as f:
            raw_signal, xinc, xorigin = pickle.load(f)
        with open(self.step_signal_filepath, 'rb') as f:
            t_tpl , y_tpl = pickle.load(f)
            
        raw_times=xorigin+np.arange(len(raw_signal))*xinc
        ind=int((self.sweep_period*1.3)/xinc)

        
        detect_jump_results=detect_jump_by_template(raw_times[:ind], raw_signal[:ind], t_tpl, y_tpl)
        start_time=detect_jump_results['jump_time']
        ind_global_start=int((start_time-xorigin)/xinc)
        
        self.N_periods=int(np.floor(raw_times[-1]/self.sweep_period))
        self.N_points_in_period=int(self.sweep_period / xinc)
        self.sampling_rate=1/xinc
        
        highpass_cutoff_hz=50e3
        nyq = 0.5 * self.sampling_rate
        normal_cutoff = highpass_cutoff_hz / nyq
        
        
        
        self.intensity_2d=np.zeros((self.N_points_in_period,self.N_periods))
        
        for ii in range(self.N_periods):
            ind_period_start=ind_global_start+int((ii*self.sweep_period+self.sleep_time)/xinc)
            ind_period_stop=ind_period_start+self.N_points_in_period
            
            fragment=raw_signal[ind_period_start:ind_period_stop]
            sos = butter(N=4, Wn=normal_cutoff, btype='highpass', output='sos')
            filtered_fragment = sosfiltfilt(sos, fragment)
            
            analytic_signal = hilbert(filtered_fragment)
            raw_envelope = np.abs(analytic_signal)**2
            self.intensity_2d[:,ii]=gaussian_filter1d(raw_envelope, sigma=5)
            
        self.times=np.arange(self.N_periods)*self.sweep_period
        self.wavelengths=np.arange(self.N_points_in_period)*xinc*self.sweep_speed+self.initial_wavelength
        
        return self.times,self.wavelengths,self.intensity_2d
        
 
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
        
        return fig,ax
                
    
    def plot_instant_spectrum(self,time:float,scale='log',**plot_params):
        ind=np.argmin(abs(self.times-time))
        fig=plt.figure()
        if self.real_power_mode:
            if scale=='lin':
                plt.plot(self.wavelengths,self.intensity_2d[:,ind],**plot_params)
                plt.ylabel('Spectral power, W')
            elif scale=='log':
                plt.plot(self.wavelengths,10*np.log10(self.intensity_2d[:,ind]/1e-3),**plot_params)
                plt.ylabel('Spectral power, dBm')
        else:
            if scale=='lin':
                plt.plot(self.wavelengths,self.intensity_2d[:,ind],**plot_params)
                plt.ylabel('Spectral power, arb.u.')
            elif scale=='log':
                plt.plot(self.wavelengths,10*np.log10(self.intensity_2d[:,ind]/1e-3),**plot_params)
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
        if not self.N_modes:
            self.find_modes()
        if self.N_modes>0:
            for i,_ in enumerate(self.modes):
                if self.real_power_mode:
                    print('Mode {}, Wavelength={:.3f} nm, life time={:.2f} ms, max power={:.3e} W'.format(i,self.modes[i].wavelength,self.modes[i].life_time*1e3,self.modes[i].max_power))
                else:
                    print('Mode {}, Wavelength={:.3f} nm, life time={:.2f} ms, max power={:.3e} arb.u.'.format(i,self.modes[i].wavelength,self.modes[i].life_time*1e3,self.modes[i].max_power))
        else:
            print('No mode found on spectrogram')

    

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
    t_tpl = np.asarray(t_tpl, dtype=float)
    y_tpl = np.asarray(y_tpl, dtype=float)

    if t_tpl.ndim != 1 or y_tpl.ndim != 1:
        raise ValueError("t_tpl и y_tpl должны быть одномерными массивами")
    if len(t_tpl) != len(y_tpl):
        raise ValueError("t_tpl и y_tpl должны быть одной длины")
    if len(t_tpl) < 2:
        raise ValueError("шаблон слишком короткий")

    order = np.argsort(t_tpl)
    t_tpl = t_tpl[order]
    y_tpl = y_tpl[order]

    if not np.all(np.diff(t_tpl) > 0):
        raise ValueError("времена шаблона должны строго возрастать")

    # Нормализация шаблона для корреляции
    y0 = y_tpl - np.mean(y_tpl)
    norm = np.linalg.norm(y0)
    if norm == 0:
        raise ValueError("шаблон имеет нулевую вариацию")

    return t_tpl, y_tpl, y0, norm


def _prepare_signal(t_sig, y_sig):
    t_sig = np.asarray(t_sig, dtype=float)
    y_sig = np.asarray(y_sig, dtype=float)

    if t_sig.ndim != 1 or y_sig.ndim != 1:
        raise ValueError("t_sig и y_sig должны быть одномерными массивами")
    if len(t_sig) != len(y_sig):
        raise ValueError("t_sig и y_sig должны быть одной длины")
    if len(t_sig) < 2:
        raise ValueError("сигнал слишком короткий")

    order = np.argsort(t_sig)
    t_sig = t_sig[order]
    y_sig = y_sig[order]

    if not np.all(np.diff(t_sig) > 0):
        raise ValueError("времена сигнала должны строго возрастать")

    return t_sig, y_sig


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
    y_tpl,
    search_times=None,
    threshold=None,
    return_curve=True,
):
    """
    Ищет время скачка в сигнале по шаблону.

    Параметры
    ---------
    t_sig, y_sig : массивы сигнала
    t_tpl, y_tpl : массивы шаблона
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
    t_sig, y_sig = _prepare_signal(t_sig, y_sig)
    t_tpl, y_tpl, y_tpl0, tpl_norm = _prepare_template(t_tpl, y_tpl)

    tpl_t_min = t_tpl[0]
    tpl_t_max = t_tpl[-1]

    # Допустимые tau: чтобы точки tau + t_tpl лежали внутри диапазона сигнала
    tau_min = t_sig[0] - tpl_t_min
    tau_max = t_sig[-1] - tpl_t_max

    if tau_min > tau_max:
        raise ValueError("шаблон по времени не помещается в сигнал")

    if search_times is None:
        mask = (t_sig >= tau_min) & (t_sig <= tau_max)
        taus = t_sig[mask]
        if len(taus) == 0:
            # Если в t_sig нет точек в допустимом диапазоне, строим свою сетку
            taus = np.linspace(tau_min, tau_max, 500)
    else:
        taus = np.asarray(search_times, dtype=float)
        taus = taus[(taus >= tau_min) & (taus <= tau_max)]
        if len(taus) == 0:
            raise ValueError("в search_times нет допустимых значений")

    corr_values = np.empty(len(taus), dtype=float)

    for i, tau in enumerate(taus):
        sample_times = tau + t_tpl
        y_win = np.interp(sample_times, t_sig, y_sig)

        y_win0 = y_win - np.mean(y_win)
        win_norm = np.linalg.norm(y_win0)

        if win_norm == 0:
            corr_values[i] = 0.0
        else:
            corr_values[i] = np.dot(y_win0, y_tpl0) / (win_norm * tpl_norm)

    best_idx = int(np.argmax(corr_values))
    jump_time = float(taus[best_idx])
    score = float(corr_values[best_idx])

    matched_signal = np.interp(jump_time + t_tpl, t_sig, y_sig)

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
