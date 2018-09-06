import logging
import time

import Adafruit_PCA9685
import RPi.GPIO as GPIO

from windmeter.dial.direction import DirectionDial
from windmeter.dial.speed import SpeedDial
from windmeter.weerbericht import get_weer_meting, DENHOORN


class Aansturing(object):
    def __init__(self):
        pwm = Adafruit_PCA9685.PCA9685()
        pwm.set_pwm_freq(60)  # good for servos

        self.richting_dial = DirectionDial(pwm)
        self.snelheid_dial = SpeedDial(pwm)
        self.meting = None

        self.start()

    def update_dials(self, meting):
        self.richting_dial.update(meting)
        self.snelheid_dial.update(meting)

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
    Aansturing()
except KeyboardInterrupt:
    GPIO.cleanup()  # clean up GPIO on normal exit
