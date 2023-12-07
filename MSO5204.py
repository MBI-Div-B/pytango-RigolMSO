#!/usr/bin/env python3
#

import pyvisa
#import easy_scpi as scpi
import time
import numpy as np

class channel():
    def __init__(self, N):
        self.channum = N
        self.active = False
        self.data = []
        self.bgstart = 0
        self.bgend = 100
        self.signalstart = 200
        self.signalend = 1000
        self.ave = 0.0 #stores background-corrected integral over signal range in Vs; named ave[rage] for historic reasons.
        self.inc = 0.1
        self.bgave = 0.0

    def update_channel(self):
        if (len(self.data)>0) and self.active:
            if self.bgstart<0:
                self.bgstart = 0
            if self.bgend >len(self.data):
                self.bgend = len(self.data)
            if self.signalstart < 0:
                self.signalstart = 0
            if self.signalend > len(self.data):
                self.signalend = len(self.data)
            self.bgave = np.average(self.data[self.bgstart:self.bgend])
            d = self.data - self.bgave
            dt = (self.signalend-self.signalstart)*self.inc
            self.ave = np.sum(d[self.signalstart:self.signalend])*dt  
            #np.average(self.data[self.signalstart:self.signalend])-np.average(self.data[self.bgstart:self.bgend])
        else:
            self.avg = 0.0

class Rigol_Oscilloscope():
    def __init__(self, IP):
        __rm = pyvisa.ResourceManager()
        dev = f"TCPIP::{IP}::INSTR"
        self.inst = __rm.open_resource(dev)
        res = str(self.inst.query("*IDN?"))
        print(res)
        if "RIGOL" in res:
            print('Device found at address '+dev)
            self.inst.write(":COUN:MODE TOT")
            self.inst.write(":COUN:TOT:ENAB ON")
            self.inst.write(":ACQ:TYPE NORM")
            self.inst.write(":ACQ:TYPE AVER")            
            self.avrg = self.inst.query(":ACQ:AVER?")
            self.inst.write(":COUN:TOT:CLE")
            self.channel = np.array([channel(1),channel(2),channel(3),channel(4)])
            self.get_active_channels()
            self.configure_channels()

    def get_active_channels(self):
        self.activechannels = []
        for i in [1,2,3,4]:
            self.channel[i-1].active = False
            if int(self.inst.query(f":CHAN{i}:DISP?"))==1:
                self.activechannels.append(f"CHAN{i}")
        for c in self.activechannels:
            self.channel[int(c[4])-1].active = True
    
    def configure_channels(self):
        for channel in self.activechannels:
            self.inst.write(f":WAV:SOUR {channel}")
            self.inst.write(":WAV:MODE NORM")
            self.inst.write(":WAV:FORM ASCII")
            self.inst.write(":WAV:POIN 1000")
            self.channel[int(channel[4])-1].inc = float(self.inst.query(":WAV:XINC?"))
            
    
    def measure(self):
        ### reset averages ###
        self.inst.write(":ACQ:TYPE NORM") 
        self.inst.write(":ACQ:TYPE AVER")            

        ### clear counter ###
        self.inst.write(":COUN:TOT:CLE")

        ### wait for counter to reach desired number of averages ###
        curr = self.inst.query(":COUN:CURR?")
        while curr < self.avrg:
            time.sleep(0.03)
            curr = self.inst.query(":COUN:CURR?")

        ### update data of all channels
        self.get_active_channels()
        self._read_all_channels()
        self.totals()

    def get_channel(self,channel):
        self._read_channel(channel)
        return self.channel[channel-1].data

    def get_channel_integral(self,channel):
        return self.channel[channel-1].ave

    def totals(self):
        tot = []
        for chan in self.channel:
            if chan.active:
                chan.update_channel()
                tot.append(chan.ave)
            else:
                tot.append(0.0)
        return tot
        
    def _read_channel(self, channel):
        if f"CHAN{channel}" in self.activechannels:
            self.inst.write(f":WAV:SOUR CHAN{channel}")
            data = self.inst.query(":WAV:DATA?")
            wavebytes = int(data[2:11])
            wavedata = (data[11:wavebytes+11]).split(",")
            wavedata = [float(dat) for dat in wavedata[:-1]]
            self.channel[channel-1].data = wavedata
            self.channel[channel-1].update_channel()
            return wavedata
        #else:
        #    print(f"Channel {channel} is not active")
    
    def _read_all_channels(self):
        for i in [1,2,3,4]:
            self._read_channel(i)

    def single_acquisition(self):
        self.inst.write(":SING")

    def activate_channel(self,channel):
        self.inst.write(f":CHAN{channel}:DISP 1")
        self.get_active_channels()
        self._read_channel(channel)

    def deactivate_channel(self,channel):
        self.inst.write(f":CHAN{channel}:DISP 0")
        self.get_active_channels()

    def set_averages(self,value):
        if value in [1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536]:
            self.inst.write(f":ACQ:AVER {value}")
            time.sleep(0.1)
            self.avrg = self.inst.query(":ACQ:AVER?")
            
    def set_ranges(self,channel, bgstart, bgend, signalstart, signalend):
        self.channel[channel-1].bgstart = bgstart
        self.channel[channel-1].bgend = bgend
        self.channel[channel-1].signalstart = signalstart
        self.channel[channel-1].signalend = signalend

    def get_ranges(self,channel):
        bgstart = self.channel[channel-1].bgstart 
        bgend = self.channel[channel-1].bgend
        signalstart = self.channel[channel-1].signalstart
        signalend = self.channel[channel-1].signalend        
        return [bgstart, bgend, signalstart, signalend]





