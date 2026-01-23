import cv2

img = cv2.imread('car.jpeg', 1)
print(img.shape)  #Prints values for three channels

#Gets the values of the first two channels, that is, the length and width
x, y = img.shape[0:2]
cv2.imshow('originalPicture', img)
# Reduce the size of the image by two times. Default is linear compression
img1 = cv2.resize(img, (int(y/2), int(x/2)))
cv2.imshow('resize1', img1)
#cv2.waitKey(0)
# Resampling compression using pixel region relationships
img2 = cv2.resize(img, (0, 0), fx=1.5, fy=1.5, interpolation=cv2.INTER_NEAREST)
cv2.imshow('resize2', img2)
cv2.waitKey(0)
cv2.destroyAllWindows() # Close all Windows
