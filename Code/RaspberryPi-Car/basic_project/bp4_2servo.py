import RPi.GPIO as GPIO
import time

servoPin2 = 7
servoPin3 = 6
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def init():
    GPIO.setup(servoPin2, GPIO.OUT)
    GPIO.setup(servoPin3, GPIO.OUT)
    
def servoPulse(servoPin, myangle):
    pulsewidth = (myangle*11) + 500  # The pulse width
    GPIO.output(servoPin,GPIO.HIGH)
    time.sleep(pulsewidth/1000000.0)
    GPIO.output(servoPin,GPIO.LOW)
    time.sleep(20.0/1000 - pulsewidth/1000000.0) # The cycle of 20 ms

try:
    init()
    while True:
        for i in range(0,180):
            servoPulse(servoPin2, i)
        for i in range(0,180):
            servoPulse(servoPin3, i)

        for i in range(0,180):
            i = 180 - i
            servoPulse(servoPin2, i)
        for i in range(0,180):
            i = 180 - i
            servoPulse(servoPin3, i)
        
        for j in range(0, 50):
            servoPulse(servoPin2, 90)
        for j in range(0, 50):
            servoPulse(servoPin3, 90)
        time.sleep(2)
except KeyboardInterrupt:
    pass
GPIO.cleanup()
