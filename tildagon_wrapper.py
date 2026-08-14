# Tildagon hardware wrapper, to enable programs to run on the EMF Camp badge.
# The Hardware_Wrapper class is passed into the constructor of your app so
# all hardware interaction (e.g. graphics drawing, button or key presses) is
# done through this hardware abstraction layer. This way the app does not need
# any hardware dependencies in the code and can run on any hardware that you
# write a suitable hardware wrapper for.
#
# Copyright (c) 2026 Paul Fretwell - aka 'Footleg'
#
# Released under the [GPL-3.0 License](https://opensource.org/license/gpl-3.0).

from machine import reset
from time import sleep_ms, sleep_us, ticks_diff, ticks_us, sleep
import asyncio
from events.input import Buttons, BUTTON_TYPES

class Hardware_Wrapper:
    # Methods to wrap timing functions. Just return MicroPython utime methods
    @staticmethod
    def sleep(seconds):
        """Sleep for the given number of seconds."""
        sleep(seconds)

    @staticmethod
    def sleep_ms(milliseconds):
        """Sleep for the given number of milliseconds."""
        sleep_ms(milliseconds)

    @staticmethod
    def sleep_us(microseconds):
        """Sleep for the given number of microseconds."""
        sleep_us(microseconds)

    @staticmethod
    def ticks_ms():
        """Return the current ticks elapsed in milliseconds."""
        return ticks_us() // 1000

    @staticmethod
    def ticks_us():
        """Return the current ticks elapsed in microseconds."""
        return ticks_us()

    @staticmethod
    def ticks_diff(ticks1, ticks2):
        """Calculate the difference between two ticks values."""
        return ticks_diff(ticks1, ticks2)

    @staticmethod
    def color_from_rgb(r, g, b):
        """ Convert RGB values to a color object of the correct type for this hardware"""
        return [r/255, g/255, b/255]

    # Map key constants used for control.
    # Different apps ask for control inputs for different purposes, 
    # so we have duplicate mappings of the badge buttons here to suit
    # multiple apps.
    KEY_UP = BUTTON_TYPES["CANCEL"]
    KEY_DOWN = BUTTON_TYPES["CANCEL"]
    KEY_LEFT = BUTTON_TYPES["LEFT"]
    KEY_RIGHT = BUTTON_TYPES["RIGHT"]

    KEY_START = BUTTON_TYPES["CONFIRM"]
    KEY_FIRE = BUTTON_TYPES["DOWN"]
    KEY_RUN = BUTTON_TYPES["UP"]
    KEY_SHIELD = BUTTON_TYPES["CONFIRM"]

    def __init__(self):
        self.width = 240
        self.height = 240
        self.circular = True
        self.fontWidth = 16
        self.fontHeight = 20
        self.black = [0, 0, 0]
        self.white = [1, 1, 1]
        self.red = [1, 0, 0]
        self.green = [0, 1, 0]
        self.blue = [0, 0, 1]
        self.cyan = [0, 1, 1]
        self.magenta = [1, 0, 1]
        self.yellow = [1, 1, 0]
        self.lines = []
        self.rects = [(0,0,239,239,self.black)] # Ensures screen is cleared on first app draw
        self.circles = []
        self.texts = []

    def show(self):
        pass

    def fill(self, colour):
        self.rects.append((0,0,239,239,self.black))

    def fill_rect(self, x, y, w, h, colour):
        self.rects.append((x, y, w, h, colour))

    def text(self, text, x, y, colour):
        self.texts.append((text, x, y, colour))

    def line(self, x1, y1, x2, y2, colour):
        self.lines.append((x1, y1, x2, y2, colour))

    def pixel(self, x, y, colour):
        self.fill_rect(x, y, 2, 2, colour)

    def circle(self, x, y, radius, colour, filled=True):
        self.circles.append((int(x), int(y), max(int(radius), 1), colour, filled))

    def setBtnStates(self, button_states):
        self.button_states = button_states

    def is_key_held(self, key):
        # Check if a key is currently being held
        return self.button_states.get(key) 

    def create_timer(self):
        print("Creating Timer")
        return TIMER()

    def reset(self):
        reset()

    def drawFromCaches(self,ctx):
        for rect in self.rects:
            r,b,g = rect[4]
            ctx.rgb(r,b,g)
            ctx.rectangle(rect[0]-120, rect[1]-120, rect[2], rect[3]).fill()
        self.rects.clear()
        for circle in self.circles:
            r,b,g = circle[3]
            if circle[4]:
                ctx.rgb(r,b,g).arc(circle[0]-120, circle[1]-120, circle[2], 0, 2 * math.pi, True).fill()
            else:
                ctx.rgb(r,b,g).arc(circle[0]-120, circle[1]-120, circle[2], 0, 2 * math.pi, True).stroke()
        self.circles.clear()
        for line in self.lines:
            r,b,g = line[4]
            ctx.rgb(r,b,g).begin_path()
            ctx.move_to(line[0]-120, line[1]-120)
            ctx.line_to(line[2]-120, line[3]-120)
            ctx.stroke()
        self.lines.clear()
        for item in self.texts:
            r,b,g = item[3]
            ctx.rgb(r,b,g).move_to(item[1]-120,item[2]-120+self.fontHeight).text(item[0])
        self.texts.clear()

class TIMER:
    # Define timer modes as constants
    ONE_SHOT = 0
    PERIODIC = 1

    def __init__(self):
        self._task = None
        self._callback = None
        self._args = None
        self._period = 0
        self._mode = TIMER.ONE_SHOT

    def init(self, period, mode, callback=None, arg=None):
        """
        Initialize the timer.
        """
        self.deinit() # Reset in case it already fired before being reinitialized
        self._period = period / 1000.0  # Convert to seconds
        self._mode = mode
        self._callback = callback
        
        # Ensure args are in a tuple format for calling
        if arg is not None:
            self._args = arg if isinstance(arg, tuple) else (arg,)
        else:
            self._args = ()

        self.start()

    def deinit(self):
        """Deinitialize the timer and stop background loops."""
        if self._task is not None:
            self._task.cancel()
            self._task = None

    def start(self):
        """Start the timer by creating an asyncio task."""
        self.deinit()
        self._task = asyncio.create_task(self._run_timer_loop())

    async def _run_timer_loop(self):
        """Internal async loop that handles delays and callbacks."""
        try:
            if self._mode == TIMER.ONE_SHOT:
                await asyncio.sleep(self._period)
                self._execute_callback()
            elif self._mode == TIMER.PERIODIC:
                while True:
                    await asyncio.sleep(self._period)
                    self._execute_callback()
        except asyncio.CancelledError:
            # Handle graceful cancellation when deinit() is called
            pass

    def _execute_callback(self):
        """Safely execute the callback."""
        if self._callback is not None:
            try:
                self._callback(*self._args)
            except Exception as e:
                print(f"Error in TIMER callback: {e}")
