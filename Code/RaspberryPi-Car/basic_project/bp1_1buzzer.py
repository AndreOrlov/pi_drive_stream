# -*- coding: utf-8 -*-
import time
import RPi.GPIO as GPIO

buzPin = 16
i1 = 0
i2 = 0
GPIO.setmode(GPIO.BCM)  # use BCM numbers
GPIO.setup(buzPin, GPIO.OUT) # set pin OUTPUT mode

try:
    while 1:  #loop
        while(i1<50):
            GPIO.output(buzPin,GPIO.HIGH)  
            time.sleep(0.001)              #wait for 1 ms
            GPIO.output(buzPin,GPIO.LOW)
            time.sleep(0.001)
            i1 = i1 + 1
        time.sleep(0.3)
        while(i2<50):
            GPIO.output(buzPin,GPIO.HIGH)
            time.sleep(0.001)              #wait for 1 ms
            GPIO.output(buzPin,GPIO.LOW)
            time.sleep(0.001)
            i2 = i2 + 1
        time.sleep(1)
        i1 = 0
        i2 = 0
except KeyboardInterrupt:
    pass
GPIO.cleanup() #release all GPIO
