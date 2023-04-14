import pickle
import matplotlib.pyplot as plt
import numpy as np





def plot_powers(file):

    def dBm2W(x):
        return 10**(x/10)/1000
    
    
    def W2dBm(x):
        return 10*np.log10(1000*x)
    
    with open(file,'rb') as f:
        [pumps,outputs]=pickle.load(f)
    pumps=dBm2W(pumps/10)
    plt.figure()
    plt.plot(pumps, outputs)
    
    
    plt.xlabel('Pump power, W')
    plt.ylabel('Generation power, W')
    secax = plt.gca().secondary_xaxis('top', functions=(W2dBm,dBm2W))
    secax.set_xlabel('Pump power, dBm')
    
    
if __name__=="__main__":
    file='powers.pkl'
    plot_powers(file)