import logging
import math

LOG = logging.getLogger(__name__)


class SpeedDial(object):
    def __init__(self, pwm):
        self.pwm = pwm
        self.snelheid_ms = None

        self.set_snelheid_ms(0)

    def get_servo_pos(self, v):
        servo_00 = 476
        servo_05 = 447
        servo_10 = 420
        servo_15 = 382
        servo_20 = 350
        servo_25 = 325
        servo_30 = 289
        servo_35 = 266
        servo_40 = 250

        map = [
            servo_00,
            servo_05,
            servo_10,
            servo_15,
            servo_20,
            servo_25,
            servo_30,
            servo_35,
            servo_40
        ]

        r = v % 5

        index = int(math.floor(v / 5))

        l = map[index]
        u = map[index + 1]
        position = int(l + ((u - l) / 5.0 * r))

        return position

    def set_snelheid_ms(self, snelheid_ms):
        if snelheid_ms == self.snelheid_ms:
            return

        self.snelheid_ms = snelheid_ms
        self.pwm.set_pwm(1, 0, self.get_servo_pos(self.snelheid_ms))

    def update(self, meting):
        self.set_snelheid_ms(meting.snelheid_ms)