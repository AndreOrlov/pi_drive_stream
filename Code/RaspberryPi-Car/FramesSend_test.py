import cv2
import numpy
import socket
import time
import struct

HOST='10.0.0.222'
#HOST='192.168.1.222'
PORT=5051  # 1024-5000
WIDTH=320
HEIGHT=240

server=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  # create a UDP 
server.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1) #enable broadcast
# Can be used to specify the destination address/port
server.connect((HOST,PORT))
print('now starting to send frames...')
capture=cv2.VideoCapture(0)   # Enabling the Camera
# Sets the width and height of the image
capture.set(cv2.CAP_PROP_FRAME_WIDTH,WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT,HEIGHT)
try:
    while True:
        time.sleep(0.01)
        success,frame=capture.read()  # Read the video by frame
        if success and frame is not None:
            result,imgencode=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,95])
            #result,imgencode=cv2.imencode('.webp',frame,[cv2.IMWRITE_WEBP_QUALITY,20])
            print(len(imgencode))
            server.sendall(imgencode)
            #print('have sent one frame')
except Exception as e:
    server.sendall(struct.pack('b',1))
    print(e)
    capture.release()
    server.close()
    
