#%%
import numpy as np
import os
import matplotlib.pyplot as plt
import pickle
import scipy.signal as signal
import heterodyning
from heterodyning.spectrograms import create_spectrogram_from_data
from matplotlib.ticker import EngFormatter
formatter1 = EngFormatter(places=2)

__version__='0.2'
__date__='09.12.2024'

stokes_detuning=10.826e9
LIGHT_SPEED=299792458
#%%

def get_detuning_of_two_LO(wavelengths,spectrum):
    '''
    wavelengths - in nm
    
    return detuning between two lasers in Hz
    '''
    peaks=signal.find_peaks(spectrum,prominence=10)
    peak1,peak2=peaks[0][0],peaks[0][1]
    detuning_freqs=LIGHT_SPEED*(1/wavelengths[peak1]-1/wavelengths[peak2])*1e9
    return detuning_freqs

def error_of_stokes_freqs(freq1,freq2,detuning,stokes_number):

    error=min(abs(freq1+freq2+detuning-stokes_detuning*stokes_number),
              abs(-freq1+freq2+detuning-stokes_detuning*stokes_number),
              abs(freq1-freq2+detuning-stokes_detuning*stokes_number),
              abs(-freq1-freq2+detuning-stokes_detuning*stokes_number))
    return error

def check_simultaneity(mode1,mode2):
    error=1
    ii_b,jj_b=0,0
    for ii,birth_time1 in enumerate(mode1.birth_times):
        for jj,birth_time2 in enumerate(mode2.birth_times):
            if abs(birth_time2-birth_time1)<error:
                error=abs(birth_time2-birth_time1)
                ii_b=ii
                jj_b=jj
    return error,ii_b,jj_b

def find_stokes_modes(modes1,modes2,stokes_number=1, print_lists=False,
                      acceptable_freq_error=40e6,
                      acceptable_time_error=300e-6):
    list_errors=[]
    for ii,m1 in enumerate(modes1):
        for jj,m2 in enumerate(modes2):
            error_freq=error_of_stokes_freqs(m1.freq, m2.freq, detuning,stokes_number)
            error_time,ii_b,jj_b=check_simultaneity(m1,m2)
            if print_lists:
                print('ii={},jj={},error_freq ={:.2f} MHz, unsimult={:.2f} mks'.format(ii,jj,error_freq/1e6,error_time*1e6))
            list_errors.append([error_freq,error_time,ii,jj,ii_b,jj_b])
    list_errors.sort()
    for l in list_errors:
        if l[0]<acceptable_freq_error:
            if l[1]<acceptable_time_error:
                return l[2],l[3],l[4],l[5]#ii,jj,ii_b,jj_b
    return np.nan,np.nan, np.nan,np.nan


def create_list_of_simult_brillouin_modes(modes1,modes2,detuning,stokes_number=1,print_lists=False,
                                       acceptable_freq_error=50e6, # Hz
                                       acceptable_time_error=300e-6): # s
    list_errors=[]
    for ii,m1 in enumerate(modes1):
        for jj,m2 in enumerate(modes2):
            error_freq=error_of_stokes_freqs(m1.freq, m2.freq, detuning,stokes_number)
            error_time,ii_b,jj_b=check_simultaneity(m1,m2)
            if print_lists:
                print('ii={},jj={},error_freq ={:.2f} MHz, unsimult={:.2f} mks'.format(ii,jj,error_freq/1e6,error_time*1e6))
            list_errors.append([error_freq,error_time,ii,jj,ii_b,jj_b])
    list_errors.sort()
    new_list=[]
    for l in list_errors:
        if l[0]<acceptable_freq_error:
            if l[1]<acceptable_time_error:
                new_list.append(l)
    return new_list

