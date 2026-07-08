import numpy as np
import pickle
import matplotlib.pyplot as plt
from heterodyning.spectrograms_with_scanning_interrogator import detect_jump_by_template


file='initial_trace.pkl'
with open(file,'rb') as f:
    trace,xinc,xorigin=pickle.load(f)

times=np.arange(len(trace))*xinc+xorigin
plt.plot(times,trace)

time0=-0.0009652
window=0.0002

time1=time0-window/2
time2=time0+window/2
ind1=np.argmin(abs(times-time1))
ind2=np.argmin(abs(times-time2))

times=times[ind1:ind2]-time0
times=times[::3]
signal=trace[ind1:ind2]
signal=signal[::3]
plt.figure()
plt.plot(times,signal)

with open('strfrwd_step_signal_oscillogram.pkl','wb') as f:
    pickle.dump([times,signal],f)

t_tpl = np.asarray(times, dtype=float)
y_tpl = np.asarray(signal, dtype=float)
y_tpl0 = y_tpl - np.mean(y_tpl)
tpl_norm = np.linalg.norm(y_tpl0)
        
  
#%%

test_file='example_trace 2.pkl'
with open(file,'rb') as f:
    y_sig,xinc,xorigin=pickle.load(f)
t_sig=np.arange(len(trace))*xinc+xorigin
results=detect_jump_by_template(t_sig, y_sig, t_tpl, y_tpl0, tpl_norm,0.006)
start_time=results['jump_time']-t_tpl[0]
plt.plot(t_sig, y_sig)
plt.axvline(start_time,color='red')
plt.xlim((start_time-0.2e-3,start_time+0.2e-3))
