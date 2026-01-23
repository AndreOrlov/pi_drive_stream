import cv2 

img = cv2.imread('car.jpeg', 1)  # read photo
(b, g, r) = img[100, 100]  # Get the BGR value at the image coordinates [100, 100]
print(b, g, r) # print
x = 0
y = 0
#At the coordinates [100,100], draw a white square
for x in range(100, 200):
    img[x, y] = (255, 255, 255) # Assigns a value to the specified pixel color
    for y in range(100, 200):
        img[x, y] = (255, 255, 255)

cv2.imshow('image', img)
cv2.waitKey(0)
