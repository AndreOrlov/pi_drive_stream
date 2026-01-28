import time
import Adafruit_GPIO.SPI as SPI
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from board import SCL, SDA
import busio

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Note you can change the I2C address, or add a reset pin:
# disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3c, reset=reset_pin)

# Clear display.
#disp.fill(0)
#disp.show()

class Area(object):
	def __init__(self,left,top,right,bottom):
		self.left=left
		self.top=top
		self.right=right
		self.bottom=bottom

class OLED(object):
	'''oled module'''
	def __init__(self):
		self.disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
		self.image=Image.new('1',(self.disp.width,self.disp.height))
		self.draw=ImageDraw.Draw(self.image)
		self.area1=Area(0,0,127,15)
		self.area2=Area(0,16,127,33)
		self.area3=Area(0,31,127,48)
		self.area4=Area(0,46,127,63)
		self.font=ImageFont.truetype('VCR_OSD_MONO_1.001.ttf',15)


	def setup(self):
		#self.disp.begin()
		#self.disp.clear()
		#self.disp.display()
		self.disp.fill(0)
		self.disp.show()
		
		
	def clearArea1(self):
		self.draw.rectangle((self.area1.left,self.area1.top,self.area1.right,self.area1.bottom),outline=0,fill=0)
		self.disp.image(self.image)
		#self.disp.display()
		disp.show()
		
	def clearArea2(self):
		self.draw.rectangle((self.area2.left,self.area2.top,self.area2.right,self.area2.bottom),outline=0,fill=0)
		self.disp.image(self.image)
		#self.disp.display()
		disp.show()
		
	def clearArea3(self):
		self.draw.rectangle((self.area3.left,self.area3.top,self.area3.right,self.area3.bottom),outline=0,fill=0)
		self.disp.image(self.image)
		#self.disp.display()
		disp.show()
		
	def clearArea4(self):
		self.draw.rectangle((self.area4.left,self.area4.top,self.area4.right,self.area4.bottom),outline=0,fill=0)
		self.disp.image(self.image)
		#self.disp.display()
		self.disp.show()
		
	def writeArea1(self,text):
		self.clearArea1()
		self.draw.text((self.area1.left,self.area1.top),text,font=self.font,fill=1)
		self.disp.image(self.image)
		#self.disp.display()
		self.disp.show()
		
	def writeArea2(self,text):
		self.clearArea2()
		self.draw.text((self.area2.left,self.area2.top),text,font=self.font,fill=1)
		self.disp.image(self.image)
		#self.disp.display()
		self.disp.show()
		
	def writeArea3(self,text):
		self.clearArea3()
		self.draw.text((self.area3.left,self.area3.top),text,font=self.font,fill=1)
		self.disp.image(self.image)
		#self.disp.display()
		self.disp.show()
		
	def writeArea4(self,text):
		self.clearArea4()
		self.draw.text((self.area4.left,self.area4.top),text,font=self.font,fill=1)
		self.disp.image(self.image)
		#self.disp.display()
		self.disp.show()
		
	def clear(self):
		#self.disp.clear()
		#self.disp.display()
		self.disp.fill(0)
		self.disp.show()

