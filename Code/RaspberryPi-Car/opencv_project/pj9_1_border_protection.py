import cv2
import numpy as np
import random

img = cv2.imread('car.jpeg', 1)
imgInfo = img.shape
height = imgInfo[0]
width = imgInfo[1]
cv2.imshow('src', img)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
imgG = cv2.GaussianBlur(gray,(3,3),0)
dst = cv2.Canny(img,50,50)
cv2.imshow('dst', dst)
cv2.waitKey(0)
