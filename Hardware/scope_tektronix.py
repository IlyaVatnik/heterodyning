# -*- coding: utf-8 -*-


__version__ = '1'
__date__ = '2025.08.14'


import pyvisa as visa
import numpy as np
from struct import unpack

# TO RUN THIS YOU NEED TO:
# HAVE VISA TEKTRONIX LIBRARY INSTALLED (OR TO PUT PATH TO THE DLL INTO SYSPATH)
# HAVE PYVISA PYTHON PACKAGE INSTALLED
# MATCH PYTHON BIT VERSION WITH YOUR VISA'S (x64 WITH x64 OR x32 WITH x32)
# ACTIVATE SERVER ON YOUR OSCILLOSCOPE (UTILITIES->LAN SERVER STATUS) (OR TO TURN IT ON IN TekVISA LAN SERVER CONTROL IN WINDOWS APP)
# SET HORIZONTAL MODE TO MANUAL (Horiz/Acq->Horizontal modes)

# Tektronix DPO7254
class scope():
	# When you init this class, connection is established
	def __init__(self, ip = '10.0.156.21', channel = '4', full_address = None):
		self.rm = visa.ResourceManager()
		try:
			if not full_address	is None:
				self.scope = self.rm.open_resource(full_address)
			else:
				self.scope = self.rm.open_resource('TCPIP0::' + ip + '::inst0::INSTR')
			#self.channel = channel
		except Exception as e:
			print(e)
			print('No device found. Specify ip, channel or full_address. Devices registered in the system:')
			self.rm.list_resources()
			exit(0)
		self.samples_per_sec = None
		self.sec_per_div = None

		self.set_channel(channel)
		#self.scope.write('DATA:SOU CH' + self.channel)
		# self.scope.write("HORizontal:MODE MANual")
		self.scope.write("DATa:STARt 1")
		self.scope.write("DATa:STOP 10000000000")

		# self.set_samples_per_sec(6.25e9)
		# self.set_sec_per_div(2e-6)
		# self.set_sec_per_div(16e-9)

		print(self.__class__.__name__, 'inited!')
	
	def __del__(self):
		pass

	def set_channel(self, channel):
		self.channel = channel
		self.scope.write('DATA:SOU CH' + self.channel)

	def set_samples_per_sec(self, value):
		self.samples_per_sec = value
		self.scope.write("HORizontal:MODE:SAMPLERate " + str(self.samples_per_sec))

	def set_sec_per_div(self, value):
		if not self.samples_per_sec	 is None:
			self.sec_per_div = value * 2
			s_period = 2 / self.samples_per_sec
			print(s_period)
			rec_len = round(self.sec_per_div * 10 / s_period)
			print(rec_len)
			self.scope.write("HORizontal:MODE:RECOrdlength " + str(rec_len))
		else:
			Exception('First specify samplerate')

	def get_waveform_setup(self):
		self.scope.write('DATA:WIDTH 1')
		self.scope.write('DATa:ENCdg RPBinary')
		recLen = self.scope.query("horizontal:recordlength?")
		Hscale = float(self.scope.query("HOR:SCA?"))
		HDelay = float(self.scope.query("HORizontal:DELay:TIMe?"))
		HPos = float(self.scope.query("HORIZONTAL:POSITION?"))
		xincr = float(self.scope.query("wfmo:xincr?"))
		ymult = float(self.scope.query("wfmo:ymult?"))
		yoff = float(self.scope.query("wfmo:yoff?"))
		yzero = float(self.scope.query("wfmo:yzero?"))
		return recLen,  HPos, xincr, HDelay, yoff, ymult, yzero

	def get_waveform(self):
		''' Returns X and Y separatly in the form of numpy arrays'''
		[recLen,  HPos, xincr, HDelay, yoff, ymult, yzero] =  self.get_waveform_setup()
		recLenNumBytes = len(recLen)
		self.scope.write('curve?')
		wave= self.scope.read_raw()
		headerlen = 2 + recLenNumBytes
		header = wave[:headerlen]
		ADC_wave = wave[headerlen:-1]
		ADC_wave = np.array(unpack('%sB' % len(ADC_wave),ADC_wave))
		volt = ((ADC_wave-yoff) * ymult) + yzero
		time = np.arange(0, xincr*len(volt), xincr)
		return time, volt

	def get_osc(self):
		return self.get_waveform()
    #%%
if __name__ == '__main__':
    sc=scope('10.2.60.150')
    [t,s]=sc.get_waveform()
    import matplotlib.pyplot as plt
    plt.figure()
    print(len(t))
    plt.plot(t,s)