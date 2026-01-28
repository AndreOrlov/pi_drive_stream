#!/usr/bin/python
import cv2
import numpy
import socket
import time
import struct

from scapy.all import *
IPData = [0,1] # Store the size of the IP address of the phone
def Echo(packet):
    IP=(packet['IP'].src)
    Bigx=len(packet[Raw])
    global IPData
    IPData[0]=IP
    IPData[1]=Bigx
    print ("source IP:",IPData[0])
    print("Packet size：",IPData[1])
def Stop(packet):
    #if IPData[1] == 1111:
    return True

#sniff(iface="wlan0",filter="icmp[icmptype] = icmp-echo",count=1,prn=Echo,stop_filter=Stop)
#sniff(iface="eth0",filter="icmp[icmptype] = icmp-echo",count=1,prn=Echo,stop_filter=Stop)
while(IPData[0] == 0)or(IPData[0] == '10.0.0.1'):
    print("wait..")
    sniff(iface="wlan0",filter="icmp[icmptype] = icmp-echo",count=0,prn=Echo,stop_filter=Stop)
    print("IP = ",IPData[0])

print ("source IP:",IPData[0])
HOST=IPData[0]  # Assign the obtained IP address to HOST
#HOST='10.0.0.222'
#HOST='192.168.1.222'
PORT=5051
WIDTH=320
HEIGHT=240

server=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  # create a UDP 
server.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1) #enable broadcast
server.connect((HOST,PORT))
print('now starting to send frames...')
capture=cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH,WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT,HEIGHT)
try:
    while True:
        try:
            time.sleep(0.01)
            success,frame=capture.read()
            if success and frame is not None:
                result,imgencode=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,95])
                #result,imgencode=cv2.imencode('.webp',frame,[cv2.IMWRITE_WEBP_QUALITY,20])
                #print(len(imgencode))
                server.sendall(imgencode)
                #print('have sent one frame')
        except Exception as e:
            print(e)
            continue
except Exception as e:
    server.sendall(struct.pack('b',1))
    print(e)
    capture.release()
    server.close()
    
