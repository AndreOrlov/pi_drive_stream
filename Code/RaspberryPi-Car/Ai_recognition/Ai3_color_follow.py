import RPi.GPIO as GPIO
import time
import enum
import cv2

import time
# Thread function operation library
import threading
import inspect
import ctypes

import numpy as np
import PID

# servo pin
ServoPin = 7  #S2
ServoPinB = 6  #S3
#Set GPIO BCM
GPIO.setmode(GPIO.BCM)
#servo output mode
def init():
    GPIO.setup(ServoPin, GPIO.OUT)
    GPIO.setup(ServoPinB, GPIO.OUT)

#Defines an impulse function used to generate PWM values in analog mode
#The time-base pulse is 20ms, 
#and the high level part of the pulse controls 0-180 degrees in 0.5-2.5ms
def servo_pulse(myangleA, myangleB):
    pulsewidth = myangleA
    GPIO.output(ServoPin, GPIO.HIGH)
    time.sleep(pulsewidth/1000000.0)
    GPIO.output(ServoPin, GPIO.LOW)
    time.sleep(20.0/1000-pulsewidth/1000000.0)
    
    pulsewidthB = 2500-myangleB
    GPIO.output(ServoPinB, GPIO.HIGH)
    time.sleep(pulsewidthB/1000000.0)
    GPIO.output(ServoPinB, GPIO.LOW)
    time.sleep(20.0/1000-pulsewidthB/1000000.0)

#According to the steering gear pulse control range of 500-2500USEC:
def Servo_control(angle_1, angle_2):
    init()
    if angle_1 < 500:
        angle_1 = 500
    elif angle_1 > 2500:
        angle_1 = 2500
        
    if angle_2 < 500:
        angle_2 = 500
    elif angle_2 > 2500:
        angle_2 = 2500
    servo_pulse(angle_1, angle_2)

# Thread closing function
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

# Enabling the Camera
image = cv2.VideoCapture(0)
image.set(3, 640)
image.set(4, 480)
image.set(5, 120)   #Set the frame rate
# fourcc = cv2.VideoWriter_fourcc(*"MPEG")
image.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
image.set(cv2.CAP_PROP_BRIGHTNESS, 55) #Set the brightness-64 - 64  0.0
image.set(cv2.CAP_PROP_CONTRAST, 20)   #Set contrast -64 - 64  2.0

global color_x, color_y, color_radius
color_x = color_y = color_radius = 0
global target_valuex
target_valuex = 1500
global target_valuey
target_valuey = 1500
global g_mode
g_mode = 0


global color_lower
#color_lower = np.array([156, 43, 46])
#color_lower = np.array([0, 43, 46])  # red
color_lower=np.array([100, 43, 46])  # blue
#color_lower = np.array([35, 43, 46]) #green
global color_upperv
#color_upper = np.array([180, 255, 255])
#color_upper = np.array([10, 255, 255]) # red
color_upper = np.array([124, 255, 255]) # blue
#color_upper = np.array([77, 255, 255]) #green

target_valuex = target_valuey = 2048
Servo_control(1500, 1500)
xservo_pid = PID.PositionalPID(0.8, 0.1, 0.3)
yservo_pid = PID.PositionalPID(0.4, 0.1, 0.2)

# Camera head movement
def Color_track():
    global color_lower, color_upper, g_mode 
    global target_valuex, target_valuey
    t_start = time.time()
    fps = 0
    times = 0
    print("start")
    while True:
        ret, frame = image.read()  # Read the video by frame
        frame = cv2.resize(frame, (300, 300))  # Image size
        frame_ = cv2.GaussianBlur(frame,(5,5),0) # Gaussian filter           
        hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV) # HSV
        mask = cv2.inRange(hsv,color_lower,color_upper)  # Specify color range
        mask = cv2.erode(mask,None,iterations=2)
        mask = cv2.dilate(mask,None,iterations=2)
        mask = cv2.GaussianBlur(mask,(3,3),0)     
        cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2] 
        #if g_mode == 1: # Button switch
        if len(cnts) > 0:
            cnt = max (cnts, key = cv2.contourArea)
            (color_x,color_y),color_radius = cv2.minEnclosingCircle(cnt)
            if color_radius > 10:
                times =  times +  1
                # Mark detected colors
                cv2.circle(frame,(int(color_x),int(color_y)),int(color_radius),(255,0,255),2)  
                # Proportion-Integration-Differentiation
                xservo_pid.SystemOutput = color_x
                xservo_pid.SetStepSignal(150)
                xservo_pid.SetInertiaTime(0.01, 0.1)
                target_valuex = int(1500+xservo_pid.SystemOutput)
                # Input Y direction parameter PID control input
                yservo_pid.SystemOutput = color_y
                yservo_pid.SetStepSignal(150)
                yservo_pid.SetInertiaTime(0.01, 0.1)
                target_valuey = int(1500+yservo_pid.SystemOutput)
                print(target_valuey)
                # Turn the head holder to the PID setting position
                time.sleep(0.008)
                if times == 5 :
                    times = 0 
                    Servo_control(target_valuex,target_valuey)
        fps = fps + 1
        mfps = fps / (time.time() - t_start)
        cv2.putText(frame, "FPS " + str(int(mfps)), (40,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 3)
        # Real-time return image data for display
        cv2.imshow("resuilt",frame) # Display renderings
        
        if cv2.waitKey(10) & 0xFF == ord('q'):
            #End the process, release the camera, and execute as needed
            #stop_thread(thread1)
            image.release()
            break
    #stop_thread(thread1)
    image.release()
    cv2.destroyAllWindows()

Color_track()
# Start the process
#thread1 = threading.Thread(target=Color_track)  # Enter the head control main process
#thread1.setDaemon(True)
#thread1.start()
