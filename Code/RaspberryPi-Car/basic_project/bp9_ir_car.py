import RPi.GPIO as GPIO
import time

PIN = 15;
SCLK = 8
DIO  = 9
# Display pattern data
matrix_smile = (0x00, 0x00, 0x38, 0x40, 0x40, 0x40, 0x3a, 0x02, 0x02, 0x3a, 0x40, 0x40, 0x40, 0x38, 0x00, 0x00)
matrix_forward = (0x00, 0x00, 0x00, 0x00, 0x12, 0x24, 0x48, 0x90, 0x90, 0x48, 0x24, 0x12, 0x00, 0x00, 0x00, 0x00)
matrix_back = (0x00, 0x00, 0x00, 0x00, 0x48, 0x24, 0x12, 0x09, 0x09, 0x12, 0x24, 0x48, 0x00, 0x00, 0x00, 0x00)
matrix_left = (0x00, 0x00, 0x00, 0x00, 0x18, 0x24, 0x42, 0x99, 0x24, 0x42, 0x81, 0x00, 0x00, 0x00, 0x00, 0x00)
matrix_right = (0x00, 0x00, 0x00, 0x00, 0x00, 0x81, 0x42, 0x24, 0x99, 0x42, 0x24, 0x18, 0x00, 0x00, 0x00, 0x00)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN,GPIO.IN,GPIO.PUD_UP)
GPIO.setup(SCLK,GPIO.OUT)
GPIO.setup(DIO,GPIO.OUT)

print("irm test start...")
# Control M2 motor
L_IN1 = 20
L_IN2 = 21
L_PWM1 = 0
# Control M1 motor
L_IN3 = 22
L_IN4 = 23
L_PWM2 = 1
# Control M3 motor
R_IN1 = 24
R_IN2 = 25
R_PWM1 = 12
# Control M4 motor
R_IN3 = 26
R_IN4 = 27
R_PWM2 = 13

GPIO.setmode(GPIO.BCM)  # use BCM numbers
#set the MOTOR Driver Pin OUTPUT mode
GPIO.setup(L_IN1,GPIO.OUT)
GPIO.setup(L_IN2,GPIO.OUT)
GPIO.setup(L_PWM1,GPIO.OUT)
GPIO.setup(L_IN3,GPIO.OUT)
GPIO.setup(L_IN4,GPIO.OUT)
GPIO.setup(L_PWM2,GPIO.OUT)
GPIO.setup(R_IN1,GPIO.OUT)
GPIO.setup(R_IN2,GPIO.OUT)
GPIO.setup(R_PWM1,GPIO.OUT)
GPIO.setup(R_IN3,GPIO.OUT)
GPIO.setup(R_IN4,GPIO.OUT)
GPIO.setup(R_PWM2,GPIO.OUT)

GPIO.output(L_IN1,GPIO.LOW)
GPIO.output(L_IN2,GPIO.LOW)
GPIO.output(L_IN3,GPIO.LOW)
GPIO.output(L_IN4,GPIO.LOW)
GPIO.output(R_IN1,GPIO.LOW)
GPIO.output(R_IN2,GPIO.LOW)
GPIO.output(R_IN3,GPIO.LOW)
GPIO.output(R_IN4,GPIO.LOW)

#set pwm frequence to 1000hz
pwm_R1 = GPIO.PWM(R_PWM1,100)
pwm_R2 = GPIO.PWM(R_PWM2,100)
pwm_L1 = GPIO.PWM(L_PWM1,100)
pwm_L2 = GPIO.PWM(L_PWM2,100)

#set inital duty cycle to 0
pwm_R1.start(0)
pwm_L1.start(0)
pwm_R2.start(0)
pwm_L2.start(0)

def nop():
    time.sleep(0.000001)
    
def nop2():
    time.sleep(0.01)
    
def start():
    GPIO.output(SCLK,1)
    nop()
    GPIO.output(DIO,1)
    nop()
    GPIO.output(DIO,0)
    nop()
    GPIO.output(SCLK,0)

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

