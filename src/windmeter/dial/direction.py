import json
import logging
import threading
import time
from collections import namedtuple
from datetime import datetime, timedelta
from os import path

import RPi.GPIO as GPIO


LOG = logging.getLogger(__name__)

servo_neutral = 368


marker_start_event = threading.Event()
marker_end_event = threading.Event()


def marker_reached(channel):
    if (GPIO.input(channel)) == 1:
        marker_end_event.set()
        LOG.debug("Marker end")

    else:
        marker_start_event.set()
        LOG.debug("Marker start")


MARKER_START = object()
MARKER_END = object()

CalibrationData = namedtuple('CalibrationData', ('marker', 'ccw', 'cw'))


class DirectionDial(object):
    def __init__(self, pwm):
        self.pwm = pwm

        # setup hall effect sensor
        halleffect_pin_number = 21

        GPIO.setup(halleffect_pin_number, GPIO.IN)
        GPIO.add_event_detect(halleffect_pin_number, GPIO.BOTH, callback=marker_reached)

        self.calibration_data = []
        self.last_calibration = datetime.utcnow()

        self.load_calibration()
        self.actions = 0

        self.calibrate()

    def calibrate_measure(self):
        LOG.info("Calibration in progress")
        LOG.info("Preparing position")
        self.ccw(fast=True, passed=MARKER_END)
        self.cw(until=MARKER_END)

        # measure marker length
        LOG.info("Measuring marker")
        marker_length = self.ccw(passed=MARKER_START)
        LOG.info("Measuring dial CCW")
        dial_length_ccw = self.ccw(passed=MARKER_START)
        LOG.info("Measuring dial CW")
        self.cw(passed=MARKER_START)
        dial_length_cw = self.cw(passed=MARKER_START)

        LOG.info("Calibration (marker, ccw, cw): %f, %f, %f", marker_length, dial_length_ccw, dial_length_cw)

        return CalibrationData(marker_length, dial_length_ccw, dial_length_cw)

    def calibrate(self):
        data = self.calibrate_measure()
        self.calibration_data.append(data)

        if len(self.calibration_data) > 5:
            self.calibration_data = self.calibration_data[-5:]

        self.calibrate_recalculate_means()

        LOG.info("Calibration MEAN (marker, ccw, cw): %f, %f, %f", self.lengths.marker, self.lengths.ccw,
                 self.lengths.cw)

        self.center_after_calibration()
        self.last_calibration = datetime.utcnow()

        self.save_calibration()

    def calibrate_recalculate_means(self):
        n = len(self.calibration_data)
        marker = sum((each.marker for each in self.calibration_data)) / float(n)
        cw = sum((each.cw for each in self.calibration_data)) / float(n)
        ccw = sum((each.ccw for each in self.calibration_data)) / float(n)
        self.lengths = CalibrationData(marker, ccw, cw)

    def center_after_calibration(self):
        t = self.ccw(duration=(self.lengths.marker / 2.0))
        self.degrees = 0
        self.actions = 0

    def center(self):
        self.ccw(fast=True, passed=MARKER_START)
        self.ccw(duration=0.5)
        self.cw(passed=MARKER_START)
        t = self.ccw(duration=(self.lengths.marker / 2.0))

        self.degrees = 0
        self.actions = 0

    def ccw(self, fast=False, until=None, duration=None, passed=None):
        freq_offset = 3
        if fast:
            freq_offset += 10

        actual = self.run_servo_until(freq_offset, until, passed, duration)

        if duration:
            LOG.debug("Actual vs Duration: %f vs %f", actual, duration)

        return actual

    def run_servo_until(self, freq_offset, until, passed, duration):
        T = time.time()

        marker_start_event.clear()
        marker_end_event.clear()

        self.pwm.set_pwm(0, 0, servo_neutral + freq_offset)

        if until is not None:
            if until is MARKER_START:
                LOG.info("Waiting until start")
                marker_start_event.wait(timeout=60.0)
            elif until is MARKER_END:
                LOG.info("Waiting until end")
                marker_end_event.wait(timeout=60.0)

            self.stop_servo()

        if passed is not None:
            if passed is MARKER_START:
                marker_end_event.wait(timeout=60.0)
                marker_start_event.wait(timeout=60.0)
            else:
                marker_end_event.wait(timeout=60.0)
                marker_start_event.wait(timeout=60.0)

            self.stop_servo()

        if duration is not None:
            time.sleep(duration)
            self.stop_servo()

        return time.time() - T

    def cw(self, duration=None, fast=False, until=None, passed=None):
        freq_offset = 5
        if fast:
            freq_offset += 10

        return self.run_servo_until(-freq_offset, until, passed, duration)

    def stop_servo(self):
        self.pwm.set_pwm(0, 0, servo_neutral)

    def update(self, meting):
        self.set_degrees(meting.richting_graden)

    def set_degrees(self, degrees):
        if self.should_calibrate():
            self.calibrate()

        if degrees == self.degrees:
            return None

        self.actions += 1

        # every 10 actions, we re-center the dial
        if self.actions == 10:
            self.center()

        def calc_delta(current_deg, desired_deg):
            delta_cw = desired_deg - current_deg

            if delta_cw < 0:
                delta_cw = 360 + delta_cw

            if delta_cw > 180:
                return delta_cw - 360
            else:
                return delta_cw

        delta = calc_delta(self.degrees, degrees)

        LOG.info("Moving to %f degrees from %f (Delta %f)", self.degrees, degrees, delta)

        if delta < 0:
            LOG.info("Moving CCW")
            self.ccw(duration=abs(delta) / 360.0 * self.lengths.ccw)
        else:
            LOG.info("Moving CW")
            self.cw(duration=(delta / 360.0 * self.lengths.cw))

        self.degrees = degrees

    def load_calibration(self):
        if not path.exists('calibration.json'):
            return

        with open('calibration.json', 'r') as fp:
            self.calibration_data = [CalibrationData(*each) for each in json.load(fp)]

        self.calibrate_recalculate_means()

    def save_calibration(self):
        with open('calibration.json', 'w') as fp:
            json.dump(self.calibration_data, fp)

    def should_calibrate(self):
        now = datetime.utcnow()

        if len(self.calibration_data) < 5 and (now - self.last_calibration) >= timedelta(hours=2):
            # recalibrate every 2 hours until we have 5 calibrations
            return True

        # Calibrate 8.00 in the morning, and 18.00 in the evening
        if (now - self.last_calibration) >= timedelta(hours=1, minutes=5):
            if now.hour in [8, 18]:
                return True

        return False
