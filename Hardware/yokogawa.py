# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 14:23:20 2021

@author: stelt
"""

import pyvisa
import numpy as np
import time
from sys import stdout

__version__='2'
__date__='2023.03.16'

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
    
    def query_trace(self):
        self.resource.write_raw(':FORMat:DATA ASCii')
        wl = np.array(self.query_string(':TRACe:X? TRA').split(b','), dtype = 'f')
        amp = np.array(self.query_string(':TRACe:Y? TRA').split(b','), dtype = 'f')
        return wl, amp
    
    def set_trace_mode(self, ch='A',type_of_meas='WRITE'):
        res=self.resource.write_raw(':TRACe:ATTRibute:TR{} {}'.format(ch,type_of_meas))

    def set_measurement_mode(self,mode='SINGLE'):
        res=self.resource.write_raw(':INITiate:SMode {}'.format(mode))
    
    
    
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    osa = Yokogawa()
    osa.acquire()
    x, y = osa.query_trace()
    plt.plot(x, y)
    osa.set_trace_mode('A','MAX')
    
    # del osa
    



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
