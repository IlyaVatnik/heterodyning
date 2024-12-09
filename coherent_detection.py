import numpy as np
from scipy.optimize import minimize
from scipy.fft import rfft, rfftfreq,irfft
from matplotlib.ticker import EngFormatter
formatter1 = EngFormatter()
import matplotlib.pyplot as plt

  
def derive_dynamics(I,Q,time_step,delay=0,norm_coeff=1,
                    remove_linear_phase=True,detuning=None,
                    fitting_times=None):
    '''
    Parameters
    ----------
    I : array
        First channel oscilloscope (Inphase).
    Q : array
        Second channel oscilloscope (Quadratice).
    time_step : float
        time increment of osciiloscopes.
    delay : float, optional
        Physical delay between channels, ps
    norm_coeff : float, optional
        Difference in channel sensitivities

    Returns
    -------
    times : float array
        time stamps
    Intensity : float array
        Derived intensity dynamics.
    Phase : float array
        Derived phase dynamics.

    '''
    delay_index=abs(int(np.floor(delay*1e-12/time_step)))
    
    if delay_index!=0 and delay>0:
        I=I[:-delay_index]
        Q=Q[delay_index:]
        
    elif delay<0:
        I=I[delay_index:]
        Q=Q[:-delay_index]
    else:
        pass
    
    
    Q[Q==0]=1e-16        #replace zeros in Q on machine epsilon
    I_norm=I*norm_coeff
    
    Intensity=(I_norm**2+Q**2)
    Phase=np.arctan(I_norm/Q)
    Phase=np.unwrap(Phase,discont=np.pi/2, period=np.pi)
    # Phase=np.unwrap(Phase,discont=np.pi, period=2*np.pi)
    times=time_step*np.arange(len(I))
    if remove_linear_phase:
        if detuning is None:
            if fitting_times==None:
                fit_params=np.polyfit(times,Phase,deg=1)
                Phase-=fit_params[1]+times*fit_params[0]
            else:
                start_time,stop_time=fitting_times[0],fitting_times[1]
                ind_start=np.argmin(abs(times-start_time))
                ind_stop=np.argmin(abs(times-stop_time))
                fit_params=np.polyfit(times[ind_start:ind_stop],Phase[ind_start:ind_stop],deg=1)
                Phase-=fit_params[1]+times*fit_params[0]
        else:
            Phase-=detuning*2*np.pi*times
    return times,Intensity,Phase

def optimize_delay_and_coeff(signal1,signal2,xinc): 
    '''
    finds proper delay between ch1 and ch2, and sensitivity correction coefficient 
    for ch1
    
    signal1 and signal2 - time traces for the single-wavelength signal with CONSTANT intensity

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    def cost_function(arg):
        delay,norm_coeff=arg[0],arg[1]
        
        _,Intensity,_=derive_dynamics(signal1, signal2, xinc,delay,norm_coeff)
        deviation=np.std(Intensity)/np.mean(Intensity)
        
        return deviation
    
        
    res = minimize(cost_function, (0,1), method='Nelder-Mead',
                   bounds=((-500,500),(0.8,1.2)),tol=1e-8)
    print(res)
    delay,norm_coeff=res.x[0],res.x[1]
    print('delay={} ps, norm_coeff={}'.format(delay, norm_coeff))
    return delay, norm_coeff

def plot_dynamics(times,Intensity,Phase):
    fig,axes=plt.subplots(2,1,sharex=True,figsize=(10,7))

    axes[0].plot(times,Intensity)
    axes[0].set_ylabel('Intensity, arb.u.')
    axes[0].set_title('Intensity')
    axes[0].xaxis.set_major_formatter(formatter1)
    axes[0].yaxis.set_major_formatter(formatter1)


    axes[1].plot(times,Phase/np.pi)
    axes[1].set_xlabel('Time, s')
    axes[1].set_ylabel(r'Phase, $\pi$')
    axes[1].set_title('Phase derived')
    axes[1].xaxis.set_major_formatter(formatter1)
    

    plt.tight_layout()
    plt.show()
    
    
def filter_signals(signal1,signal2, xinc,mode_freq,
                   mode_bandwidth=10e6,
                   low_freqs_to_remain=100e6):
    
    freqs = rfftfreq(len(signal1), xinc)
    
    
    yf = rfft(signal1)
    yf[freqs>mode_freq+mode_bandwidth/2] = 0
    yf[(freqs<mode_freq-mode_bandwidth/2) & (freqs>low_freqs_to_remain)] = 0
    new_signal1 = irfft(yf)
    
    yf = rfft(signal2)
    yf[freqs>mode_freq+mode_bandwidth/2] = 0
    yf[(freqs<mode_freq-mode_bandwidth/2) & (freqs>low_freqs_to_remain)] = 0
    new_signal2 = irfft(yf)
    

    return new_signal1,new_signal2,xinc


def filter_phase(phase, xinc, low_cut_off):
    freqs = rfftfreq(len(phase), xinc)
    yf = rfft(phase)
    yf[freqs<low_cut_off] = 0
    new_phase = irfft(yf)
    return new_phase