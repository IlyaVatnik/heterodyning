# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 14:23:20 2021

@author: stelt
"""

import pyvisa
import numpy as np
import time
from sys import stdout


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
        
    def set_measurement_mode(self,mode='SINGLe'):
        '''
        AUTO Auto sweep
        REPEAT Repeat sweep
        SINGLE Single sweep
        STOP Sweep stop
        '''
        self.clear()
        self.resource.write_raw(':INITiate:SMODe '+mode)
        
    def start_measurements(self):
        self.clear()
        self.resource.write_raw(':INITiate:IMMediate')
        # self.resource.write_raw(':INITiate:SMODe REPeat')
    
        
    
        
    def abort(self):
        self.clear()
        self.resource.write_raw(':ABORt')
        
    
        
    def set_average_count(self,n:int):
        self.clear()
        self.resource.write_raw(':SENSE:AVERAGE:COUNT '+str(n))
        
    def get_average_count(self):
        self.clear()
        return int(self.query_string(':SENSE:AVERAGE:COUNT?'))
    
    def set_sensitivity(self,sens:str):
        self.clear()
        self.resource.write_raw(':SENSE:SENSe '+sens)
        
    def get_sensitivity(self):
        self.clear()
        return self.query_string(':SENSE:SENSe?')
    
    def set_trace_mode(self,trace='A',mode='WRITE'):
        '''
        WRITe = WRITE
        FIX = FIX
        MAX = MAX HOLD
        MIN = MIN HOLD
        RAVG = ROLL AVG
        CALC = CALC
        '''
        self.clear()
        self.resource.write_raw(':TRACE:ATTRIBUTE:TR'+trace+' '+mode)
        
    def get_trace_mode(self,trace='A'):
        '''
        WRITe = WRITE
        FIX = FIX
        MAX = MAX HOLD
        MIN = MIN HOLD
        RAVG = ROLL AVG
        CALC = CALC
        '''
        self.clear()
        return self.query_string(':TRACE:ATTRIBUTE:TR'+trace+'?')
    
    
    def clear_trace(self,trace='A'):
        self.clear()
        self.resource.write_raw(':TRACE:DELETE TR'+trace)

    
    
    
    def query_trace(self):
        self.resource.write_raw(':FORMat:DATA ASCii')
        wl = np.array(self.query_string(':TRACe:X? TRA').split(b','), dtype = 'f')
        amp = np.array(self.query_string(':TRACe:Y? TRA').split(b','), dtype = 'f')
        return wl, amp
    
    
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    osa = Yokogawa()
    
    



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

