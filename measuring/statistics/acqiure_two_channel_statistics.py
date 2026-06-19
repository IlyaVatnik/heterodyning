# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 12:26:38 2022

@author: Артем
"""
#%%
import pyvisa
import pickle
import time
import os
from sys import stdout
import numpy as np
import scipy.signal as signal
import scipy.fft as fft
import matplotlib.pyplot as plt
import bottleneck as bn
from matplotlib.ticker import EngFormatter
import matplotlib.gridspec as gridspec

import itla
import scope
import yokogawa
import keopsys
from Hardware.APEX_OSA import APEX_OSA_with_additional_features

def spectrogram(trace, xinc=1e-6, window = 100, overlap=0):
    freq, tme, spec=signal.spectrogram(
        trace,
        1/xinc,
        window='triang',
        nperseg=window,
        noverlap=overlap,          
        #detrend=False,
        detrend='constant',
        scaling='spectrum',
        mode='magnitude')
    return tme, freq, spec

class Mode:
    def __init__(self,
                 freq_ind,
                 freq_lips,
                 freq_rips,
                 tme_ind,
                 tme_lips,
                 tme_rips):
        self.freq_ind = freq_ind
        self.freq_lips = freq_lips
        self.freq_rips = freq_rips
        self.tme_ind = tme_ind
        self.tme_lips = tme_lips
        self.tme_rips = tme_rips
        
         
def find_modes(spec, base = None,
                min_width_inds = 5,
                min_length_inds = 1,
                smooth = 20,rel_height=0.9):
    modes = []
    spec_shrinked = np.nanmax(spec, axis = 1)
    if base is not None:
        base_shrinked = np.nanmax(base, axis = 1)
        searched = spec_shrinked - base_shrinked
    else:
        searched = spec_shrinked
    smoothed = bn.move_mean(searched, smooth)
    std=bn.nanstd(smoothed)
    mode_freq_inds, mode_freq_props = signal.find_peaks(
        smoothed,
        width = min_width_inds,
        distance = min_length_inds,
        prominence = std*2,
        rel_height = rel_height)
    lines = spec[mode_freq_inds, : ]

    # plt.figure()
    # plt.plot(smoothed)
    # for i in mode_freq_inds:
        # plt.plot(i,smoothed[i],'o',color='red')
    
    for i in range(mode_freq_inds.shape[0]):
        
        line_smoothed=bn.move_mean(lines[i], smooth)
        std=bn.nanstd(line_smoothed)
        
        # plt.figure()
        # plt.plot(line_smoothed)
        
        mode_tme_inds, mode_tme_props = signal.find_peaks(
            line_smoothed,
            width = min_length_inds,
            distance = min_length_inds,
            prominence = std,
            rel_height = rel_height)
        for j in range(mode_tme_inds.shape[0]):

            md = Mode(mode_freq_inds[i],
                      mode_freq_props['left_ips'][i],
                      mode_freq_props['right_ips'][i],
                      mode_tme_inds[j],
                      mode_tme_props['left_ips'][j],
                      mode_tme_props['right_ips'][j]
                      )
            modes.append(md)

            # plt.plot([mode_tme_props['left_ips'][j],mode_tme_props['right_ips'][j]],[0,0],color='red')

    return modes

def get_data(scp4):    
    scp4.acquire()
    scp4.set_wfm_source(1)
    trace_stokes = scp4.query_wave_fast()
    scp4.set_wfm_source(4)
    trace_init = scp4.query_wave_fast()
    return  trace_stokes, trace_init

def remove_copies(modes):
    sz = len(modes)
    i = 0
    while i < sz:
        j = i + 1
        while j < sz:
            if modes[i].freq_ind == modes[j].freq_ind:
                modes.pop(j)
                sz -= 1
            else:
                j += 1
        i += 1
        
def find_pairs(f1, f4, stokes_modes, init_modes, shift, delta, gate):
    pairs = []
    for i in range(len(stokes_modes)):
        for j in range(len(init_modes)):   
            freq_stokes = f1[stokes_modes[i].freq_ind]
            freq_init = f4[init_modes[j].freq_ind]
            a = delta - freq_stokes - freq_init
            b = delta + freq_stokes + freq_init
            c = delta - freq_stokes + freq_init
            d = delta + freq_stokes - freq_init
            gap = min(abs(a - shift), abs(b - shift), abs(c - shift), abs(d - shift))
            if gap < gate:
                pairs.append([freq_stokes, freq_init])  
    return pairs

def single_stokes_number(scp, iterations, shift, delta, gate):
    counter = 0 
    for i in range(iterations): 
        #scp.acquire()
        scp.acquire(sleep_step = 2)
        scp.set_wfm_source(1)
        trace_stokes = scp4.query_wave_fast()
        scp.set_wfm_source(4)
        trace_init = scp.query_wave_fast()
        t1, f1, s1 = spectrogram(trace_stokes.data, trace_stokes.xinc, window=10**4)
        t4, f4, s4 = spectrogram(trace_init.data, trace_init.xinc, window=10**4)
        stokes_modes = find_modes(s1, None)
        remove_copies(stokes_modes)
        init_modes = find_modes(s4, None)
        remove_copies(init_modes)
        pairs = find_pairs(f1, f4, stokes_modes, init_modes, shift, delta, gate) 
        counter += len(pairs)
        print('found {}'.format(len(pairs)))
    return counter

def multi_stokes(wl4, scp, stokes_number, step, gate, iterations):
    freq4 = itla.m_Hz(wl4)
    las4.off()
    las4.set_frequency(freq4)
    las4.on()
    time.sleep(60)
    las4.mode('whisper')
    time.sleep(30)
    counters = []
    print('l4 ready')
    for i in range (stokes_number):
        las3.off()
        las3.set_frequency(freq4 - step * (i + 1))
        las3.on()
        time.sleep(60)
        try:
            las3.mode('no dither')
        except:
            time.sleep(10)
            las3.mode('no dither')
        time.sleep(30)
        pieces_num = iterations // 100
        count = 0
        print('l3 ready')
        
        for i in range(pieces_num):
            while True:
                spectrum=OSA.acquire_spectrum()
                peaks_ind, _ = signal.find_peaks(spectrum[1], height = (-10, 10), threshold=None)
                peaks_x = [spectrum[0][j] for j in peaks_ind]
                delta = peaks_x[1] - peaks_x[0]
                if delta > 1:
                    delta = delta * 1e9
                    break
            count += single_stokes_number(scp, 100, step * (i + 1), delta, gate)
        while True:
            spectrum=OSA.acquire_spectrum()
            peaks_ind, _ = signal.find_peaks(spectrum[1], height = (-10, 10), threshold=None)
            peaks_x = [spectrum[0][j] for j in peaks_ind]
            delta = peaks_x[1] - peaks_x[0]
            if delta > 1:
                delta = delta * 1e9
                break
        count += single_stokes_number(scp, iterations % 100, step * (i + 1), delta, gate)
        counters.append(count)
    return counters
# hardware initializtion

'''
Connect all devices
'''
#%%
pump = keopsys.Keopsys('10.2.60.244')

las3 = itla.PPCL550(3)
las4 = itla.PPCL550(4)


#scp4 = scope.Scope(host='WINDOWS-E76DLEM', protocol = 'hislip0', timeout = 5000) # 4GHz
#scp4 = scope.Scope(host='WINDOWS-E76DLEM', protocol = 'inst0', timeout = 5000)


scp4 = scope.Scope(host='WINDOWS-B46M432', protocol = 'inst0', timeout = 5000)

trace_points=8e6
scp4.macro_setup(
            mode = 'RTIMe',
            wave_byteorder = 'MSBF',
            wave_format = 'WORD', 
            wave_view = 'ALL', # ALL for full data, MAIN for display drawn data
            streaming = 'ON',
            header = 'OFF',
            
            channels_displayed = (1, 4),
            channels_coupling = {1:'DC50', 4:'DC50'},
            average_count = 0, # if 0 - no average
            trace_points = trace_points, # if 0 - minimum  HEre was 20.5e6 Here
            sampling_rate = 20e9, # if 0 - minimum
            trigger = 'TRIG')

#scp4.SRQEnable()

OSA = APEX_OSA_with_additional_features('10.2.60.25')
OSA.SetScaleXUnit(ScaleXUnit=1)
OSA.change_range(1550,1551.5)
OSA.SetWavelengthResolution('High')
OSA.SetScaleXUnit(ScaleXUnit=0) #highres only
spectrum=OSA.acquire_spectrum()
# hardware setup
#%%
'''

number_of_stokes=3

shift_between_lasers=10.8e9*number_of_stokes
#freq3 = itla.m_Hz(wl3)
wl4 = 1550.568e-9 #no balance
freq4 = itla.m_Hz(wl4)
freq3 = freq4 - shift_between_lasers
wl3 = itla.m_Hz(freq3)

las3.set_frequency(freq3)
las4.set_frequency(freq4)

las3.set_power(1600)
las4.set_power(1600)

pump_power=298
pump.set_power(pump_power)

'''


#!!!
# laser start
#%%

las3.on()
las4.on()

time.sleep(120)

las3.mode('no dither')
las4.mode('whisper')
pump.APCon()

#
#counters = multi_stokes(wl4, scp4, 3, 10.8e9, 0.3e9, 10)

#
#%%

###############################################################################

#%%
# while True:
#     spectrum=OSA.acquire_spectrum()
#     peaks_ind, _ = signal.find_peaks(spectrum[1], height = (-10, 10), threshold=None)
#     peaks_x = [spectrum[0][j] for j in peaks_ind]
#     delta = peaks_x[1] - peaks_x[0]
#     if delta > 1:
#         delta = delta * 1e9
#         break
"""    
iterations = 100
counter = 0 
shift = 10.8e9
gate = 0.2e9
for i in range(iterations):
    scp4.SRQAcquire()
    #scp4.acquire()
    scp4.set_wfm_source(1)
    trace_stokes = scp4.query_wave_fast()
    scp4.set_wfm_source(4)
    trace_init = scp4.query_wave_fast()
    t1, f1, s1 = spectrogram(trace_stokes.data, trace_stokes.xinc, window=10**4)
    t4, f4, s4 = spectrogram(trace_init.data, trace_init.xinc, window=10**4)
    stokes_modes = find_modes(s1, None, 5, 10, 10)
    remove_copies(stokes_modes)
    init_modes = find_modes(s4, None, 5, 10, 10)
    remove_copies(init_modes)
    pairs = find_pairs(stokes_modes, init_modes, shift, delta, gate) 
    counter += len(pairs)
    print('found {}'.format(len(pairs)))
