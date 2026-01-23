import RPi.GPIO as GPIO
import time

PIN = 15;

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN,GPIO.IN,GPIO.PUD_UP)
print("irm test start...")

def exec_cmd(key_val):
    if(key_val==0x46):
        print("Button up")
    elif(key_val==0x44):
        print("Button left")
    elif(key_val==0x40):
        print("Button ok")
    elif(key_val==0x43):
        print("Button right")
    elif(key_val==0x15):
        print("Button down")
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
