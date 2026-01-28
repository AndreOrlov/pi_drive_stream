import cv2
import numpy as np

img = cv2.imread('car.jpeg', 1)
for i in range(100, 200):
    img[i,100] = (255,255,255)
    img[i,100+1] = (255,255,255)
    img[i,100-1] = (255,255,255)

cv2.imwrite('car_damaged.jpeg',img)
cv2.imshow('image',img)
cv2.waitKey(0)
