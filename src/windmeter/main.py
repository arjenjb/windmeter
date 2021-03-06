import logging
import time

import Adafruit_PCA9685
import RPi.GPIO as GPIO

from windmeter.dial.direction import DirectionDial
from windmeter.dial.speed import SpeedDial
from windmeter.weerbericht import get_weer_meting, DENHOORN

LOG = logging.getLogger(__name__)

def button_pushed(arg):
    LOG.info("Button pushed: %s", arg)

class Aansturing(object):
    def __init__(self):
        pwm = Adafruit_PCA9685.PCA9685()
        pwm.set_pwm_freq(60)  # good for servos

        button_pin = 27

        GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(button_pin, GPIO.RISING, callback=button_pushed, bouncetime=300)

        # self.richting_dial = DirectionDial(pwm)
        self.snelheid_dial = SpeedDial(pwm)
        self.meting = None

        self.self_test()
        self.start()

    def self_test(self):
        LOG.info("Starting self-test")

        for i in range(0, 40, 5):
            LOG.info("Snelheid: %s", i)
            self.snelheid_dial.set_snelheid_ms(i)
            time.sleep(5)

        LOG.info("Done")

    def update_dials(self, meting):
        # self.richting_dial.update(meting)
        self.snelheid_dial.update(meting)

    def button_pushed(self):
        LOG.info("Button pushed!")

    def start(self):
        while True:
            meting = get_weer_meting(DENHOORN)
            laatste_meting = self.meting
            self.meting = meting

            if laatste_meting is None or meting.timestamp != laatste_meting.timestamp:
                self.update_dials(meting)

            # five minutes
            time.sleep(60 * 5)


try:
    logging.basicConfig(level=logging.INFO)
    GPIO.setmode(GPIO.BCM)

    Aansturing()
except KeyboardInterrupt:
    GPIO.cleanup()  # clean up GPIO on normal exit
