import numpy as np
import matplotlib.pyplot as plt

file_names=['Rigol MSO8104 1 MOm.txt','Rigol MSO8104 50 Om.txt',
            'InGaAs_Balanced_Photorecelver_PNKY_BPRM_20G_I_FA_SN221731255.txt',
            'InGaAs_Balanced_Photorecelver_PNKY_BPRM_20G_I_FA_SN221731254.txt']

plt.figure()
for file in file_names:
    data=np.genfromtxt(file,delimiter='\t',skip_header=2)
    plt.plot(data[:,0],data[:,1],label=file)
plt.xlabel('Frequcency, MHz')
plt.ylabel('Response')
plt.legend()
plt.tight_layout()