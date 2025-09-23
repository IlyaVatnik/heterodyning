# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 19:48:14 2021

@author: stelt
"""

# <host>/cgi/sendrs232Direct.cgi

import requests


class Keopsys:
    def __init__(self, host='10.2.60.244'):
        self.command_url = 'http://' + host + '/cgi/sendrs232Direct.cgi'
        self.mode='power'
        
    def command(self, command):
        return requests.post(self.command_url, command).text
    
    def APCon(self):
        if self.mode=='power':
            result=self.command('ASS=2')
        elif self.mode=='current':
            result=self.command('ASS=1')
        print('Pump is on')
        return result
    
    def APCoff(self):
        result= self.command('ASS=0')
        print('Pump is off')
        return result

    def set_power(self, pwr):
        if pwr<270:
            print('Error. Power {} too small to be set with this Keopsys laser'.format(pwr/10))
        result= self.command('SOP={}'.format(pwr)) #dBm * 10
        print('Pump power is set to {}'.format(pwr))
        return result

    def set_current(self, c):
        return self.command('IC2={}'.format(c)) #dBm * 10
    
    def get_current(self):
        return self.command('ID2?') #dBm * 10

    def actual_pwr(self):
        return self.command('OPW?') #dBm * 10
    
    def set_control_mode(self,mode:str):
        self.mode=mode


if __name__ == '__main__':
    
    kek = Keopsys('10.2.60.244')
    
    print(kek.command('SOP?'))
    print(kek.get_current())
