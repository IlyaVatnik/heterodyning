# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 14:47:14 2020

@author: stelt
modified by Ilya

Run as main() to see example process
"""

import pyvisa
import numpy as np
import time
from sys import stdout 

#'WINDOWS-E76DLEM'

__version__='2'
__date__='2023.03.16'

class Wave:
    def __init__(self, datA, xinC):
        self.data = datA
        self.xinc = xinC
        

class Scope:
    
    def __init__(self, host = 'WINDOWS-E76DLEM', protocol = 'hislip0', backend = None, timeout = 5000):
        if backend:
            self.resource = pyvisa.ResourceManager(backend).open_resource('TCPIP0::'+host+'::'+protocol+'::INSTR')
        else:
            self.resource = pyvisa.ResourceManager().open_resource('TCPIP0::'+host+'::'+protocol+'::INSTR')
        self.resource.timeout = timeout
        
        stdout.write(str(self.query_string('*IDN?')+b'\n'))
        self.clear()
        self.resource.write_raw(b':SYSTem:HEADer 0')
        
        self.point_lims = list(map(int,self.query_string(':ACQuire:POINts:TESTLIMITS?')[11:].split(b':')))
        self.srate_lims = list(map(float,self.query_string(':ACQuire:SRATe:TESTLIMITS?')[11:].split(b':')))
           
    def err_code(self):
        self.resource.write_raw(b':SYSTem:ERRor?')
        resp = self.resource.read_raw()[:-1]
        if b':SYST:ERR ' in resp:
            return int(resp[10:])
        else:
            return int(resp)
        
    def clear(self):
        """
        use if all is fucked
        """
        self.resource.write_raw(b'*CLS')
    
    def err_corr(self):
        if self.err_code():
            self.clear()
            return 1
        else:
            return 0
        
    def command(self, command):
         self.err_corr()
         return self.resource.write_raw(bytes(command, encoding = 'utf8'))
     
    def read(self):
        return self.resource.read_raw()
     
    def query_string(self, command):
        self.err_corr()
        if not command[-1] == '?':
            raise RuntimeError('query with no question mark')
        self.resource.write_raw(bytes(command, encoding = 'utf8'))
        return self.resource.read_raw()[:-1]
    
    """
    
    def query_wave(self):
        self.err_corr()
        self.resource.write_raw(':SYSTem:HEADer?')
        is_header = self.resource.read_raw()[-2]
        self.resource.write_raw(':SYSTem:HEADer 0')
        
        self.resource.write_raw(':WAVeform:STReaming?')
        is_streaming = self.resource.read_raw()[-2]
        self.resource.write_raw(':WAVeform:STReaming 1')
        
        self.resource.write_raw(':WAVeform:BYTeorder?')
        byteorder = self.resource.read_raw()[-2]
        self.resource.write_raw(':WAVeform:BYTeorder MSBF')
        
        self.resource.write_raw(":WAVeform:PREamble?")
        preamble = self.resource.read_raw()
        (wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin,
         x_reference, y_increment, y_origin, y_reference, coupling,
         x_display_range, x_display_origin, y_display_range,
         y_display_origin, date, time, frame_model, acq_mode,
         completion, x_units, y_units, max_bw_limit, min_bw_limit
         ) = preamble.split(b",")
         
        if not ( int(wav_form) in (1,2) ):
            raise RuntimeError('Currently not supported wave format')
        
        origins = np.array(list(map(float,(x_increment, x_origin, y_increment, y_origin))), dtype = 'f')
        
        self.resource.write_raw(':WAVeform:DATA?')
        wave = np.frombuffer(self.resource.read_raw()[2:-1],dtype = np.dtype('>i{}'.format(int(wav_form))))*origins[2]+origins[3]

        self.resource.write_raw(':SYSTem:HEADer '+str(is_header))
        self.resource.write_raw(':WAVeform:STReaming '+str(is_streaming))                
        self.resource.write_raw(':WAVeform:BYTeorder '+byteorder)
        
        return Wave(wave,origins[0])
    """
        
    def query_wave_fast(self):
        """
        Currently only for int16 polling.
        Setup required for correct operation:
            :SYSTem:HEADer 0
            :WAVeform:STReaming 1
            :WAVeform:BYTeorder MSBF
        """
        self.resource.write_raw(b":WAVeform:PREamble?")
        preamble = self.resource.read_raw()
        (wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin,
         x_reference, y_increment, y_origin, y_reference, coupling,
         x_display_range, x_display_origin, y_display_range,
         y_display_origin, date, time, frame_model, acq_mode,
         completion, x_units, y_units, max_bw_limit, min_bw_limit
         ) = preamble.split(b",")
        
        origins = np.array(list(map(float,(x_increment, x_origin, y_increment, y_origin))), dtype = 'f')
        self.resource.write_raw(b':WAVeform:DATA?')
        wave = np.frombuffer(self.resource.read_raw()[2:-1],dtype = np.dtype('>i2'))*origins[2]+origins[3]
    
        return Wave(wave,origins[0])
    
    def set_wfm_source(self, ch_num = 1, source_str = None):
        """ choose data for download"""
        if source_str:
            self.resource.write_raw(bytes(':WAVeform:SOURce {}'.format(source_str), encoding = 'utf8'))
        else:
            self.resource.write_raw(bytes(':WAVeform:SOURce CHAN{}'.format(ch_num), encoding = 'utf8'))
        return self.query_string(':WAVeform:SOURce?')+b'\n'
    
    # def set_params(self, average_count = 0, # if 0 - no average
    #                trace_points = 0, # if 0 - minimum
    #                sampling_rate = 0, # if 0 - minimum
    #                trigger = 'AUTO',
    #                trigger_channel=1,
    #                channels_displayed=(1,)):

    #     channels_coupling={}
    #     for ch in channels_displayed:
    #         channels_coupling[ch]='DC50'
            
    #     self.macro_setup(channels_displayed, channels_coupling,
    #                      mode = 'RTIMe', average_count=average_count, # if 0 - no average
    #                      trace_points = trace_points, # if 0 - minimum
    #                      sampling_rate = sampling_rate, # if 0 - minimum
    #                      trigger = trigger,
    #                      trigger_channel=trigger_channel,
    #                      wave_byteorder = 'MSBF',
    #                      wave_format = 'WORD', 
    #                      wave_source = channels_displayed[0], # channel number
    #                      wave_view = 'ALL', # ALL for full data, MAIN for display drawn data
    #                      streaming = 'ON',
    #                      header = 'OFF'
    #                      )
    
    def macro_setup(self,
            channels_displayed = (1,),
            channels_coupling = {1:'DC50'},
            mode = 'RTIMe',
            average_count = 0, # if 0 - no average
            trace_points = 0, # if 0 - minimum
            sampling_rate = 0, # if 0 - minimum
            trigger = 'AUTO',
            trigger_channel=1,
            bandwidth='AUTO', # AUTO, MAX, 4E09, 3.5E09, 3E09, 2.5E09, 2E09, 1.5E09, 1E09, 5E08
            wave_byteorder = 'MSBF',
            wave_format = 'WORD', 
            wave_source = 1, # channel number
            wave_view = 'ALL', # ALL for full data, MAIN for display drawn data
            streaming = 'ON',
            header = 'OFF'
            ):
        """
        Needs to be later
        """
        
        self.err_corr()
        self.resource.write_raw(b':SYSTem:HEADer 1')
        remaining = {1,2,3,4}
        for number in channels_displayed:
            remaining -= set((number,))
            self.resource.write_raw(bytes(':CHANnel{}:DISPlay 1'.format(number), encoding = 'utf8'))
            stdout.write(str(self.query_string(':CHANnel{}:DISPlay?'.format(number))+b'\n'))
        for number in remaining:
             self.resource.write_raw(bytes(':CHANnel{}:DISPlay 0'.format(number), 'utf8'))
             stdout.write(str(self.query_string(':CHANnel{}:DISPlay?'.format(number))+b'\n'))
            
        for key in channels_coupling.keys():
            self.resource.write_raw(bytes(':CHANnel{}:INPUT '.format(key)+ channels_coupling[key], encoding = 'utf8'))
            stdout.write(str(self.query_string(':CHANnel{}:INPUT?'.format(key))+b'\n'))
            
        if 64000 > average_count > 0:
            self.resource.write_raw(bytes(':ACQuire:AVERage:COUNt {}'.format(average_count), encoding = 'utf8'))
            self.resource.write_raw(bytes(':ACQuire:AVERage 1', encoding = 'utf8'))
        elif average_count == 0:
            self.resource.write_raw(bytes(':ACQuire:AVERage 0', encoding = 'utf8'))
        else:
            raise RuntimeError('bad average count')
        stdout.write(str(self.query_string(':ACQuire:AVERage:COUNt?')+b'\n'))
        stdout.write(str(self.query_string(':ACQuire:AVERage?')+b'\n'))
        
        if trace_points < self.point_lims[0]:
            self.resource.write_raw(bytes(':ACQuire:POINts:ANALog {}'.format(self.point_lims[0]), encoding = 'utf8'))
        elif trace_points > self.point_lims[1]:
            self.resource.write_raw(bytes(':ACQuire:POINts:ANALog {}'.format(self.point_lims[1]), encoding = 'utf8'))
        else:
            self.resource.write_raw(bytes(':ACQuire:POINts:ANALog {}'.format(trace_points), encoding = 'utf8'))
        stdout.write(str(self.query_string(':ACQuire:POINts:ANALog?')+b'\n'))
        
        if sampling_rate < self.srate_lims[0]:
            self.resource.write_raw(bytes(':ACQuire:SRATe:ANALog {}'.format(self.srate_lims[0]), encoding = 'utf8'))
        elif sampling_rate > self.srate_lims[1]:
            self.resource.write_raw(bytes(':ACQuire:SRATe:ANALog {}'.format(self.srate_lims[1]), encoding = 'utf8'))
        else:
            self.resource.write_raw(bytes(':ACQuire:SRATe:ANALog {}'.format(sampling_rate), encoding = 'utf8'))
        stdout.write(str(self.query_string(':ACQuire:SRATe:ANALog?')+b'\n'))
        
        self.resource.write_raw(bytes(':ACQuire:MODE '+mode, encoding = 'utf8'))
        stdout.write(str(self.query_string(':ACQuire:MODE?')+b'\n'))
        
        self.resource.write_raw(bytes('TRIGger:SWEep '+trigger, encoding = 'utf8'))
        stdout.write(str(self.query_string('TRIGger:SWEep?')+b'\n'))

        self.resource.write_raw(bytes(':TRIGger:EDGE:SOURce CHANnel{}'.format(trigger_channel), encoding = 'utf8'))
        # stdout.write(str(self.query_string('TRIGger:AND:SOURce? CHANnel')+b'\n'))
        
        self.resource.write_raw(bytes(':ACQuire:BANDwidth {}'.format(bandwidth), encoding = 'utf8'))
        # stdout.write(str(self.query_string('TRIGger:AND:SOURce? CHANnel')+b'\n'))
        
        self.resource.write_raw(bytes(':WAVeform:FORMat ' + wave_format, encoding = 'utf8'))
        stdout.write(str(self.query_string(':WAVeform:FORMat?')+b'\n'))
        
        self.resource.write_raw(bytes(':WAVeform:BYTeorder ' + wave_byteorder, encoding = 'utf8'))
        stdout.write(str(self.query_string(':WAVeform:BYTeorder?')+b'\n'))
          
        self.resource.write_raw(bytes(':WAVeform:VIEW {}'.format(wave_view), encoding = 'utf8'))
        stdout.write(str(self.query_string(':WAVeform:VIEW?')+b'\n'))
        
        self.resource.write_raw(bytes(':WAVeform:STReaming ' + streaming, encoding = 'utf8'))
        stdout.write(str(self.query_string(':WAVeform:STReaming?')+b'\n'))
        
        self.resource.write_raw(bytes(':SYSTem:HEADer ' + header, encoding = 'utf8'))
        stdout.write(str(self.query_string(':SYSTem:HEADer?')+b'\n'))
           
    def vertical_autoscale(self, ch_num):
        self.err_corr()
        self.resource.write_raw(bytes(':AUToscale:VERTical CHANnel{}'.format(ch_num), encoding = 'utf8'))
        
        
    def set_channel_offset(self,ch_num,offset):
        self.err_corr()
        self.resource.write_raw(bytes(':CHANnel{}:OFFSet '.format(ch_num)+'{}'.format(offset), encoding = 'utf8'))
        
        
    def acquire(self, timeout = np.inf, sleep_step = 0.01):
        """
        Acquire trace using current setup.
        Default timeout is infinite, every ~5 sec a message is written to stdout
        """
        self.err_corr()
        self.resource.write_raw(b':SINGle')
        i = 0
        t0 = time.time()
        self.query_string(':ADER?')
        while time.time() - t0 < timeout:
            if int(self.query_string(':ADER?')):
                stdout.write('Acquisition complete\n')
                break
            else:
                i+=1
                if i % 500 == 0:
                    if int(self.query_string(':ACQuire:AVERage?')):
                        stdout.write('Averaging... \n')
                    else:
                        stdout.write('Are you sure your trigger setup is correct?\n')
                time.sleep(sleep_step)
        else:
            raise RuntimeError('Acquisition timeout')
    
    def acquire_and_return(self,ch_num):
        self.acquire(sleep_step=2)
        self.set_wfm_source(ch_num)
        return self.query_wave_fast()
        
    def get_data(self,ch_num):
        self.set_wfm_source(ch_num)
        return self.query_wave_fast()
        
      
    def SRQEnable(self):
        self.command('OPEE 1')
        stdout.write(str(self.query_string(':OPEE?')+b'\n'))
        self.command('*SRE 128')
        stdout.write(str(self.query_string('*SRE?')+b'\n'))
        
        self.event_type = pyvisa.constants.EventType.service_request
        self.event_mech = pyvisa.constants.EventMechanism.queue
        
        self.resource.enable_event(self.event_type, self.event_mech)
        
    def SRQAcquire(self, timeout = 25000):
        """preferable use, enable first"""
        self.clear()
        self.err_corr()
        self.query_string(':ADER?')
        self.resource.write_raw(b':SINGle')
        self.resource.wait_on_event(self.event_type, timeout)
        
        if int(self.query_string(':ADER?')):
            stdout.write('Acquisition complete\n')
        else:
            raise RuntimeError(':ADER not asserted')
            
        
        
        

if __name__ == '__main__':
    scope = Scope('WINDOWS-E76DLEM')
    scope.set_channel_offset(1, 0)
    # scope.macro_setup(
    #         channels_displayed = (1,3),
    #         channels_coupling = {1:'DC50', 3:'DC50'},
    #         average_count = 0, # if 0 - no average
    #         trace_points = 1e9, # if 0 - minimum
    #         sampling_rate = 1e9, # if 0 - minimum
    #         trigger = 'AUTO',
    #         trigger_channel=4,
    #         wave_source = 1) # channel number
    scope.acquire()
    scope.set_wfm_source(2)
    wave = scope.query_wave_fast()


    