def exec_cmd(key_val):
    if(key_val==0x46):
        print("Button up")
        matrix_display(matrix_forward)
        GPIO.output(L_IN1,GPIO.LOW)  #Upper Left forward
        GPIO.output(L_IN2,GPIO.HIGH)
        pwm_L1.ChangeDutyCycle(50)
        GPIO.output(L_IN3,GPIO.HIGH)  #Lower left forward
        GPIO.output(L_IN4,GPIO.LOW)
        pwm_L2.ChangeDutyCycle(50)
        GPIO.output(R_IN1,GPIO.HIGH)  #Upper Right forward
        GPIO.output(R_IN2,GPIO.LOW)
        pwm_R1.ChangeDutyCycle(50)
        GPIO.output(R_IN3,GPIO.LOW)  #Lower Right forward
        GPIO.output(R_IN4,GPIO.HIGH)
        pwm_R2.ChangeDutyCycle(50)
    elif(key_val==0x44):
        print("Button left")
        matrix_display(matrix_left)
        GPIO.output(L_IN1,GPIO.HIGH)
        GPIO.output(L_IN2,GPIO.LOW)
        pwm_L1.ChangeDutyCycle(100)
        GPIO.output(L_IN3,GPIO.LOW)  
        GPIO.output(L_IN4,GPIO.HIGH)
        pwm_L2.ChangeDutyCycle(100)
        GPIO.output(R_IN1,GPIO.HIGH)  #Upper Right forward
        GPIO.output(R_IN2,GPIO.LOW)
        pwm_R1.ChangeDutyCycle(100)
        GPIO.output(R_IN3,GPIO.LOW)  #Lower Right forward
        GPIO.output(R_IN4,GPIO.HIGH)
        pwm_R2.ChangeDutyCycle(100)
    elif(key_val==0x40):
        print("Button ok")
        matrix_display(matrix_smile)
        pwm_L1.ChangeDutyCycle(0)
        pwm_L2.ChangeDutyCycle(0)
        pwm_R1.ChangeDutyCycle(0)
        pwm_R2.ChangeDutyCycle(0)
    elif(key_val==0x43):
        print("Button right")
        matrix_display(matrix_right)
        GPIO.output(L_IN1,GPIO.LOW)  #Upper Left forward
        GPIO.output(L_IN2,GPIO.HIGH)
        pwm_L1.ChangeDutyCycle(100)
        GPIO.output(L_IN3,GPIO.HIGH)  #Lower left forward
        GPIO.output(L_IN4,GPIO.LOW)
        pwm_L2.ChangeDutyCycle(100)
        GPIO.output(R_IN1,GPIO.LOW)  #Upper Right forward
        GPIO.output(R_IN2,GPIO.HIGH)
        pwm_R1.ChangeDutyCycle(100)
        GPIO.output(R_IN3,GPIO.HIGH)  #Lower Right forward
        GPIO.output(R_IN4,GPIO.LOW)
        pwm_R2.ChangeDutyCycle(100)
    elif(key_val==0x15):
        print("Button down")
        matrix_display(matrix_back)
        GPIO.output(L_IN1,GPIO.HIGH)
        GPIO.output(L_IN2,GPIO.LOW)
        pwm_L1.ChangeDutyCycle(50)
        GPIO.output(L_IN3,GPIO.LOW)
        GPIO.output(L_IN4,GPIO.HIGH)
        pwm_L2.ChangeDutyCycle(50)
        GPIO.output(R_IN1,GPIO.LOW)
        GPIO.output(R_IN2,GPIO.HIGH)
        pwm_R1.ChangeDutyCycle(50)
        GPIO.output(R_IN3,GPIO.HIGH)
        GPIO.output(R_IN4,GPIO.LOW)
        pwm_R2.ChangeDutyCycle(50)
    elif(key_val==0x16):
        print("Button 1")
    elif(key_val==0x19):
        print("Button 2")
    elif(key_val==0x0d):
        print("Button 3")
    elif(key_val==0x0c):
        print("Button 4")
    elif(key_val==0x18):
        print("Button 5")
    elif(key_val==0x5e):
        print("Button 6")
    elif(key_val==0x08):
        print("Button 7")
    elif(key_val==0x1c):
        print("Button 8")
    elif(key_val==0x5a):
        print("Button 9")
    elif(key_val==0x42):
        print("Button *")
    elif(key_val==0x52):
        print("Button 0")
    elif(key_val==0x4a):
        print("Button #")

try:
    while True:
        if GPIO.input(PIN) == 0:
            count = 0
            while GPIO.input(PIN) == 0 and count < 200:  # Wait for 9ms LOW level boot code and exit the loop if it exceeds 1.2ms
                count += 1
                time.sleep(0.00006)

            count = 0
            while GPIO.input(PIN) == 1 and count < 80:   # Wait for a 4.5ms HIGH level boot code and exit the loop if it exceeds 0.48ms
                count += 1
                time.sleep(0.00006)

            idx = 0  # byte count variable
            cnt = 0  #Variable per byte bit
            #There are 4 bytes in total. The first byte is the address code, the second is the address inverse code, 
            #the third is the control command data of the corresponding button, and the fourth is the control command inverse code
            data = [0,0,0,0]
            for i in range(0,32):  # Start receiving 32BITE data
                count = 0
                while GPIO.input(PIN) == 0 and count < 15:  # Wait for the LOW LOW level of 562.5US to pass and exit the loop if it exceeds 900US
                    count += 1
                    time.sleep(0.00006)

                count = 0
                while GPIO.input(PIN) == 1 and count < 40:  # waits for logical HIGH level to pass and exits the loop if it exceeds 2.4ms
                    count += 1
                    time.sleep(0.00006)
                
                # if count>8, that is, the logical time is greater than 0.54+0.562=1.12ms, that is, 
                #the period is greater than the logical 0 period, that is equivalent to receiving logical 1
                if count > 8:   
                    data[idx] |= 1<<cnt    #When idx=0 is the first data  data[idx] = data[idx] | 1<<cnt   00000001 <<1 == 0000 0010
                if cnt == 7:    #With 8 byte
                    cnt = 0     #Displacement qing 0
                    idx += 1    #Store the next data
                else:
                    cnt += 1   #The shift adds 1
            #Determine whether address code + address inverse code =0xff, control code + control inverse code = 0xFF
            if data[0]+data[1] == 0xFF and data[2]+data[3] == 0xFF:  
                 print("Get the key: 0x%02x" %data[2])  #Data [2] is the control code we need
                 exec_cmd(data[2])
except KeyboardInterrupt:
    GPIO.cleanup()
