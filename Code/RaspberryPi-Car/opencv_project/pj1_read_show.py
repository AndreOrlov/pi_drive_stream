import cv2  # Import the opencv

image = cv2.imread('car.jpeg', 1)  # Read the image named car2.jpeg from the same directory
cv2.imshow('sports car', image) # Displays the read images in a window named Sports Car
cv2.waitKey(5000) # Wait for 5 seconds
