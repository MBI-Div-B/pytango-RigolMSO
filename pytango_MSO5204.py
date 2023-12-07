#!/usr/bin/env python3
#

import sys
import os
import time
from enum import IntEnum
import numpy as np
from matplotlib import pyplot as plt

from tango import AttrQuality, AttrWriteType, DispLevel, DevState, DebugIt
from tango.server import Device, attribute, command, pipe, device_property

from MSO5204 import Rigol_Oscilloscope

class MSO5204(Device):

    # -----------------
    # Device Properties
    # -----------------

    IP = device_property(dtype='DevString', default_value = '192.168.1.176')

    # ----------
    # Attributes
    # ----------
    
    """The oscilloscope acquires traces of 1000 data points. Within the trace, 
    regions can be defined for the signal and background. 
    
    chan1regions contains start and endpoint of the background and signal regions for channel 1 in the format [background start, background end, signal start, signal end]. 

    chan1avg contains the background corrected signal average. 

    Configuration of the regions is best done using pytango: 
    import pytango
    mso = tango.DeviceProxy('XXX/YYYY/ZZZ')
    mso.chan1regions = [...4 integers between 0 and 1000...]"""

    averages = attribute(dtype = 'DevEnum',
        label = '# of averages',
        enum_labels = ['1','2','4','8','16','32','64','128','256','512','1024','2048','4096','8192','16384','32768','65536'],
        access = AttrWriteType.READ_WRITE,)


    chan1regions = attribute(dtype=(int,),
        max_dim_x = 4,
        access = AttrWriteType.READ_WRITE,) #[background start, background end, signal start, signal end]

    chan1snapshot = attribute(dtype=(float,),
        max_dim_x = 1000,
        access = AttrWriteType.READ,)

    chan1int = attribute(
        dtype='DevFloat',
        access=AttrWriteType.READ,
        label="Channel 1",
        unit="Vs",
        format="%4.3E",
        doc = 'background-corrected integral over the signal range',)
    
    chan1active = attribute(
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE,
        label="Display Channel 1",)
    
    chan2regions = attribute(dtype=(int,),
        max_dim_x = 4,
        access = AttrWriteType.READ_WRITE,) #[background start, background end, signal start, signal end]

    chan2snapshot = attribute(dtype=(float,),
        max_dim_x = 1000,
        access = AttrWriteType.READ,)

    chan2int = attribute(
        dtype='DevFloat',
        access=AttrWriteType.READ,
        label="Channel 2",
        unit="Vs",
        format="%4.3E",
        doc = 'background-corrected integral over the signal range',)
    
    chan2active = attribute(
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE,
        label="Display Channel 2",)

    chan3regions = attribute(dtype=(int,),
        max_dim_x = 4,
        access = AttrWriteType.READ_WRITE,) #[background start, background end, signal start, signal end]

    chan3snapshot = attribute(dtype=(float,),
        max_dim_x = 1000,
        access = AttrWriteType.READ,)

    chan3int = attribute(
        dtype='DevFloat',
        access=AttrWriteType.READ,
        label="Channel 3",
        unit="Vs",
        format="%4.3E",
        doc = 'background-corrected integral over the signal range',)
    
    chan3active = attribute(
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE,
        label="Display Channel 3",)

    chan4regions = attribute(dtype=(int,),
        max_dim_x = 4,
        access = AttrWriteType.READ_WRITE,) #[background start, background end, signal start, signal end]

    chan4snapshot = attribute(dtype=(float,),
        max_dim_x = 1000,
        access = AttrWriteType.READ,)

    chan4int = attribute(
        dtype='DevFloat',
        access=AttrWriteType.READ,
        label="Channel 4",
        unit="Vs",
        format="%4.3E",
        doc = 'background-corrected integral over the signal range',)
    
    chan4active = attribute(
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE,
        label="Display Channel 4",)

    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        Device.init_device(self)
        self.device = Rigol_Oscilloscope(self.IP)
        self.avs = np.array([1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536])
        self._find_first_active()
        self.set_state(DevState.ON)

    # ------------------
    # Attributes methods
    # ------------------
    
    ### READ COMMANDS ###

    def read_averages(self):
        res = np.ones(17)*int(self.device.avrg)
        return int(np.sum(np.arange(17)*(self.avs == res)))

    def read_chan1regions(self):
        return self.device.get_ranges(1)

    def read_chan1int(self):
        if self._first_active == 1:
            self.measure()
        return self.device.get_channel_integral(1)
    def read_chan1active(self):
        return ("CHAN1" in self.device.activechannels)
    def read_chan1snapshot(self):
        if "CHAN1" in self.device.activechannels:
            return self.device.get_channel(1)
        else:
            return np.zeros(1000)

    def read_chan2regions(self):
        return self.device.get_ranges(2)

    def read_chan2int(self):
        if self._first_active == 2:
            self.measure()
        return self.device.get_channel_integral(2)
    def read_chan2active(self):
        return ("CHAN2" in self.device.activechannels)
    def read_chan2snapshot(self):
        if "CHAN2" in self.device.activechannels:
            return self.device.get_channel(2)
        else:
            return np.zeros(1000)

    def read_chan3regions(self):
        return self.device.get_ranges(3)

    def read_chan3int(self):
        if self._first_active == 3:
            self.measure()
        return self.device.get_channel_integral(3)
    def read_chan3active(self):
        return ("CHAN3" in self.device.activechannels)
    def read_chan3snapshot(self):
        if "CHAN3" in self.device.activechannels:
            return self.device.get_channel(3)
        else:
            return np.zeros(1000)

    def read_chan4regions(self):
        return self.device.get_ranges(4)

    def read_chan4int(self):
        if self._first_active == 4:
            self.measure()
        return self.device.get_channel_integral(4)
    def read_chan4active(self):
        return ("CHAN4" in self.device.activechannels)
    def read_chan4snapshot(self):
        if "CHAN4" in self.device.activechannels:
            return self.device.get_channel(4)
        else:
            return np.zeros(1000)

    ### WRITE COMMANDS ###

    def write_averages(self,value):
        self.device.set_averages(int(2**value))

    def write_chan1active(self,value):
        if value:
            self.device.activate_channel(1)
        else:
            self.device.deactivate_channel(1)
        self._find_first_active()

    def write_chan1regions(self, value):
        self.device.set_ranges(1, value[0], value[1], value[2], value[3])

    def write_chan2active(self,value):
        if value:
            self.device.activate_channel(2)
        else:
            self.device.deactivate_channel(2)
        self._find_first_active()

    def write_chan2regions(self, value):
        self.device.set_ranges(2, value[0], value[1], value[2], value[3])

    def write_chan3active(self,value):
        if value:
            self.device.activate_channel(3)
        else:
            self.device.deactivate_channel(3)
        self._find_first_active()

    def write_chan3regions(self, value):
        self.device.set_ranges(3, value[0], value[1], value[2], value[3])

    def write_chan4active(self,value):
        if value:
            self.device.activate_channel(4)
        else:
            self.device.deactivate_channel(4)
        self._find_first_active()

    def write_chan4regions(self, value):
        self.device.set_ranges(4, value[0], value[1], value[2], value[3])

    @command(doc_in="measure and update all channels")
    def measure(self):
        self.device.measure()

    @command(dtype_in=(float,), doc_in="declare measurement regions. Five values [channel, bgstart, bgend, signalstart, signalend]")
    def declare_regions(self,value):
        print(value)
        cha, bgs, bge, sigs, sige = value
        reg = np.array([bgs, bge, sigs, sige])
        if int(cha) == 1:
            self.write_chan1regions(reg)
        elif int(cha) == 2:
            self.write_chan2regions(reg)
        elif int(cha) == 3:
            self.write_chan3regions(reg)
        elif int(cha) == 4:
            self.write_chan4regions(reg)
    
    def _find_first_active(self):
        if self.read_chan1active():
            self._first_active = 1
        elif self.read_chan2active():
            self._first_active = 2        
        elif self.read_chan3active():
            self._first_active = 3
        elif self.read_chan4active():
            self._first_active = 4

if __name__ == "__main__":
    MSO5204.run_server()

