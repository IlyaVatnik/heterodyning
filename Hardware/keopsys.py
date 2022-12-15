# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 19:48:14 2021

@author: stelt
"""

# <host>/cgi/sendrs232Direct.cgi

import requests


class Keopsys:
    def __init__(self, host='10.2.60.227'):
        self.command_url = 'http://' + host + '/cgi/sendrs232Direct.cgi'
        self.mode='power'
        
    def command(self, command):
        return requests.post(self.command_url, command).text
    
    def APCon(self):
        if self.mode=='power':
            return self.command('ASS=2')
        elif self.mode=='current':
            return self.command('ASS=1')
    
    def APCoff(self):
        return self.command('ASS=0')

    def set_power(self, pwr):
        return self.command('SOP={}'.format(pwr)) #dBm * 10

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
