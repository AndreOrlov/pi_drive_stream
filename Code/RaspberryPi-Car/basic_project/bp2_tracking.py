import RPi.GPIO as GPIO
from time import sleep

#tracking pin
trackingPin1 = 17
trackingPin2 = 18
trackingPin3 = 19

GPIO.setmode(GPIO.BCM) # use BCM numbers

GPIO.setup(trackingPin1,GPIO.IN)  # set trackingPin INPUT mode
GPIO.setup(trackingPin2,GPIO.IN)
GPIO.setup(trackingPin3,GPIO.IN)

while True:
    val1 = GPIO.input(trackingPin1) # read the value
    val2 = GPIO.input(trackingPin2)
    val3 = GPIO.input(trackingPin3)
    print("tracking1 = ", val1, "tracking2 = ", val2, "tracking3 = ", val3)
    sleep(0.1)
        
GPIO.cleanup() # Release all GPIO
