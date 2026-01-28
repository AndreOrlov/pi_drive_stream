import cv2
img = cv2.imread('car.jpeg', 1)
img2 = img[100:500, 20:200] # Select rectangle X(100~500) Y(20~200)
cv2.imshow('image_src', img)
cv2.imshow('image2', img2)
cv2.waitKey(0)
