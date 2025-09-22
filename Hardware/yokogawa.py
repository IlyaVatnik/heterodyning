# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 14:23:20 2021

@author: stelt
"""

import pyvisa
import numpy as np
import time
from sys import stdout

__version__='3.2'
__date__='2025.09.22'

class Yokogawa:
    
    def __init__(self, host = '6370D91UA07984', protocol = 'inst0', backend = None, timeout = 1e5):
        if backend:
            self.resource = pyvisa.ResourceManager(backend).open_resource('TCPIP0::'+host+'::'+protocol+'::INSTR')
        else:
            self.resource = pyvisa.ResourceManager().open_resource('TCPIP0::'+host+'::'+protocol+'::INSTR')
        self.resource.timeout = timeout
        # stdout.write(self.query_string('*IDN?')+b'\n')
        
    def __del__(self):
        self.resource.close()
        
    def clear(self):
        self.resource.write_raw('*CLS')
            
    def query_string(self, command):
        self.clear()
        self.resource.write_raw(command)
        return self.resource.read_raw()[:-1]
        
    def acquire(self):
        self.clear()
        self.resource.write_raw(':INITiate:IMMediate')
        self.query_string('*OPC?')
        
    def wait(self):
        return self.resource.write_raw('*WAI')
    
    def query_trace(self, trace='A'):
        '''
        return wavelengths in nm!
        '''
        self.resource.write_raw(':FORMat:DATA ASCii')
        wl = np.array(self.query_string((':TRACe:X? TR{}').format(trace)).split(b','), dtype = 'f')
        amp = np.array(self.query_string((':TRACe:Y? TR{}').format(trace)).split(b','), dtype = 'f')
        return wl*1e9, amp
    
    def set_trace_mode(self, ch='A',type_of_meas='WRITE'):
        res=self.resource.write_raw(':TRACe:ATTRibute:TR{} {}'.format(ch,type_of_meas))

    def set_measurement_mode(self,mode='SINGLE'):
        res=self.resource.write_raw(':INITiate:SMode {}'.format(mode))
        
    def set_average_count(self,av_count:int):
        res=self.resource.write_raw(':TRACe:ATTRibute:RAVG {}'.format(av_count))
        
    def clear_trace(self):
        active=self.query_string(':TRACe:ACTive?')
        res=self.resource.write_raw(':TRACE:DELETE {}'.format(active))
    
    def abort(self):
        self.resource.write_raw(':ABORt')
        
    def start_measurements(self):
        self.resource.write_raw(':INITiate:IMMediate')
        
    def set_input_trigger_state(self,trigger):
        '''
        OFF:  External Trigger OFF
        ON:  External trigger mode
        PHOLd:  Peak hold mode
        GATE: Gate sampling
        '''
        res=self.resource.write_raw(':TRIGger:STATe {}'.format(trigger))
        
 
    def get_input_trigger_state(self):
        '''
        OFF:  External Trigger OFF
        ON:  External trigger mode
        PHOLd:  Peak hold mode
        GATE: Gate sampling
        Response 0 = OFF, 1 = ON, 2 = PHOLd, 3 = GATE
        '''
        trigger_state=self.query_string(':TRIGger:STATe?')
        return trigger_state
    
    
    def set_input_trigger_type(self,trigger):
        '''
        TRigger|0: Sampling trigger
        STRigger|1: Sweep trigger
        SENable|2: Sample enable
        '''
        res=self.resource.write_raw(':TRIGger:INPUT {}'.format(trigger)) 
        self.query_string('*OPC?')
    
    def get_input_trigger_type(self):
        '''
        TRigger|0: Sampling trigger
        STRigger|1: Sweep trigger
        SENable|2: Sample enable
        '''
        trigger_state=self.query_string(':TRIGger:INPUT?')
        return trigger_state
        
        
    def set_sensitivity(self,sens:str):
        '''
        sens:
            NHLD = NORMAL HOLD
            NAUT = NORMAL AUTO
            NORMal = NORMAL
            MID = MID
            HIGH1 = HIGH1 or HIGH1/CHOP
            HIGH2 = HIGH2 or HIGH2/CHOP
            HIGH3 = HIGH3 or HIGH3/CHOP
        '''
        self.resource.write_raw(':SENSe:SENSe {}'.format(sens))
        
        
    def set_span(self,start_wavelength=None,stop_wavelength=None):
        if start_wavelength is not None:
            Command = ':SENSe:WAVelength:STARt '+f'{start_wavelength:.3f}'+'NM'
            self.resource.write_raw(Command)
        if stop_wavelength is not None:
            Command = ':SENSe:WAVelength:STOP '+f'{stop_wavelength:.3f}'+'NM\n'
            self.resource.write_raw(Command)
            
    def set_sampling_point(self,N_points):
        if  N_points==0:
            Command = ':SENSe:SWEep:POINts:AUTO ON'
        else:
            Command = ':SENSe:SWEep:POINts '+f'{N_points:d}'
        self.resource.write_raw(Command)
        
    def get_sampling_point(self):
        N_points=self.query_string(':SENSe:SWEep:POINts?')
        return int(N_points)
    
    def set_resolution(self,resolution):
        '''
        set in nm
        '''
        Command=':SENSe:BANDwidth:RESolution '+f'{resolution}NM'
        self.resource.write_raw(Command)
    
    def get_resolution(self):
        '''
        return resolution in nm
        '''
        resolution=self.query_string(':SENSe:BANDwidth:RESolution?')
        return float(resolution)*1e9
        
    #%%
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    osa = Yokogawa()
    osa.acquire()
    x, y = osa.query_trace()
    plt.plot(x, y)
    osa.set_trace_mode('A','MAX')
    osa.clear_trace()
    osa.abort()
    
    del osa
    



#:FORMat:DATA REAL,64
#:INITiate:SMODe:SINGle / AUTO
#:SENSe:AVERage:COUNt
#:SENSe:CORRection:RVELocity:MEDium AIR | VACuum
#:SENSe:SENSe: NAUT = NORMAL AUTO | NORMal = NORMAL
#:SENSe:SETTing:FCONnetcor ANGL / NORMal
#:SENSe:SWEep:POINts
#:SENSe:SWEep:POINts:AUTO
#:SENSe:SWEep:STEP
#:SENSe:SWEep:SPEed
#:TRACe:ACTive:TRA:WRITe
#:TRACe:STATe[:<trace name>]
#:TRACe:DELete:ALL
#:TRACe[:DATA]:Y:PDENsity?
#:DISPlay[:WINDow]:TRACe:Y1[:SCALe]:RLEVel
#:DISPlay[:WINDow]:TRACe:Y1[:SCALe]:UNIT
#:SENSe:BANDwidth|:BWIDth[:RESolution]
#:SPACing LOGarithmic|LINear|0|1
#:UNIT DBM|W|DBM/NM|W/NM|0|1|2|3
