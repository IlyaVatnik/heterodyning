from heterodyning.spectrograms_with_scanning_interrogator import TraceAnalyzer2D
import numpy as np
import time

time_to_derive_spectrum=0.000



__date__='2026.08.27'

class Interrogator_OSA():
    
    def __init__(self,
                 scope,
                 channel_signal,
                 channel_trigger=None,
                 polarization_channels='single', # 'both'
                 channel_signal_2=None,
                 
                 start_wavelength=1528,
                 stop_wavelength=1568,
                 start_time=None,
                 sampling_rate=500e6,
                 scope_acqusition_time=10e-3,
                 channel_signal_1_scale=0.05,
                 channel_signal_2_scale=None,
                 

                 
                 wavelength_resolution=0.02,
                 power_coeff_pol=1,
                 power_control_powermeter=None,
                 full_source_power=0): 
        
        self.scope=scope
        self.channel_signal=channel_signal
        self.channel_trigger=channel_trigger
         
        self.channel_signal_1_scale=channel_signal_1_scale
        self.channel_signal_2_scale=channel_signal_2_scale
        
        
        self.start_wavelength=start_wavelength
        self.stop_wavelength=stop_wavelength
        self.start_time=start_time

        self.channel_signal_2=channel_signal_2
        
        self.power_coeff_pol=power_coeff_pol
        
        
        
        self.polarization_channels=polarization_channels
        
        if power_control_powermeter!=None:
            self.PM=power_control_powermeter
            self.full_source_power=full_source_power # mW
        else:
            self.PM=None
        
        if self.channel_trigger!=None:
            self.analyzer=TraceAnalyzer2D(trigger_by='ax_channel',start_wavelength=start_wavelength,stop_wavelength=stop_wavelength,
                                          wavelength_resolution=wavelength_resolution)
        else:
            self.analyzer=TraceAnalyzer2D(trigger_by='balanced_channel',start_wavelength=start_wavelength,stop_wavelength=stop_wavelength,
                                          wavelength_resolution=wavelength_resolution)
        

        '''
        channel_signal - для гетеродинного сигнала
        channel_trigger - для сигнала запуска
        '''
        
        self.start_time=start_time
        
        self.trace_signal=None
        self.trace_trigger=None
        
        self.sampling_rate=sampling_rate
        self.scope_acqusition_time=scope_acqusition_time
        
    
        scope_trace_points_set = self.scope_acqusition_time*self.sampling_rate
    
        memory_depth, sampling_rate=self.scope.macro_setup(channels_displayed=(self.channel_signal,self.channel_trigger,self.channel_signal_2),
                                                      acq_time=self.scope_acqusition_time,trace_points=scope_trace_points_set,
                                                      channels_impedances={self.channel_signal:'FIFTy',self.channel_signal:'FIFTy'},
                                                      trigger='SINGLe')
        
        
        
        channel_signal_offset=0
        
     
        
        
        
        self.scope.set_channel_scale(self.channel_signal,self.channel_signal_1_scale)
        self.scope.set_channel_offset(self.channel_signal,channel_signal_offset)
        
        if self.polarization_channels=='both':
            self.scope.set_channel_impedance(self.channel_signal_2,'FIFTy')
            self.scope.set_channel_scale(self.channel_signal_2,self.channel_signal_2_scale)
            self.scope.set_channel_offset(self.channel_signal_2,channel_signal_offset)
     
            
            
        central_wavelength=(self.stop_wavelength-self.start_wavelength)/2+self.start_wavelength
        delay=self._wave_to_time(central_wavelength)

        
        self.scope.set_delay(delay)
    
    def _wave_to_time(self,wave):
        try:
            return (self.start_time+self.analyzer.sleep_time+
                      (np.sqrt(self.analyzer.sweep_speed**2+
                               4*self.analyzer.sweep_accel*(wave-self.analyzer.interrogator_start_wavelength))-self.analyzer.sweep_speed ) /2/self.analyzer.sweep_accel)
        except TypeError:
            print('start_time is not specified')
            
            
    def _time_to_wave(self,x):
        try:
            # return (self.start_time+self.analyzer.sleep_time+
            #           (np.sqrt(self.analyzer.sweep_speed**2+
            #                    4*self.analyzer.sweep_accel*(wave-self.analyzer.interrogator_start_wavelength))-self.analyzer.sweep_speed ) /2/self.analyzer.sweep_accel)
        
        
            return (x-self.analyzer.sleep_time-self.start_time) * self.analyzer.sweep_speed + (x-self.analyzer.sleep_time-self.start_time)**2*self.analyzer.sweep_accel+self.analyzer.interrogator_start_wavelength
   
        except TypeError:
            print('start_time is not specified')
    

            
            
    def query_trace(self,scale='log',timeout=1):

        self.signal_acquired=False
        t0 = time.time()
        # int(self.query_string('*OPC?'))
        
        while time.time() - t0 < timeout:
            self.trace_signal=self.scope.get_data(self.channel_signal)
            if len(self.trace_signal[0])>1:
                self.signal_acquired=True
                break
            
        
            
        # if self.start_time==None:
            # if self.channel_trigger!=None:
            #     t0 = time.time()
            #     while time.time() - t0 < timeout:
            #         self.trace_trigger=self.scope.get_data(self.channel_trigger)
            #         if len(self.trace_trigger[0])>1:
            #             break
            
            #     raw_times=self.trace_trigger[2]+np.arange(len(self.trace_trigger[0]))*self.trace_trigger[1]
            #     detect_jump_results=detect_jump_by_template(raw_times, self.trace_trigger[0], self.analyzer.t_tpl, self.analyzer.y_tpl0,self.analyzer.tpl_norm,
            #                                                 searching_time=self.analyzer.sweep_period*2)
            #         # print('jump detected')
            #     self.start_time=detect_jump_results['jump_time']
                

        if self.signal_acquired:
            self.analyzer.process(self.trace_signal[0], self.trace_signal[1], self.trace_signal[2],self.start_time)
            waves, spectrum_polarization_1 = self.analyzer.get_instant_spectrum(time_to_derive_spectrum)
            if self.polarization_channels=='both':
                while time.time() - t0 < timeout:
                    self.trace_signal=self.scope.get_data(self.channel_signal_2)
                    if len(self.trace_signal[0])>1:
                        self.signal_acquired=True
                        break
                self.analyzer.process(self.trace_signal[0], self.trace_signal[1], self.trace_signal[2],self.start_time)
                _, spectrum_polarization_2 = self.analyzer.get_instant_spectrum(time_to_derive_spectrum)
            else:
                spectrum_polarization_2=np.ones(len(waves))*1e-20
            
            spectrum_polarization_2*=self.power_coeff_pol
            
            self.start_time=self.analyzer.start_time+self.analyzer.sweep_period*int(time_to_derive_spectrum/0.005)
            
            if self.PM!=None:
                current_power=self.full_source_power-self.PM.get_power()
                coeff=np.sqrt(current_power*2/self.full_source_power)
                spectrum_polarization_2*=coeff
                spectrum_polarization_1*=coeff
        
        else:
            waves=np.array([self.start_wavelength,self.stop_wavelength])
            spectrum_total=np.array([1e-20,1e-20])
            spectrum_polarization_1=np.array([1e-20,1e-20])
            spectrum_polarization_2=np.array([1e-20,1e-20])
            self.analyzer.start_time=0
                
        spectrum_total=spectrum_polarization_1+spectrum_polarization_2
        
        if scale=='log':
            spectrum_polarization_1=10*np.log10(spectrum_polarization_1)
            spectrum_polarization_2=10*np.log10(spectrum_polarization_2)
            spectrum_total=10*np.log10(spectrum_total)
        
        return waves, spectrum_total,spectrum_polarization_1,spectrum_polarization_2,self.start_time,current_power

    def acquire(self,timeout=3):
        
            # print(1)
            # scope.wait()
            # scope.force_trigger()
        try:
            self.scope.acquire(timeout=timeout)
        except RuntimeError:
            print('no signal on scope channel')

        
if __name__=='__main__':
    SCOPE_IP = '10.2.60.127'           # IP Осциллографа Tektronix
    INTERROGATOR_IP = '10.2.60.38'     # IP Интеррогатора
    
        
    


