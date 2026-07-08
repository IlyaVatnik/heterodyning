from heterodyning.spectrograms_with_scanning_interrogator import TraceAnalyzer2D,detect_jump_by_template
import numpy as np
import time


class Interrogator_OSA():
    
    def __init__(self,
                 scope,
                 channel_signal,
                 channel_trigger=None,
                 start_wavelength=1528,
                 stop_wavelength=1568): 
        
        self.scope=scope
        self.channel_signal=channel_signal
        self.channel_trigger=channel_trigger
        self.start_wavelength=start_wavelength
        self.stop_wavelength=stop_wavelength
        if self.channel_trigger!=None:
            self.analyzer=TraceAnalyzer2D(trigger_by='ax_channel',start_wavelength=start_wavelength,stop_wavelength=stop_wavelength)
        else:
            self.analyzer=TraceAnalyzer2D(trigger_by='balanced_channel',start_wavelength=start_wavelength,stop_wavelength=stop_wavelength)
        
        
        '''
        channel_signal - для гетеродинного сигнала
        channel_trigger - для сигнала запуска
        '''
        
        self.start_time=None
        
        
    def query_trace(self,scale='log',timeout=1):
        time_to_derive_spectrum=0.005
        self.signal_acquired=False
        t0 = time.time()
        # int(self.query_string('*OPC?'))
        
        while time.time() - t0 < timeout:
            trace_1=self.scope.get_data(self.channel_signal)
            if len(trace_1[0])>1:
                self.signal_acquired=True
                break
        if self.channel_trigger!=None:
            t0 = time.time()
            while time.time() - t0 < timeout:
                trace_2=self.scope.get_data(self.channel_trigger)
                if len(trace_2[0])>1:
                    break
        
            raw_times=trace_2[2]+np.arange(len(trace_2[0]))*trace_2[1]
            detect_jump_results=detect_jump_by_template(raw_times, trace_2[0], self.analyzer.t_tpl, self.analyzer.y_tpl0,self.analyzer.tpl_norm,
                                                        searching_time=self.analyzer.sweep_period*2)
                # print('jump detected')
            self.start_time=detect_jump_results['jump_time']
            
        else:
            self.start_time=None
        if self.signal_acquired:
            self.analyzer.process(trace_1[0], trace_1[1], trace_1[2],self.start_time)
            waves, spectrum = self.analyzer.get_instant_spectrum(time_to_derive_spectrum)
            self.start_time=self.analyzer.start_time+self.analyzer.sweep_period*int(time_to_derive_spectrum/0.005)
        else:
            waves=np.array([self.start_wavelength,self.stop_wavelength])
            spectrum=np.array([1e-20,1e-20])
            self.analyzer.start_time=0
                
        
        if scale=='log':
            spectrum=10*np.log10(spectrum)
        
        return waves, spectrum,self.start_time

    def acquire(self,timeout=3):
        self.scope.set_trigger_mode('SINGLE')
        self.scope.trigger='SINGLe'
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
    
        
    


