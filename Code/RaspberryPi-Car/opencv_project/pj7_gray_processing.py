import cv2

img = cv2.imread('car.jpeg', 1)
print("img = ", img.shape)
cv2.imshow('image', img)
dst = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print("gray = ", dst.shape)
cv2.imshow('gray', dst)
cv2.waitKey(0)
