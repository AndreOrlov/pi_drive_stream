
import cv2
img = cv2.imread('car.jpeg',1) #Read the pictures
cv2.imwrite('carTest.jpeg', img, [cv2.IMWRITE_JPEG_QUALITY, 50]) #Compress the image and save it
img2 = cv2.imread('carTest.jpeg',1) #Read the compressed image
cv2.imshow('car', img) 
cv2.imshow('carTest', img2)
cv2.waitKey(0)
