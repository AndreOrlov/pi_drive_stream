import cv2
import numpy as np

img = cv2.imread('car.jpeg',1)

img_bgr2rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
cv2.imshow('src', img_bgr2rgb)
#cv2.waitKey(0)
imgInfo = img.shape
height = imgInfo[0]
width = imgInfo[1]
#src 3->dst 3 (左上角 左下角 右上角)
matSrc = np.float32([[0,0],[0,height-1],[width-1,0]])
matDst = np.float32([[50,50],[100,height-50],[width-100,50]])
#组合
matAffine = cv2.getAffineTransform(matSrc,matDst)# mat 1 src 2 dst
dst = cv2.warpAffine(img,matAffine,(width,height))
img_bgr2rgb2 = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
cv2.imshow('affine', img_bgr2rgb2)
cv2.waitKey(0)