def get_correlation_time(spec1,spec2,detuning,stokes_number,
                         mode_index_1, mode_index_2,mode1_birth_time_index,plot=True,
                         span=5e-3):
    mode1=spec1.modes[mode_index_1]
    mode2=spec2.modes[mode_index_2]
    times,mode1_d=spec1.get_mode_dynamics(mode_index_1)
    _,mode2_d=spec2.get_mode_dynamics(mode_index_2)
    mode1_d=mode1_d[(times > mode1.birth_times[mode1_birth_time_index]-span) & (times<mode1.death_times[mode1_birth_time_index]+span)]
    mode2_d=mode2_d[(times > mode1.birth_times[mode1_birth_time_index]-span) & (times<mode1.death_times[mode1_birth_time_index]+span)]
    times=times[(times > mode1.birth_times[mode1_birth_time_index]-span) & (times<mode1.death_times[mode1_birth_time_index]+span)]

    correlation=signal.correlate(mode1_d,mode2_d)
    correlation /= np.sqrt(np.sum(np.abs(mode1_d)**2)*np.sum(np.abs(mode2_d)**2))
    correlation_lags=signal.correlation_lags(len(mode1_d),len(mode2_d))
    correlation_lags=correlation_lags*(times[1]-times[0])
    
 
        
        
    correlation_shift=correlation_lags[np.argmax(correlation)]
    
    error_of_stokes_freq=error_of_stokes_freqs(mode1.freq,mode2.freq,detuning,stokes_number)
    
    error_time,_,_=check_simultaneity(mode1,mode2)
    
    if plot:
        fig_dynamics=plt.figure()
        plt.plot(times,mode1_d,label='pump')
        plt.xlabel('Time, s')
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.plot(times,mode2_d,color='red',label='Stokes')
        plt.ylabel('Insensity, arb.u.')
        plt.tight_layout()
        plt.legend()
        plt.title('Detuning={:.2f} MHz'.format(error_of_stokes_freq/1e6))
    
    
        fig_correlation=plt.figure(figsize=(8,6))
        plt.plot(correlation_lags,correlation)
        plt.gca().xaxis.set_major_formatter(formatter1)
        plt.xlabel('Delay, s')
        plt.ylabel('Correlation')
        plt.tight_layout()
    else:
        fig_dynamics=None
        fig_correlation=None
    
        
    return correlation_shift,error_of_stokes_freq,error_time,fig_dynamics,fig_correlation
    
def get_oscillogram(trace,t_min,t_max):
    times=np.arange(len(trace.data))*trace.xinc
    return times[(times>t_min) & (times<t_max)],trace.data[(times>t_min) & (times<t_max)]

def plot_oscillogram(trace,t_min,t_max):
    times, data=get_oscillogram()
    
    



#%%

if __name__=='__main__':
    
    


    # file='3rdStokes-32.7-29'
    folder=r'F:\!Projects\!Rayleigh lasers - localisation, heterodyne, coherent detection\2022.06 Several Stokes\data'
    # file_list=os.listdir(folder)
    # file='1stStokes-12.6-6'
    file='1stStokes-12.6-5'
    # file='1stStokes-12.6-0'
    # file='2ndStokes-22.6-1'
    # file='2ndStokes-22.6-13'
    # file='3rdStokes-32.7-29'

    stokes_number=int(file[0])
    detuning=float(file.split('-')[1])*1e9
    # folder='data\\'
    with open(folder+'\\'+file,'rb') as f:
        data=pickle.load(f)


    win_time=1e-6
    # IsAveraging=False
    IsAveraging=True
    average_freq_window=3e6
    average_time_window=1e-6

    real_power_ch1=0

    trace_stokes=data['balance']
    trace_init=data['hetero']
    spec1=create_spectrogram_from_data(trace_init.data,trace_init.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                       real_power_coeff=real_power_ch1,high_cut_off=4e9,low_cut_off=50e6)
    spec2=create_spectrogram_from_data(trace_stokes.data,trace_stokes.xinc,IsAveraging=IsAveraging,win_time=win_time,average_freq_window=average_freq_window,average_time_window=average_time_window,
                                       real_power_coeff=real_power_ch1,high_cut_off=4e9,low_cut_off=50e6)
    
    spec1.plot_spectrogram(scale='log')
    spec2.plot_spectrogram(scale='log')
    spec1.find_modes(indicate_modes_on_spectrogram=True,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=False)
    spec2.find_modes(indicate_modes_on_spectrogram=True,prominance_factor=3,height=1e-15,min_freq_spacing=2e6,plot_shrinked_spectrum=False)
    
    spec1.print_all_modes()
    spec2.print_all_modes()
    #%%
    pair_list=create_list_of_simult_brillouin_modes(spec1.modes, spec2.modes,detuning,stokes_number,
                                                 print_lists=True)
    print(pair_list)
    for l in pair_list:
        correlation_shift,error_of_stokes_freq,error_time=get_correlation_time(spec1,spec2,detuning,stokes_number,l[2],l[3],l[4],plot=True)
        print('{:.2f} mks, error = {:.2f} MHz, error_time={:.2f} mks'.format(correlation_shift*1e6,error_of_stokes_freq/1e6,error_time*1e6))
    
        
    #%%


