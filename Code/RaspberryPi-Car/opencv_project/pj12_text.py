import cv2
import numpy as np

img = cv2.imread('car.jpeg', 1)
font = cv2.FONT_HERSHEY_SIMPLEX

cv2.rectangle(img, (50,50),(480,220),(0,255,0),3)
cv2.putText(img,'car',(215,40),font,1,(200,200,0),2,cv2.LINE_AA)
cv2.imshow('src', img)
cv2.waitKey(0)
