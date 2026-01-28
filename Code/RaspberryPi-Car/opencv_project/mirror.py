import cv2
import numpy as np

img = cv2.imread('car.jpeg', 1)
cv2.imshow('src', img)
imgInfo = img.shape
height = imgInfo[0]
width = imgInfo[1]
deep = imgInfo[2]
newImgInfo = (height*2, width, deep)
dst = np.zeros(newImgInfo, np.uint8)
for i in range(0, height):
    for j in range(0, width):
        dst[i, j] = img[i, j]
        #x y = 2*h - y -1
        dst[height*2-i-1,j] = img[i,j]
for i in range(0,width):
    dst[height,i] = (0,0,255)#BGR
cv2.imshow('dst',dst)
cv2.waitKey(0)