"""    
###############################################################################
#%%
N_of_rounds = 30
N_in_round=10
gate = 0.4e9
numbers_of_stokes=range(1,6,1)
wl4 = 1551.568e-9 #no balance
las3.off()
las4.off()
las3.set_power(1600)
las4.set_power(1600)
pump_power=298
pump.set_power(pump_power)

OSA.SetScaleXUnit(ScaleXUnit=1)
OSA.change_range(wl4*1e9-0.1,wl4*1e9+1.2)
OSA.SetWavelengthResolution('High')
OSA.SetScaleXUnit(ScaleXUnit=0) #highres only


for number_of_stokes in numbers_of_stokes:
    print('number_of_stokes=',number_of_stokes)
    count = 0
    shift_between_lasers=10.8e9*number_of_stokes
    
    freq4 = itla.m_Hz(wl4)
    freq3 = freq4 - shift_between_lasers
    wl3 = itla.m_Hz(freq3)
    
    las3.set_frequency(freq3)
    las4.set_frequency(freq4)
    
    las3.on()
    las4.on()
    print('lasers are on')
    error=True
    while error:
        try: 
            las3.mode('no dither')
            error=False
            print( 'las3 set to no dither')
        except:
            pass
    error=True
    while error:
        try: 
            las4.mode('whisper')
            error=False
            print( 'las4 set to whisper')
        except:
            pass
    
    
    shift = shift_between_lasers
    
    print('pump is ON with ',pump.APCon())
    
    
    
    time.sleep(5)
    
    for i in range(N_of_rounds):
        while True:
            spectrum=OSA.acquire_spectrum()
            peaks_ind, _ = signal.find_peaks(spectrum[1], height = (-10, 10), threshold=None,distance=100)
            peaks_x = [spectrum[0][j] for j in peaks_ind]
            if len(peaks_x)>1:
                delta = peaks_x[1] - peaks_x[0]
                if delta > 1:
                    delta = delta * 1e9
                    break
        print('delta={}'.format(delta))
        count += single_stokes_number(scp4, N_in_round, shift, delta, gate)
        print(count/((i+1) * N_in_round))
        print('{} ready'.format(i + 1))
        with open('number_of_stokes={} pump={} wavelength={}.txt'.format(number_of_stokes,pump_power, wl4), 'a') as the_file:
            the_file.write('{}, {}, {}\n'.format((i+1) * N_in_round, count,count/((i+1) * N_in_round)))
    pump.APCoff()
    print('pump is off')
    las3.off()
    las4.off()
    print('lasers are off')


###############################################################################
#%%
'''
Statistics for one laser
'''

N_of_rounds = 50
N_in_round=10
wl4 = 1550e-9 #no balance
wavelengths=wl4+np.arange(0,2,0.1)*1e-9

las4.off()
las4.set_power(1600)
pump_power=298
pump.set_power(pump_power)

try:
    for wavelength in wavelengths:
        print('wavelength=',wavelength*1e9)
        count = 0
        freq4 = itla.m_Hz(wl4)
        
        las4.set_frequency(freq4)
        
        
        las4.on()
        print('laser is on')
    
        error=True
        while error:
            try: 
                las4.mode('whisper')
                error=False
                print( 'las4 set to whisper')
            except:
                pass
        
       
        print('pump is ON with ',pump.APCon())
        
        
        
        time.sleep(5)
        
        for i in range(N_of_rounds):
            scp4.acquire(sleep_step = 2)
            scp4.set_wfm_source(4)
            trace = scp4.query_wave_fast()
            t1, f1, s1 = spectrogram(trace.data, trace.xinc, window=10**4)
            modes = find_modes(s1, None)
            remove_copies(modes)
            count += len(modes)
            print('{} modes are found'.format(len(modes)),count/((i+1) * N_of_rounds))
            with open('wavelength={} pump={}.txt'.format(wavelength*1e9,pump_power, wl4), 'a') as the_file:
                the_file.write('{}, {}, {}\n'.format((i+1) * N_of_rounds, count,count/((i+1) * N_of_rounds)))
        pump.APCoff()
        print('pump is off')
        las4.off()
        print('lasers are off')
except Exception as e:
    print(e, ' ERROR!')
    pump.APCoff()
    print('pump is off')
    las4.off()
    print('lasers are off')
    
#%%                
cutoff = 100
number_of_stokes=0
plt.clf()
#scp4.acquire()
#scp4.SRQAcquire()

# while True:
#     spectrum=OSA.acquire_spectrum()
#     peaks_ind, _ = signal.find_peaks(spectrum[1], height = (-10, 10), threshold=None,distance=100)
#     peaks_x = [spectrum[0][j] for j in peaks_ind]
#     if len(peaks_x)>1:
#         delta = peaks_x[1] - peaks_x[0]
#         if delta > 1:
#             delta = delta * 1e9
#             break
        
        
scp4.acquire(sleep_step = 2)
scp4.set_wfm_source(1)
trace_stokes = scp4.query_wave_fast()
scp4.set_wfm_source(4)
trace_init = scp4.query_wave_fast()


#trace_stokes, trace_init = get_data(scp4)
t1, f1, s1 = spectrogram(trace_stokes.data, trace_stokes.xinc, window=10**4)
t4, f4, s4 = spectrogram(trace_init.data, trace_init.xinc, window=10**4)
print('spectrograms created')




#"""
fig, ax = plt.subplots(2, sharex = True, sharey=True)
ax[0].pcolorfast(t1, f1[cutoff:], s1[cutoff:,:], cmap='jet')
ax[0].set_title('stokes')
ax[1].pcolorfast(t4, f4[cutoff:], s4[cutoff:,:], cmap='jet')
ax[1].set_title('init')
#"""

