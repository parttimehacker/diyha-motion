#!/usr/bin/python3
""" DIYHA MQTT location initializer """

# The MIT License (MIT)
#
# Copyright (c) 2019 parttimehacker@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import time
import datetime
import socket
import board
import busio

from adafruit_ht16k33.segments import Seg7x4, NUMBERS

import logging
import logging.config

# Seven Segment LED modes

TIME_MODE = 0
WHO_MODE = 1

# time display digit index into NUMBERS

DIGIT0 = [0,1,2]
DIGIT1 = [0,1,2,3,4,5,6,7,8,9]
DIGIT2 = [0,1,2,3,4,5]
DIGIT3 = [0,1,2,3,4,5,6,7,8,9]

class TimeDisplay:
    """ display time """

    def __init__(self, display, logger):
        """ initialize special feature and display format """
        self.display = display
        self.logger = logger
        self.colon = False
        self.alarm = 0
        self.time_format = 12
        self.last_minute = 99
        
    def activate(self,format):
        self.last_minute = 99
        self.time_format = format

    def update(self,):
        """ display 3 digits of ip address """
        now = datetime.datetime.now()
        if now.minute != self.last_minute:
            self.last_minute = now.minute
            try:
                self.display.fill(0)
            except Exception as e:
                self.logger.error("Exception occurred", exc_info=True)
            # write hour digits based on mode and am/pm bit
            hr = now.hour
            pm = 0
            if self.time_format == 12:
                if hr >= 12:
                    pm = 0b10000000
                if hr > 12:
                    hr -= 12
                d0 = hr // 10
                if d0 > 0:
                    idx = NUMBERS[d0]
                try:
                    self.display.set_digit_raw(0,idx)
                except Exception as e:
                    self.logger.error("Exception occurred", exc_info=True)
            else:
                d0 = hr // 10
                idx = NUMBERS[d0]
                try:
                    self.display.set_digit_raw(0,idx)
                except Exception as e:
                    self.logger.error("Exception occurred", exc_info=True)
            # write out second digit of hour regardless of mode
            d1 = hr % 10
            idx = NUMBERS[d1]
            idx1 = idx | pm
            # write minuetes
            d2 = now.minute // 10
            idx2 = NUMBERS[d2]
            d3 = now.minute % 10
            idx3 = NUMBERS[d3]
            idx3 = idx3 | self.alarm
            try:
                self.display.set_digit_raw(1,idx1)
                self.display.set_digit_raw(2,idx2)
                self.display.set_digit_raw(3,idx3)
            except Exception as e:
                self.logger.error("Exception occurred", exc_info=True)
        try:
            self.display.colon = self.colon
            if self.colon:
                self.colon = False
            else:
                self.colon = True
            self.display.show()
        except Exception as e:
            self.logger.error("Exception occurred", exc_info=True)
        
class WhoDisplay:
    """ display IP address in who mode """

    def __init__(self, display, logger):
        """ prepare to show ip address on who message """
        self.display = display
        self.logger = logger
        self.iterations = 0
        default = "0.0.0.0"
        self.ip_address = default.split(".")
        
    def activate(self,):
        self.iterations = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        host_ip = sock.getsockname()[0]
        sock.close()
        self.ip_address = host_ip.split(".")

    def update(self,):
        """ display 3 digits of ip address """
        print("who.updae() "+self.ip_address[self.iterations])
        try:
            self.display.fill(0)
            self.display.brightness = 1.0
            self.display.print(self.ip_address[self.iterations])
            self.iterations += 1
            if self.iterations >= 4:
                self.iterations = 0
            self.display.show()
        except Exception as e:
            self.logger.error("Exception occurred", exc_info=True)

class SevenSegmentHAL:
    """ Hardware abstraction layer for seven segment LED backpack HT16K33
    """

    def __init__(self, logging_file):
        """ Initialize device and class defaults """
        logging.config.fileConfig(fname=logging_file, disable_existing_loggers=False)
        # Get the logger specified in the file
        self.logger = logging.getLogger(__name__)
        # Create the I2C interface. Auto write is false device show() required
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.display = Seg7x4(i2c, auto_write=False)
        except Exception as e:
            self.logger.error("SSH Init Exception: ", exc_info=True)
            raise IOError
            
        self.set_brightness(1.0)
        self.display_mode = TIME_MODE
        self.time_format = 12
        self.clock = TimeDisplay(self.display, self.logger)
        self.who = WhoDisplay(self.display, self.logger)
        
    def set_brightness(self, val=1.0):
        """ set brightness in range from 0.0 to 1.0 """
        self.brightness = val
        try:
            self.display.brightness = self.brightness
        except Exception as e:
            self.logger.error("SSH Brightness Exception: ", exc_info=True)
            raise IOError
            
    def set_display_mode(self, mode=TIME_MODE):
        self.display_mode = mode
        if self.display_mode == TIME_MODE:
            self.set_brightness(self.brightness)
            self.clock.activate(self.time_format)
        else:
            self.who.activate()
            
    def update(self,):
        if self.display_mode == TIME_MODE:
            self.clock.update()
        else:
            self.who.update()
            
    def set_clock_format(self, hour_format=12):
        """ set the time display in 12 or 24 hour format """
        self.time_format = hour_format

    def set_clock_alarm(self, alarm=False):
        """ set alarm indictor pixel """
        if alarm:
        	self.alarm = 0x10000000
        else:
        	self.alarm = 0


