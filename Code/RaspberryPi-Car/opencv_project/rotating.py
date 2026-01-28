import cv2
import numpy as np
img = cv2.imread('car.jpeg',1)
cv2.imshow('src',img)
imgInfo = img.shape
height = imgInfo[0]
width = imgInfo[1]
# 2*3 
# cv2.getRotationMatrix2D(center, angle, scale)  
# center: 旋转中心点
# angle：旋转角度，正数表示逆时针，负数表示顺时针
# scale：变换尺度
matRotate = cv2.getRotationMatrix2D((width*0.5, height*0.5), 20, 1)# mat rotate 1 center 2 angle 3 scale
#100*100 25 
dst = cv2.warpAffine(img, matRotate, (width,height))
cv2.imshow('dst',dst)
cv2.waitKey(0)
