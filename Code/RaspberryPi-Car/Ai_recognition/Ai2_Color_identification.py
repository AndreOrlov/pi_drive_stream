import cv2
import numpy as np
import time

cap = cv2.VideoCapture(0)
cap.set(3, 480)
cap.set(4, 380)
cap.set(5, 120)  #Set the frame rate
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_BRIGHTNESS, 60) #Set the brightness -64 - 64  0.0
cap.set(cv2.CAP_PROP_CONTRAST, 40)   #Set contrast -64 - 64  2.0
# image.set(cv2.CAP_PROP_EXPOSURE, 156)  #Set exposure 1.0 - 5000  156.0

# The red areas
color_lower = np.array([0, 43, 46])
color_upper = np.array([10, 255, 255])

# #Green range
#color_lower = np.array([35, 43, 46])
#color_upper = np.array([77, 255, 255])

# #Blue range
#color_lower=np.array([100, 43, 46])
#color_upper = np.array([124, 255, 255])

# #Yellow range
# color_lower = np.array([26, 43, 46])
# color_upper = np.array([34, 255, 255])

# #Orange range
# color_lower = np.array([11, 43, 46])
# color_upper = np.array([25, 255, 255])

def Color_Recongnize():
    
    while(1):
        ret, frame = cap.read()
        cv2.imshow('Capture', frame)
        # change to hsv model
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # get mask
        # The inRange() function and the upper and lower bounds of the blue
        # range in HSV model are used to obtain the mask. The blue part of the
        # original video of the mask will be made white, and the other parts will be black.
        mask = cv2.inRange(hsv, color_lower, color_upper)
        cv2.imshow('Mask', mask)
        #mask_widget.value = bgr8_to_jpeg(mask)

        # detect blue
        # When the mask is pressed and operated on the original video frame,
        # white in the mask will be replaced with the real image:
        res = cv2.bitwise_and(frame, frame, mask=mask)
        cv2.imshow('Result', res)
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        time.sleep(0.01)
    # Exit when closed
    cap.release()
    cv2.destroyAllWindows()

# main function
Color_Recongnize()



