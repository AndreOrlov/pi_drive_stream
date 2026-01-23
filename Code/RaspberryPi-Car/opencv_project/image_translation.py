import cv2
import numpy as np

img = cv2.imread('car.jpeg', 1)
cv2.imshow('image', img)
imgInfo = img.shape
height = imgInfo[0]
width = imgInfo[1]
matShift = np.float32([[1,0,30],[0,1,20]])# 2*3
dst = cv2.warpAffine(img,matShift,(width,height))#1 data 2 mat 3 info
cv2.imshow('dst',dst)
cv2.waitKey(0)
