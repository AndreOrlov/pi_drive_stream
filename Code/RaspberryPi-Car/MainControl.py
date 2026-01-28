import socket
import time
from OledModule.OLED import OLED
import RPi.GPIO as GPIO
GPIO.setwarnings(False)

servoPin1 = 5
servoPin2 = 6
servoPin3 = 7
angle1 = 90
angle2 = 90

GPIO.setup(servoPin1, GPIO.OUT)
GPIO.setup(servoPin2, GPIO.OUT)
GPIO.setup(servoPin3, GPIO.OUT)

def servoPulse(servoPin, myangle):
    pulsewidth = (myangle*11) + 500
    GPIO.output(servoPin,GPIO.HIGH)
    time.sleep(pulsewidth/1000000.0)
    GPIO.output(servoPin,GPIO.LOW)
    time.sleep(20.0/1000 - pulsewidth/1000000.0)

L_IN1 = 20
L_IN2 = 21
L_PWM1 = 0
L_IN3 = 22
L_IN4 = 23
L_PWM2 = 1

R_IN1 = 24
R_IN2 = 25
R_PWM1 = 12

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

def ahead():
    GPIO.output(L_IN1,GPIO.LOW)  #Upper Left forward
    GPIO.output(L_IN2,GPIO.HIGH)
    pwm_L1.ChangeDutyCycle(80)
    GPIO.output(L_IN3,GPIO.HIGH)  #Lower left forward
    GPIO.output(L_IN4,GPIO.LOW)
    pwm_L2.ChangeDutyCycle(80)
    GPIO.output(R_IN1,GPIO.HIGH)  #Upper Right forward
    GPIO.output(R_IN2,GPIO.LOW)
    pwm_R1.ChangeDutyCycle(80)
    GPIO.output(R_IN3,GPIO.LOW)  #Lower Right forward
    GPIO.output(R_IN4,GPIO.HIGH)
    pwm_R2.ChangeDutyCycle(80)

def left():
    GPIO.output(L_IN1,GPIO.HIGH)
    GPIO.output(L_IN2,GPIO.LOW)
    pwm_L1.ChangeDutyCycle(80)
    GPIO.output(L_IN3,GPIO.LOW)
    GPIO.output(L_IN4,GPIO.HIGH)
    pwm_L2.ChangeDutyCycle(80)
    GPIO.output(R_IN1,GPIO.HIGH)
    GPIO.output(R_IN2,GPIO.LOW)
    pwm_R1.ChangeDutyCycle(80)
    GPIO.output(R_IN3,GPIO.LOW)
    GPIO.output(R_IN4,GPIO.HIGH)
    pwm_R2.ChangeDutyCycle(80)

def right():
    GPIO.output(L_IN1,GPIO.LOW)
    GPIO.output(L_IN2,GPIO.HIGH)
    pwm_L1.ChangeDutyCycle(80)
    GPIO.output(L_IN3,GPIO.HIGH)
    GPIO.output(L_IN4,GPIO.LOW)
    pwm_L2.ChangeDutyCycle(80)
    GPIO.output(R_IN1,GPIO.LOW)
    GPIO.output(R_IN2,GPIO.HIGH)
    pwm_R1.ChangeDutyCycle(80)
    GPIO.output(R_IN3,GPIO.HIGH)
    GPIO.output(R_IN4,GPIO.LOW)
    pwm_R2.ChangeDutyCycle(80)

def rear():
    GPIO.output(L_IN1,GPIO.HIGH)
    GPIO.output(L_IN2,GPIO.LOW)
    pwm_L1.ChangeDutyCycle(80)
    GPIO.output(L_IN3,GPIO.LOW)
    GPIO.output(L_IN4,GPIO.HIGH)
    pwm_L2.ChangeDutyCycle(80)
    GPIO.output(R_IN1,GPIO.LOW)
    GPIO.output(R_IN2,GPIO.HIGH)
    pwm_R1.ChangeDutyCycle(80)
    GPIO.output(R_IN3,GPIO.HIGH)
    GPIO.output(R_IN4,GPIO.LOW)
    pwm_R2.ChangeDutyCycle(80)

def stop():
    pwm_L1.ChangeDutyCycle(0)
    pwm_L2.ChangeDutyCycle(0)
    pwm_R1.ChangeDutyCycle(0)
    pwm_R2.ChangeDutyCycle(0)

def clear():
    GPIO.cleanup()

def getLocalIp():
    '''Get the local ip'''
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(('8.8.8.8',80))
        ip=s.getsockname()[0]
    finally:
        s.close()
    return ip


def cameraAction(command):
    global angle1
    global angle2
    if command=='CamUp':
        angle1 = angle1 - 1
        servoPulse(servoPin2, angle1)
        if(angle1 <= 0):
            angle1 = 0
    elif command=='CamDown':
        angle1 = angle1 + 1
        servoPulse(servoPin2, angle1)
        if(angle1 >= 180):
            angle1 = 180

    elif command=='CamLeft':
        angle2 = angle2 + 1
        servoPulse(servoPin3, angle2)
        if(angle2 >= 180):
            angle2 = 180
    elif command=='CamRight':
        angle2 = angle2 - 1
        servoPulse(servoPin3, angle2)
        if(angle2 <= 0):
            angle2 = 0


def motorAction(command):
    '''Set the action of motor according to the command'''
    if command=='DirForward':
        print("go")
        ahead()
    elif command=='DirBack':
        print("back")
        rear()
    elif command=='DirLeft':
        print("left")
        left()
    elif command=='DirRight':
        print("right")
        right()
    elif command=='DirStop':
        print("stop")
        stop()

def setCameraAction(command):
    if command=='CamUp' or command=='CamDown' or command=='CamLeft' or command=='CamRight':
        return command
    else:
        return 'CamStop'



def main():
    ks = 'keyestudio'
    #Init oled module
    oled=OLED()
    oled.setup()
    oled.writeArea1(ks)
    oled.writeArea3('State:')
    oled.writeArea4(' Disconnect')
    time.sleep(2) #Must add delay
    '''The main thread, control the motor'''
    host=getLocalIp()
    print('localhost ip :'+host)
    port=5051

    #Init the tcp socket
    tcpServer=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcpServer.bind((host,port))
    tcpServer.setblocking(0) #Set unblock mode
    tcpServer.listen(5)

    global cameraActionState #Set a state variable for steering module
    cameraActionState='CamStop'

    #Init oled module
    oled=OLED()
    oled.setup()
    oled.writeArea1(host)
    oled.writeArea3('State:')
    oled.writeArea4(' Disconnect')
    while True:
        try:
            time.sleep(0.001)
            (client,addr)=tcpServer.accept()
            print('accept the client!')
            oled.writeArea4(' Connect')
            client.setblocking(0)
            while True:
                time.sleep(0.001)
                cameraAction(cameraActionState)
                try:
                    data=client.recv(1024)
                    data=bytes.decode(data)
                    if(len(data)==0):
                        print('client is closed')
                        oled.writeArea4(' Disconnect')
                        break
                    motorAction(data)
                    cameraActionState=setCameraAction(data)
                except socket.error:
                    continue
                except KeyboardInterrupt as e:
                    raise e
        except socket.error:
            pass
        except KeyboardInterrupt:
            tcpServer.close()
            oled.clear()
            clear()
            print("close")
            break
        except Exception as e1:
            tcpServer.close()
            oled.clear()
main()
