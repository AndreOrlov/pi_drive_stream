import cv2
import numpy as np

img = cv2.imread('car.jpeg',1)
cv2.imshow('src',img)
# (5,5) indicates that both the length and width of the Gaussian matrix are 5
# The standard deviation is 1.5
dst = cv2.GaussianBlur(img,(5,5),1.5)
cv2.imshow('dst',dst)
cv2.waitKey(0)

