#!/usr/bin/python
import RPi.GPIO as GPIO
from time import sleep
 
led_pin = 12
delay = 0.12

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(led_pin, GPIO.OUT)

i = 10
try:
  while i > 0:
    i -= 1
    GPIO.output(led_pin, 1)
    sleep(delay)
    GPIO.output(led_pin, 0)
    sleep(delay)
except KeyboardInterrupt:
  GPIO.cleanup()
