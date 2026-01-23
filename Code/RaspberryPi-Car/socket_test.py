import socket
import time
import sys
from OledModule.OLED import OLED
import RPi.GPIO as GPIO
GPIO.setwarnings(False)

def getLocalIp():
    '''Get the local ip'''
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Create a UDP socket
        s.connect(('8.8.8.8',80)) 
        ip=s.getsockname()[0]  # The returned IP address is obtained
    finally:
        s.close()
    return ip
    
def cameraAction(command):
    if command=='CamUp':
        print("camUp")
    elif command=='CamDown':
        print("camDown")
    elif command=='CamLeft':
        print("camLeft")
    elif command=='CamRight':
        print("camRight")
    elif command=='CamStop':
        print("camStop")

def motorAction(command):
    '''Set the action of motor according to the command'''
    if command=='DirForward':
        print("go")
    elif command=='DirBack':
        print("back")
    elif command=='DirLeft':
        print("left")
    elif command=='DirRight':
        print("right")
    elif command=='DirStop':
        print("stop")

def main():
    ks = 'keyestudio'
    #Init oled module
    oled=OLED()
    oled.setup()
    oled.writeArea1(ks)
    oled.writeArea3('State:')
    oled.writeArea4(' Disconnect')
    time.sleep(2) #Must add delay
    
    host=getLocalIp()
    print('localhost ip :'+host)
    port=5051
    #Init the tcp socket
    tcpServer=socket.socket(socket.AF_INET,socket.SOCK_STREAM) # Create a TCP socket
    tcpServer.bind((host,port)) # Bind address (host, port)
    tcpServer.setblocking(0) #Set unblock mode
    tcpServer.listen(5) # Start listening for TCP incoming connections
    time.sleep(1)
    oled.clear()
    time.sleep(0.1)
    oled.writeArea1(host)
    oled.writeArea3('State:')
    oled.writeArea4(' Disconnect')
    time.sleep(2)
    
    while True:
        try:
            #time.sleep(0.001)
            # Accepts a TCP connection and returns (connect,address), 
            # where connect is the new socket object that can be used to receive and send data. 
            # Address is the address of the connected client.
            client,addr = tcpServer.accept()
            print('accept the client!')
            oled.writeArea4(' Connect')
            client.setblocking(0) # Set the socket to non-blocking mode
            while True:
                time.sleep(0.001)
                try:
                    #Accepts TCP socket data. The data is returned as a string
                    data=client.recv(1024) 
                    data=bytes.decode(data) # Get the final data
                    if(len(data)==0):
                        print('client is closed')
                        oled.writeArea4(' Disconnect')
                        break
                    motorAction(data)  # Passes the received data to the function
                    cameraAction(data)
                except socket.error:
                    continue
                    #pass
                except KeyboardInterrupt as e:
                    raise e
        except socket.error:
            pass
        except KeyboardInterrupt:
            tcpServer.close() 
            oled.clear()
            print("close")
            sys.exit()

            
        except Exception as e:
            tcpServer.close()
            oled.clear()

        
main() # Enter main program
