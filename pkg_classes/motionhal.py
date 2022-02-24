#!/usr/bin/python3
""" DIYHA Motion Controller:
    Detect PIR motion and create a queue to manage them.
"""

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

import queue
import logging
import logging.config

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!")

class MotionHAL:
    """ Motion detection device driver for PIR sensor """

    def __init__(self, logging_file, pin):
        """ Initialize device and class defaults """
        logging.config.fileConfig(fname=logging_file, disable_existing_loggers=False)
        # Get the logger specified in the file
        self.logger = logging.getLogger(__name__)
        self.queue = queue.Queue()
        """ Setup interrupts on the GPIO pin and the motion queue. """
        self.channel = pin
        try:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        except RuntimeError:
            print("HAL PIR setup error RPi.GPIO!")
        self.last_reading = 0

    def pir_interrupt_handler(self, gpio):
        """ Motion interrupt handler adds 1 or 0 to queue. """
        try:
            state = GPIO.input(gpio)
        except RuntimeError:
            print("HAL PIR Error interrupt handler RPi.GPIO!")
        if state == 1:
            message = "1"
        else:
            message = "0"
        if state != self.last_reading:
            self.queue.put(message)
        self.last_reading = state

    def enable(self,):
        """ Enable interrupts and prepare the callback. """
        try:
            GPIO.add_event_detect(self.channel, GPIO.RISING, callback=self.pir_interrupt_handler)
        except RuntimeError:
            print("Error importing RPi.GPIO!")

    def detected(self,):
        """ Has motion been detected? True or false based on queue contents. """
        return not self.queue.empty()

    def get_motion(self,):
        """ Return the last value either 1 or 0. """
        return self.queue.get(False)

    def wait_for_motion(self,):
        """ Blocking wait for the next interrupt 1 or 0. """
        return self.queue.get(True)

