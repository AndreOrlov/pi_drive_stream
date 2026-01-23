import enum
import cv2

#Camera display module
import cv2
import time
import sys

image = cv2.VideoCapture(0)
image.set(3,320)
image.set(4,240)
image.set(cv2.CAP_PROP_BRIGHTNESS, 50) #Set the brightness -64 - 64  0.0
ret, frame = image.read()

# Face recognition
# body_haar = cv2.CascadeClassifier("haarcascade_upperbody.xml")
face_haar = cv2.CascadeClassifier("haarcascade_profileface.xml") 
#face_haar = cv2.CascadeClassifier("haarcascade_fullbody.xml")
#eye_haar = cv2.CascadeClassifier("haarcascade_eye.xml")  
#eye_haar = cv2.CascadeClassifier("haarcascade_eye_tree_eyeglasses.xml")  
def Camera_display():
    while 1:
        ret, frame = image.read()
        # Convert the image to black and white
        gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         # Detect all pedestrians in the image
#         bodies = body_haar.detectMultiScale(gray_img, 1.3, 5)
#         for body_x,body_y,body_w,body_h in bodies:
#             cv2.rectangle(frame, (body_x, body_y), (body_x+body_w, body_y+body_h), (0,255,0), 2)

# detectMultiScale（const Mat& image, vector& objects, double scaleFactor=1.1，int minNeighbors, int flag，cvSize）
# 1. image is the gray scale image of the input
# 2. Objects is a vector group of rectangular boxes to get the detected object
# 3. ScaleFactor is the scale parameter in each image scale, with a default value of 1.1. 
#    The scale_factor parameter determines how much of a jump there is between scans of two Windows of different sizes. 
#    Setting this parameter to large means that the computation is faster, but if the window misses a face of a certain size, the object may be lost.
# 4. MinNeighbors parameters for each cascade number of adjacent rectangular should be retained (can't understand this parameter, -_ - | | |), the default value is 3. 
#    MinNeighbors controls false detection, with a default value of 3 indicating at least three overlapping detections before we think a face actually exists.
# 5. MinSize indicates the minimum size of the target
# 6. MaxSize is the maximum size of the target


        faces = face_haar.detectMultiScale(gray_img, 1.1, 3)
        for face_x,face_y,face_w,face_h in faces:
            cv2.rectangle(frame, (face_x, face_y), (face_x+face_w, face_y+face_h), (0,255,0), 2)
            (face_x, face_y, face_w, face_h) = faces[0]
            print(faces[0:1])
        '''
        eyes = eye_haar.detectMultiScale(gray_img, 1.1, 3)
        for eye_x,eye_y,eye_w,eye_h in eyes:
            cv2.rectangle(frame, (eye_x,eye_y), (eye_x+eye_w, eye_y+eye_h), (255,0,0), 2)
        
#         eyes = eye_haar.detectMultiScale(gray_img, 1.3, 5)
#         for eye_x,eye_y,eye_w,eye_h in eyes:
#             cv2.rectangle(frame, (eye_x,eye_y), (eye_x+eye_w, eye_y+eye_h), (255,0,0), 2)
        '''
        cv2.imshow("people",frame)
        time.sleep(0.010)
        # If you press q, exit the loop and close the thread
        if cv2.waitKey(10) & 0xFF == ord('q'):
            image.release()
            break

Camera_display()



