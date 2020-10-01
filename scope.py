# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 14:47:14 2020

@author: stelt
"""
import pyvisa
import win32net
import os
import time
import shutil

class Oscilloscope():
    def __init__(self,hostname,
                 host_dirname,
                 username,
                 password,
                 set_filename=''):    

        rm=pyvisa.ResourceManager('@py')
        self.dev=rm.open_resource('TCPIP0::'+hostname+'::inst0::INSTR')
        if set_filename:
            with open(set_filename,'rb') as setfile:
                self.dev.write_binary_values(":SYST:SET ",setfile.read(), datatype='B')
                self.wait()
        self.dev.write(r':DISK:CDIR "'+host_dirname+'"')
        self.wait()
        use_dict={}
        use_dict['remote']='\\\\'+hostname+'\\'+host_dirname[3:]
        use_dict['password']=password
        use_dict['username']=username
        win32net.NetUseAdd(None, 2, use_dict)
        self.wdir=use_dict['remote']
    
    def wait(self):
        while self.dev.query(":PDER?")[1]!='1':
                    time.sleep(0.01)
    
    
    
    def single(self,filename):
        self.dev.write('*CLS;:SING')
        self.wait()
        command=':DISK:SAVE:WAV ALL,"'+filename+'",BIN,ON'
        self.dev.write(command)
        self.wait()
    
    def save_setup(self, set_filename):
        setup_bytes=self.dev.query_binary_values("*LRN?", datatype='s')[0]
        with open(set_filename,'wb') as set_file:
            set_file.write(setup_bytes)
            
    def download(self,copy_to_dir, copy_from_dir, filename_list):
        for filename in filename_list:
            src=copy_from_dir.rstrip('\\')+'\\'+filename
            dst=copy_to_dir.rstrip('\\')+'\\'+filename
            print('copying {}'.format(src))
            shutil.copyfile(src,dst)
        
    

if __name__=='__main__':

    scope=Oscilloscope('WINDOWS-E76DLEM','C:\\Shared','qwerty','qwerty')
    
    # D:\study\science\RemoteMeasures\data
    
    fname_list=os.listdir(scope.wdir)
    print(fname_list)
    """
    #
    download(r'D:\study\science\RemoteMeasures\data\2GSs',r'\\WINDOWS-E76DLEM\Shared',fname_list)
    single(dev,fname)
    """
    
