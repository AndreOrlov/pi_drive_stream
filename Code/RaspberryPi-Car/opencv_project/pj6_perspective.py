import cv2
import numpy as np

img = cv2.imread('car.jpeg',1)

imgInfo = img.shape
print(imgInfo)
height = imgInfo[0]
width = imgInfo[1]
#src 4->dst 4 Enter the coordinates of the four points of the image
matSrc = np.float32([[50,10],[50,200],[400,50],[400,230]])
matDst = np.float32([[100,30],[100,200],[400,100],[360,200]])
#Perspective conversion function
matAffine = cv2.getPerspectiveTransform(matSrc,matDst)# mat 1 src 2 dst
dst = cv2.warpPerspective(img,matAffine,(width,height))
img_bgr2rgb = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
cv2.imshow('perspective', img_bgr2rgb)
cv2.waitKey(0)