"""
###
fig, ax = plt.subplots(2, sharex = True, sharey=True)
ax[0].pcolorfast(t1, f1[:], s1[:,:], cmap='jet')
ax[0].set_title('stokes')
ax[1].pcolorfast(t4, f4[:], s4[:,:], cmap='jet')
ax[1].set_title('init')
###
"""

stokes_modes = find_modes(s1, None)
init_modes = find_modes(s4, None)
remove_copies(stokes_modes)
remove_copies(init_modes)

for mode in stokes_modes:
    ax[0].plot([t1[int(mode.tme_lips)], t1[int(mode.tme_rips)]], [f1[int(mode.freq_ind)], f1[int(mode.freq_ind)]], color = 'red')
for mode in init_modes:
    ax[1].plot([t4[int(mode.tme_lips)], t4[int(mode.tme_rips)]], [f4[int(mode.freq_ind)], f4[int(mode.freq_ind)]], color = 'red')

shift = 10.8e9*number_of_stokes
delta=0
pairs = find_pairs(f1, f4, stokes_modes, init_modes, shift, delta, 0.3e9) 
print(pairs)
with open('s1.pkl','wb') as f: pickle.dump([t1,f1,s1],f)
with open('s4.pkl','wb') as f: pickle.dump([t4,f4,s4],f)

#%%
pump.APCoff()
las3.off()
las4.off()

#%%


