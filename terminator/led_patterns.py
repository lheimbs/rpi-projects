#!/usr/bin/env python

# Copyright (C) 2017 Seeed Technology Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import numpy
import time


class LedPattern(object):
    def __init__(self, show=None, number=12):
        self.pixels_number = number
        self.pixels = [0] * 4 * number

        self.basis = numpy.array([0] * 4 * 12)
        self.basis[0 * 4 + 1] = 2
        self.basis[3 * 4 + 1] = 1
        self.basis[3 * 4 + 2] = 1
        self.basis[6 * 4 + 2] = 2
        self.basis[9 * 4 + 3] = 2

        self.pixels_np_google = self.basis * 24

        if not show or not callable(show):

            def dummy(data):
                pass

            show = dummy

        self.show = show
        self.stop = False

    def cmd_accepted(self):
        pixels = [255, 0, 0, 0] * self.pixels_number
        pixels += [0, 2, 50, 0] * 5
        pixels += [255, 0, 0, 0] * self.pixels_number

        for i in reversed(range(18)):
            active_pixels = pixels[i * 4 : (12 + i) * 4]
            self.show(active_pixels)
            time.sleep(0.05)

    def cmd_rejected(self):
        pixels = numpy.array([0, 1, 0, 0] * 12)
        self.show(pixels)
        time.sleep(0.1)
        for i in range(15):
            if i < 7:
                pixels *= 2
            else:
                pixels = pixels / 2
            self.show(pixels)
            time.sleep(0.05)
        self.off()

    def alexa_wakeup(self, direction=0):
        position = (
            int((direction + 15) / (360 / self.pixels_number)) % self.pixels_number
        )

        pixels = [0, 0, 0, 24] * self.pixels_number
        pixels[position * 4 + 2] = 48

        self.show(pixels)

    def google_wakeup(self, direction=0):
        position = int((direction + 15) / 30) % 12

        basis = numpy.roll(self.basis, position * 4)
        for i in range(1, 25):
            pixels = basis * i
            self.show(pixels)
            time.sleep(0.005)

        pixels = numpy.roll(pixels, 4)
        self.show(pixels)
        time.sleep(0.1)

        for i in range(2):
            new_pixels = numpy.roll(pixels, 4)
            self.show(new_pixels * 0.5 + pixels)
            pixels = new_pixels
            time.sleep(0.1)

        self.show(pixels)
        self.pixels_np_google = pixels

    def alexa_listen(self):
        pixels = [0, 0, 0, 24] * self.pixels_number

        self.show(pixels)

    def google_listen(self):
        pixels = self.pixels_np_google
        for i in range(1, 25):
            self.show(pixels * i / 24)
            time.sleep(0.01)

    def alexa_think(self):
        pixels = [0, 0, 12, 12, 0, 0, 0, 24] * self.pixels_number

        while not self.stop:
            self.show(pixels)
            time.sleep(0.2)
            pixels = pixels[-4:] + pixels[:-4]

    def google_think(self):
        pixels = self.pixels_np_google

        while not self.stop:
            pixels = numpy.roll(pixels, 4)
            self.show(pixels)
            time.sleep(0.2)

        t = 0.1
        for i in range(0, 5):
            pixels = numpy.roll(pixels, 4)
            self.show(pixels * (4 - i) / 4)
            time.sleep(t)
            t /= 2

        self.pixels_np_google = pixels

    def alexa_speak(self):
        step = 1
        position = 12
        while not self.stop:
            pixels = [0, 0, position, 24 - position] * self.pixels_number
            self.show(pixels)
            time.sleep(0.01)
            if position <= 0:
                step = 1
                time.sleep(0.4)
            elif position >= 12:
                step = -1
                time.sleep(0.4)

            position += step

    def google_speak(self):
        pixels = self.pixels_np_google
        step = 1
        brightness = 10
        while not self.stop:
            self.show(pixels * brightness / 24)
            time.sleep(0.02)

            if brightness <= 5:
                step = 1
                time.sleep(0.4)
            elif brightness >= 24:
                step = -1
                time.sleep(0.4)

            brightness += step

    def alarm(self):
        step = 1
        position = 1
        start = True

        while not self.stop:
            pixels = [0, position, 0, 0] * self.pixels_number

            self.show(pixels)
            time.sleep(0.02)

            if position > 20:
                start = False
                step = -1
            elif position < 1:
                step = 1

            position += step

    def wait(self):
        position = 0
        step = True

        while not self.stop:
            pixels = []
            for i in range(self.pixels_number):
                if i == position and step:
                    pixels += [0, 15, 15, 0]
                else:
                    pixels += [0] * 4

            self.show(pixels)
            time.sleep(0.5)

            if position > 11:
                position = 0

            if step:
                position += 1
            step = not step

    def timer(self, seconds=15):
        position = 0
        step = seconds / self.pixels_number

        while not self.stop:
            pixels = []
            for i in range(self.pixels_number):
                if i <= position:
                    pixels += [0, 5, 5, 5]
                else:
                    pixels += [0] * 4

            self.show(pixels)
            time.sleep(step)

            position += 1

    def off(self):
        self.show([0] * 4 * 12)
