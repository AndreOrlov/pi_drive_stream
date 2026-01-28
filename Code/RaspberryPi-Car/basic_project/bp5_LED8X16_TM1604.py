import RPi.GPIO as GPIO
import time

SCLK = 8
DIO  = 9
# Display pattern data
smile = (0x00, 0x00, 0x38, 0x40, 0x40, 0x40, 0x3a, 0x02, 0x02, 0x3a, 0x40, 0x40, 0x40, 0x38, 0x00, 0x00)
matrix_forward = (0x00, 0x00, 0x00, 0x00, 0x12, 0x24, 0x48, 0x90, 0x90, 0x48, 0x24, 0x12, 0x00, 0x00, 0x00, 0x00)
matrix_back = (0x00, 0x00, 0x00, 0x00, 0x48, 0x24, 0x12, 0x09, 0x09, 0x12, 0x24, 0x48, 0x00, 0x00, 0x00, 0x00)
matrix_left = (0x00, 0x00, 0x00, 0x00, 0x18, 0x24, 0x42, 0x99, 0x24, 0x42, 0x81, 0x00, 0x00, 0x00, 0x00, 0x00)
matrix_right = (0x00, 0x00, 0x00, 0x00, 0x00, 0x81, 0x42, 0x24, 0x99, 0x42, 0x24, 0x18, 0x00, 0x00, 0x00, 0x00)


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SCLK,GPIO.OUT)
GPIO.setup(DIO,GPIO.OUT)

def nop():
    time.sleep(0.00003)
    
def start():
    GPIO.output(SCLK,0)
    nop()
    GPIO.output(SCLK,1)
    nop()
    GPIO.output(DIO,1)
    nop()
    GPIO.output(DIO,0)
    nop()
    
def matrix_clear():
    GPIO.output(SCLK,0)
    nop()
    GPIO.output(DIO,0)
    nop()
    GPIO.output(DIO,0)
    nop()
    
def send_date(date):
    for i in range(0,8):
        GPIO.output(SCLK,0)
        nop()
        if date & 0x01:
            GPIO.output(DIO,1)
        else:
            GPIO.output(DIO,0)
        nop()
        GPIO.output(SCLK,1)
        nop()
        date >>= 1
        GPIO.output(SCLK,0)
    
def end():
    GPIO.output(SCLK,0)
    nop()
    GPIO.output(DIO,0)
    nop()
    GPIO.output(SCLK,1)
    nop()
    GPIO.output(DIO,1)
    nop()
    
def matrix_display(matrix_value):
    start()
    send_date(0xc0)
    
    for i in range(0,16):
        send_date(matrix_value[i])
        
    end()
    start()
    send_date(0x8A)
    end()

try:
    while True:
        matrix_display(smile)
        time.sleep(1)
        matrix_display(matrix_back)
        time.sleep(1)
        matrix_display(matrix_forward)
        time.sleep(1)
        matrix_display(matrix_left)
        time.sleep(1)
        matrix_display(matrix_right)
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
        
