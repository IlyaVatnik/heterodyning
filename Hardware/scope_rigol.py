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

__version__='2.5'
__date__='2025.11.24'

class Wave:
    def __init__(self, datA, xinC,xorigin=0):
        self.data = datA
        self.xinc = xinC
        self.xorigin = xorigin
        

class Scope:
    
    def __init__(self, host, protocol = 'inst0', backend = None, timeout = 5000):
        if backend:
            self.resource = pyvisa.ResourceManager(backend).open_resource('TCPIP0::'+host+'::'+protocol+'::INSTR')
        else:
            self.resource = pyvisa.ResourceManager().open_resource('TCPIP0::'+host+'::'+protocol+'::INSTR')
        self.resource.timeout = timeout
        
        stdout.write(str(self.query_string('*IDN?')+b'\n'))
        
        self.set_wfm_mode('RAW') #for all data in memory
        self.set_wfm_format('BYTE')
        self.trigger='AUTO'
          
    def err_code(self):
        self.resource.write_raw(b':SYSTem:ERRor?')
        resp = self.resource.read_raw()[:-1]
        if b':SYST:ERR ' in resp:
            return int(resp[10:])
        else:
            return int(resp)
       
    
    
    def macro_setup(self,
            channels_displayed = (1,),
            channels_coupling = {1:'DC50'},
            channels_impedances={1:'FIFTy'},
            acq_time=1e-9,
            trace_points = 0, # if 0 - minimum,
            trigger='AUTO'
            ):
        """
        Needs to be  later
        """
        
    
        
        remaining = {1,2,3,4}
        for number in channels_displayed:
            remaining -= set((number,))
            self.set_channel_on(number)
        for number in remaining:
              self.set_channel_off(number)
          
        
        for key in channels_coupling.keys():
            self.set_channel_coupling(key,channels_coupling[key])
            
        for key in channels_impedances.keys():
            self.set_channel_impedance(key,channels_impedances[key])
        
    
        self.set_timescale(acq_time/10)
        self.set_memory_depth(trace_points)
        self.clear()
        
        self.trigger=trigger
        self.set_trigger_mode(trigger)
        
        self.acquire()
        
        
        
        print('Sampling rate is {} MS/s'.format(self.get_sampling_rate()/1e6))
        print('Memory depth is {:.3e} S'.format(self.get_memory_depth()))
        print('Time span is {:.3f} us'.format(self.get_memory_depth()/self.get_sampling_rate()*1e6))
        
        return [self.get_memory_depth(),self.get_sampling_rate()]
        
    

    
    def clear(self):
        """
        use if all is fucked
        """
        self.resource.write_raw(b'*CLS')
        
    """
    def err_corr(self):
        if self.err_code():
            self.clear()
            return 1
        else:
            return 0
    """
    
    def command(self, command):
         #self.err_corr()
         return self.resource.write_raw(bytes(command, encoding = 'utf8'))
     
    def read(self):
        return self.resource.read_raw()
     
    def query_string(self, command):
        #self.err_corr()
        if not command[-1] == '?':
            raise RuntimeError('query with no question mark')
        self.resource.write_raw(bytes(command, encoding = 'utf8'))
        return self.resource.read_raw()[:-1]
        
    def query_wave_fast(self):
        result=self.resource.write_raw(b":WAVeform:PREamble?")
        preamble = self.resource.read_raw()
        (wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin,
         x_reference, y_increment, y_origin, y_reference) = preamble.split(b",")
        # print(preamble)
        
        result=self.resource.write_raw(b"WAVeform:STARt 1")
        self.resource.write_raw(bytes("WAVeform:STOP {}".format(int(wfmpts)), encoding = 'utf8'))
        origins = np.array(list(map(float,(x_increment, x_origin, y_increment, y_origin))))#, dtype = 'float')
        
        
        # print(origins,int(y_reference))
        result=self.resource.write_raw(b':WAVeform:DATA?')
        raw = self.resource.read_raw()[11:-1]
        raw=(np.frombuffer(raw, dtype = np.uint8)).astype(np.int16)
        # print(raw)
        # plt.figure()
        # plt.plot((np.frombuffer(raw, dtype = np.uint16)).astype(np.int16))
        
        # wave = ((np.frombuffer(raw, dtype = np.uint8)).astype(np.int16) - int(y_reference)) * origins[2] + origins[3]
        wave = (raw - int(y_origin)-int(y_reference)) * origins[2]
        print('Got signal with length of {}'.format(len(wave)))
        return wave,origins[0],origins[1]
    
    """
    def set_acquisition_type(self, typ = 'NORMal'):
        #NORMal
        #AVERages
        #PEAK
        #HRESolution
        self.resource.write_raw(bytes(':ACQuire:TYPE {}'.format(typ), encoding = 'utf8'))
    
    def get_acquisition_type(self):
        return self.query_string(':ACQuire:TYPE?')
    
    def set_average_count(self, average_count  = 2):
        #2 to 65536
        self.resource.write_raw(bytes(':ACQuire:AVERages {}'.format(average_count), encoding = 'utf8'))
        
    def get_average_count(self):
        return self.query_string(':ACQuire:AVERages?')
    """
    def set_wfm_source(self, ch_num = 1, source_str = None):
        if source_str:
            self.resource.write_raw(bytes(':WAVeform:SOURce {}'.format(source_str), encoding = 'utf8'))
        else:
            self.resource.write_raw(bytes(':WAVeform:SOURce CHAN{}'.format(ch_num), encoding = 'utf8'))
    def get_wfm_source(self):
        return self.query_string(':WAVeform:SOURce?')       
    
    def set_wfm_mode(self, mode = 'RAW'):
        self.resource.write_raw(bytes(':WAVeform:MODE {}'.format(mode), encoding = 'utf8'))
    
    
    def set_trigger_mode(self, trigger_mode):
        '''
        AUTO|NORMal|SINGle
        '''
        self.resource.write_raw(bytes(':TRIGger:SWEep {}'.format(trigger_mode), encoding = 'utf8'))
    
    def get_trigger_mode(self):
        '''
        AUTO|NORMal|SINGle
        '''
        return str(self.query_string(':TRIGger:SWEep?').decode('utf-8'))
        
    
    def set_trigger_source(self, source:str):
        '''
        source D0|D1|D2|D3|D4|D5|D6|D7|D8|D9|D10|D11|D12|D13|D14|D15|CHANnel1|CHANnel2|CHANnel3|CHANnel4|ACLine|EXT
        '''
        self.resource.write_raw(bytes(':TRIGger:EDGE:SOURce {}'.format(source), encoding = 'utf8'))
        return 

    def get_trigger_high_level(self):
        return float(self.query_string(':TRIGger:SLOPe:ALEVel?'))
    
    def set_trigger_high_level(self,level):
        self.resource.write_raw(bytes(':TRIGger:SLOPe:ALEVel {}'.format(level), encoding = 'utf8'))
        
    def check_trigger_status(self):
        """
        Проверяет статус триггера осциллографа
        Возвращает: 'TD' (ждущий), 'RUN' (захват), 'STOP' (остановлен), 'AUTO' (авто)
        """
        status = self.query_string(':TRIG:STAT?').decode('utf-8')
        return status.strip()
    
    def wait_for_trigger_status(self, status='STOP',timeout=2):
        """
        Ожидает срабатывания триггера с таймаутом
        """
        start_time = time.time()
        
        # print("Ожидание триггера...")
        while time.time() - start_time < timeout:
            current_status = self.check_trigger_status()
            # print(current_status)
            if current_status == status :
                # Триггер еще не сработал - ожидание
                # print("Статус: Ожидание триггера...")
                return True
            else:
                time.sleep(0.01)
        return False


    
    def get_wfm_mode(self):
        return self.query_string(':WAVeform:MODE?')
    
    def get_xinc(self):
        return float(self.query_string(':WAVeform:XINCrement?'))
    
    def set_wfm_format(self, fmt = 'BYTE'):
        self.resource.write_raw(bytes(':WAVeform:FORMat {}'.format(fmt), encoding = 'utf8'))
    
    def get_wfm_format(self):
        return self.query_string(':WAVeform:FORMat?')
    
    def set_channel_scale(self,ch_num,scale):
        self.resource.write_raw(bytes(':CHANnel{}:SCALe '.format(ch_num)+'{}'.format(scale), encoding = 'utf8'))
    
    def get_channel_scale(self,ch_num):
        return float(self.query_string(':CHANnel{}:SCALe?'.format(ch_num)))
 
    
    
    def set_channel_offset(self,ch_num,offset):
        self.resource.write_raw(bytes(':CHANnel{}:OFFSet '.format(ch_num)+'{}'.format(offset), encoding = 'utf8'))
    
    def get_channel_offset(self,ch_num):
        return float(self.query_string(':CHANnel{}:OFFSet?'.format(ch_num)))
    

    
    def set_memory_depth(self, depth = 'AUTO'):
        if depth == 'AUTO':
            self.resource.write_raw(bytes(':ACQuire:MDEPth {}'.format(depth), encoding = 'utf8'))
        else:
            depths = [(1000, '1k'),
                      (10000, '10k'),
                      (100000, '100k'),
                      (1000000, '1M'),
                      (10000000, '10M'),
                      (25000000, '25M'),
                      (50000000, '50M'),
                      (100000000, '100M'),
                      (125000000, '125M'),
                      (250000000, '250M'),
                      (500000000, '500M')]
            npd = np.array([1000,
                            10000,
                            100000,
                            1000000,
                            10000000,
                            25000000,
                            50000000,
                            100000000,
                            125000000,
                            250000000,
                            500000000])
            closest = np.argmin(np.abs(npd - depth))
            self.resource.write_raw(bytes(':ACQuire:MDEPth {}'.format(depths[closest][1]), encoding = 'utf8'))
        self.resource.write_raw(b':RUN')
        self.resource.write_raw(b':STOP')
        
    def get_memory_depth(self):
        return int(float(self.query_string(':ACQuire:MDEPth?')))
    
    def set_channel_on(self, channel = 1):
        self.resource.write_raw(bytes(':CHANnel{}:DISPlay 1'.format(channel), encoding = 'utf8'))
        
        
    
        
    def set_channel_off(self, channel = 1):
        self.resource.write_raw(bytes(':CHANnel{}:DISPlay 0'.format(channel), encoding = 'utf8'))
        
        
    def set_timescale(self,time_scale):
        self.resource.write_raw(bytes(':TIMebase:MAIN:SCALe {}'.format(time_scale), encoding = 'utf8'))
        
        
    def get_timescale(self):
        return  float(self.query_string(':TIMebase:MAIN:SCALe?'))
    
    def set_delay(self,delay_time):
        self.resource.write_raw(bytes(':TIMebase:DELay:ENABLe TRUE', encoding = 'utf8'))
        self.resource.write_raw(bytes(':TIMebase:DELay:ENABLe TRUE', encoding = 'utf8'))
    
    def get_sampling_rate(self):
        return  int(float(self.query_string(':ACQuire:SRATe?')))
        
    def set_channel_coupling(self, channel = 1, coupling = 'DC'):
        #DC
        #AC
        self.resource.write_raw(bytes(':CHANnel{}:COUPling {}'.format(channel, coupling), encoding = 'utf8'))
        
    def get_channel_coupling(self, channel = 1):
        return self.query_string(':CHANnel{}:COUPling?'.format(channel))
        
    def set_channel_impedance(self, channel = 1, impedance = 'FIFTy'):
        #FIFTy for 50 Ohm
        #OMEG for 1 MOhm
        self.resource.write_raw(bytes(':CHANnel{}:IMPedance {}'.format(channel, impedance), encoding = 'utf8'))
        
    def get_channel_impedance(self, channel = 1):
        return self.query_string(':CHANnel{}:IMPedance?'.format(channel))
    
    """
    def set_trigger_type(self, trigger = 'AUTO'):
        #AUTO
        #NORMal
        #SINGle
        self.resource.write_raw(bytes(':TRIGger:SWEep {}'.format(trigger), encoding = 'utf8'))
        
    def get_trigger_type(self):
        return self.query_string(':TRIGger:SWEep?')
    """
    
    def get_wfm_raw_preamble(self):
        self.resource.write_raw(b":WAVeform:PREamble?")
        return self.resource.read_raw()
 
    def acquire(self, timeout = np.inf, sleep_step = 0.01):
        """
        Acquire trace using current setup.
        Default timeout is infinite, every ~5 sec a message is written to stdout
        """
        #self.err_corr()
        # self.clear()
        if self.trigger=='AUTO':
            self.resource.write_raw(b':TRIGger:SWEep AUTO')
            self.resource.write_raw(b':RUN')
        elif self.trigger=='SINGLe':
            self.resource.write_raw(b':SINGLe')
        i = 0
        t0 = time.time()
        # int(self.query_string('*OPC?'))
        time.sleep(sleep_step)
        while time.time() - t0 < timeout:
            if int(self.query_string('*OPC?')):
                stdout.write('Acquisition complete\n')
                break
            else:
                i+=1
                if i % 500 == 0:
                    #if int(self.query_string(':ACQuire:AVERage?')):
                    #    stdout.write('Averaging... \n')
                    #else:
                        stdout.write('Are you sure your trigger setup is correct?\n')
                time.sleep(sleep_step)
        else:
            raise RuntimeError('Acquisition timeout')
            
    def run(self):
        self.resource.write_raw(b':RUN')
        return
    
    # def wait(self):
    #     return self.resource.write_raw('*WAI')
    
    def wait(self):
        self.resource.write_raw(b':*CLS')
        complete = int(self.query_string('*OPC?').decode('utf-8'))
        while complete != '1':
            time.sleep(0.05)
            complete = str(self.query_string('*OPC?').decode('utf-8'))
        
    
    def stop(self):
        self.resource.write_raw(b':STOP')
        result=self.query_string('*OPC?')
        return result
    
    def acquire_and_return(self,ch_num):
        self.acquire()
        self.set_wfm_source(ch_num)
        N_points=0
        while N_points==0:
            wave,x_inc,x_origin=self.query_wave_fast()
            N_points=len(wave)
        return wave,x_inc,x_origin
        
    def get_data(self,ch_num):
        self.set_wfm_source(ch_num)
        return self.query_wave_fast()
    
    
                #%%
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    ch = 2
    # scope = Scope('10.2.60.239')
    scope = Scope('10.2.60.108')
    print('try something')
    # '''
    # averaging needs to be turned on\off manually
    # '''

    scope.trigger='SINGLe'
    #anyway 8 bit only

    # scope.set_channel_on(ch)
    # scope.set_channel_coupling(ch, 'DC') # 'DC' ot 'AC'
    # print(scope.get_channel_coupling(ch))
    # scope.set_channel_impedance(ch, 'OMEG') # 'FIFTy' for 50 'OMEG' for 1M
    # print(scope.get_channel_impedance(ch))
    # scope.set_wfm_source(ch)
    # print(scope.get_wfm_source())
    # scope.set_memory_depth(2000000)
    # print(scope.get_memory_depth())

    wave=scope.acquire_and_return(1)
    # plt.plot(wave.data)


    