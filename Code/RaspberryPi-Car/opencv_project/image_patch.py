import cv2
import numpy as np

img = cv2.imread('car_damaged.jpeg', 1)
cv2.imshow('src',img)
imgInfo = img.shape
height = imgInfo[0]
width = imgInfo[1]
paint = np.zeros((height,width,1),np.uint8)

for i in range(100, 200):
    paint[i,100] = 255
    paint[i,100+1] = 255
    paint[i,100-1] = 255
    
cv2.imshow('paint',paint)

imgDst = cv2.inpaint(img, paint, 3, cv2.INPAINT_TELEA)

cv2.imshow('image', imgDst)
cv2.waitKey(0)
