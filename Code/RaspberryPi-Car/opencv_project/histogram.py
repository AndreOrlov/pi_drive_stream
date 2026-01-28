import cv2
import numpy as np
import matplotlib.pyplot as plt


img = cv2.imread('Road_test.jpg', 1)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#cv2.imshow('img', img)
#histb = cv2.calcHist([img], [0], None, [256], [0, 255])
#plt.plot(histb, color='b')
plt.hist(img.ravel(), 256)
plt.show()
cv2.waitKey(0)
