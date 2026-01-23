import cv2

def useCamera():
    # Obtaining a Camera
    capture = cv2.VideoCapture(0)
    capture.set(3, 480)  # Gets the video frame width
    capture.set(10, 55)  # Screen brightness
    while capture.isOpened():
        # Open the camera and read the image
        flag, image = capture.read()
        cv2.imshow("image", image)
        k = cv2.waitKey(1)
        if k == ord('s'):
            cv2.imwrite("test.jpg", image)
        elif k == ord("q"):
            break
    # release the camera
    capture.release()
    # Close all Windows
    cv2.destroyAllWindows()

if __name__ == '__main__':
    useCamera()
