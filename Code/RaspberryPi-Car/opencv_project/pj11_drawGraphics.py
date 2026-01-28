import cv2
import numpy as np

newImageInfo = (500, 500, 3)
dst = np.zeros(newImageInfo, np.uint8)

cv2.rectangle(dst, (350,100),(300,200),(0,0,255),5)
cv2.circle(dst,(100,100),(50),(255, 0, 0), 2)
cv2.ellipse(dst, (226,256), (120,80),0,0,360,(0,255,255),-1)

cv2.imshow('dst',dst)
cv2.waitKey(0)
