import enum
import cv2
# import the necessary packages
#import simple_barcode_detection
import numpy as np
import pyzbar.pyzbar as pyzbar
from PIL import Image

# Define and parse two-dimensional code
def decodeDisplay(image):
    barcodes = pyzbar.decode(image)
    for barcode in barcodes:
        # Extract the position of the boundary box of the TWO-DIMENSIONAL code
        # Draw the bounding box for the bar code in the image
        (x, y, w, h) = barcode.rect
        cv2.rectangle(image, (x, y), (x + w, y + h), (225, 225, 225), 2)

        # Extract qr code data as byte objects, so if we want to output images on
        # To draw it, you have to convert it to a string
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type

        # Plot the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,0.5, (225, 225, 225), 2)

        # Prints barcode data and barcode type to the terminal
        print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
    return image

def detect():
    camera = cv2.VideoCapture(0)
    camera.set(3, 320)
    camera.set(4, 240)
    camera.set(5, 120)  #Set the frame rate
    # fourcc = cv2.VideoWriter_fourcc(*"MPEG")
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    camera.set(cv2.CAP_PROP_BRIGHTNESS, 50) #Set the brightness -64 - 64  0.0
    camera.set(cv2.CAP_PROP_CONTRAST, 50) #Set contrast -64 - 64  2.0
    camera.set(cv2.CAP_PROP_EXPOSURE, 156) #Set exposure 1.0 - 5000  156.0
    ret, frame = camera.read()
    while True:
        # Read current frame
        ret, frame = camera.read()
        #Grayscale image
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        im = decodeDisplay(gray)
        cv2.waitKey(5)
        cv2.imshow("image",im)
        # If you press Q, the loop will be broken
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    camera.release()
    cv2.destroyAllWindows()

while 1:
    detect()
