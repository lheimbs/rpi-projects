#!/usr/bin/env python3

import apa102
import time
import threading
from gpiozero import LED
import argparse

try:
    import queue as Queue
except ImportError:
    import Queue as Queue

from led_patterns import LedPattern


class Pixels:
    PIXELS_N = 12

    def __init__(self, pattern=LedPattern):
        self.pattern = pattern(show=self.show)

        self.dev = apa102.APA102(num_led=self.PIXELS_N)

        self.power = LED(5)
        self.power.on()

        self.queue = Queue.Queue()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

        self.last_direction = None

    def alexa_wakeup(self, direction=0):
        self.last_direction = direction

        def f():
            self.pattern.alexa_wakeup(direction)

        self.put(f)

    def alexa_listen(self):
        if self.last_direction:

            def f():
                self.pattern.alexa_wakeup(self.last_direction)

            self.put(f)
        else:
            self.put(self.pattern.alexa_listen)

    def alexa_speak(self):
        self.put(self.pattern.alexa_speak)

    def google_wakeup(self, direction=0):
        self.last_direction = direction

        def f():
            self.pattern.google_wakeup(direction)

        self.put(f)

    def google_listen(self):
        if self.last_direction:

            def f():
                self.pattern.google_wakeup(self.last_direction)

            self.put(f)
        else:
            self.put(self.pattern.google_listen)

    def google_speak(self):
        self.put(self.pattern.google_speak)

    def off(self):
        self.put(self.pattern.off)

    def put(self, func):
        self.pattern.stop = True
        self.queue.put(func)

    def _run(self):
        while True:
            func = self.queue.get()
            self.pattern.stop = False
            func()

    def show(self, data):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(
                i, int(data[4 * i + 1]), int(data[4 * i + 2]), int(data[4 * i + 3])
            )

        self.dev.show()


if __name__ == "__main__":
    start = time.time()
    methods = [
        func
        for func in dir(LedPattern)
        if callable(getattr(LedPattern, func)) and "__" not in func
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", choices=methods)
    parser.add_argument("-t", type=int)
    args = parser.parse_args()

    pixels = Pixels()

    if args.t:
        t = args.t
    else:
        t = 5

    if args.s:
        try:
            caller = getattr(pixels, args.s)
            if args.s == "timer":
                caller(t)
            else:
                caller()
        except AttributeError:
            led_caller = getattr(pixels.pattern, args.s)
            if led_caller.__code__.co_argcount > 1:

                def f():
                    led_caller(t)

                pixels.put(f)
            else:
                pixels.put(led_caller)
        time.sleep(t)
        pixels.off()
        time.sleep(1)
    else:
        while True:

            try:
                pixels.wakeup()
                time.sleep(3)
                pixels.think()
                time.sleep(3)
                pixels.speak()
                time.sleep(6)
                pixels.off()
                time.sleep(3)
            except KeyboardInterrupt:
                break

        pixels.off()
        time.sleep(1)
    print(time.time() - start)
