import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

#define GPIO pin
GPIO_TRIGGER = 14
GPIO_ECHO = 4

#set GPIO mode (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

def distance():
    # 10us is the trigger signal
    GPIO.output(GPIO_TRIGGER, GPIO.HIGH)
    time.sleep(0.00001)  #10us
    GPIO.output(GPIO_TRIGGER, GPIO.LOW)
    while not GPIO.input(GPIO_ECHO):
        pass
    t1 = time.time()
    while GPIO.input(GPIO_ECHO):
        pass
    t2 = time.time()
    print("distance is %d " % (((t2 - t1)* 340 / 2) * 100))
    time.sleep(0.01)
    return ((t2 - t1)* 340 / 2) * 100


if __name__ == '__main__':   #Program entry
    try:
        while True:
            print("aaaa")
            dist = distance()  #
            print("Measured Distance = {:.2f} cm".format(dist)) #{:.2f},Keep two decimal places
            time.sleep(1)

        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
