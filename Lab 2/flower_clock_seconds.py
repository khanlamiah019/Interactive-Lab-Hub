#!/usr/bin/env python3
"""
flower_clock_seconds.py

Seconds portion of a Flower Clock, built for the Adafruit Mini PiTFT -
135x240 Color TFT Add-on for Raspberry Pi (ST7789, SPI):
https://www.adafruit.com/product/4393

Ported (best-effort) from the described logic of the p5.js sketch at
https://github.com/khanlamiah019/the_flower_clock

Behavior:
    - A flower blooms (petals grow from the center outward) over the
      course of each 60-second minute.
    - At :00 the flower is fully closed (petal length ~ 0).
    - At :59 the flower is at full bloom.
    - The instant the minute rolls over, the flower resets and blooms
      again automatically (it reads live wall-clock time every frame).

NOTE: I could not fetch the actual contents of your sketch.js (small/
private repos aren't crawlable), so the petal shape, count, colors, and
easing curve here are my own interpretation of "flower blooms over each
second, restarts at 60." Paste your real sketch.js and I can make this an
exact 1:1 port.

--------------------------------------------------------------------------
ONE-TIME SETUP ON THE PI
--------------------------------------------------------------------------
1. This display uses SPI directly (not pygame/X11/framebuffer). If you
   previously installed Adafruit's kernel-driver "console mode" for this
   same screen, remove/disable it first -- it will conflict with this
   script talking to the display over SPI directly.

2. Make sure SPI is enabled:
       sudo raspi-config
       -> Interface Options -> SPI -> Enable

3. Install the required Python libraries (inside your venv):
       pip3 install adafruit-circuitpython-rgb-display pillow
       pip3 install adafruit-blinka   # if not already installed

4. Run it:
       python3 flower_clock_seconds.py

   Press Ctrl+C to quit.
--------------------------------------------------------------------------
"""

import math
import time

import board
import digitalio
from PIL import Image, ImageDraw
import adafruit_rgb_display.st7789 as st7789


# ------------------------------------------------------- display setup
# CS / DC / RST pins and the width/height/offset values below are
# Adafruit's own documented defaults for the Mini PiTFT 1.14" (135x240),
# straight from:
# https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/python-usage
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)
BAUDRATE = 24000000

spi = board.SPI()

disp = st7789.ST7789(
    spi,
    rotation=90,        # landscape orientation
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

# After a 90/270 rotation, swap width/height for landscape drawing
if disp.rotation % 180 == 90:
    WIDTH = disp.height   # 240
    HEIGHT = disp.width   # 135
else:
    WIDTH = disp.width
    HEIGHT = disp.height


# ---------------------------------------------------------------- settings
NUM_PETALS = 10           # petals around the center
MAX_PETAL_LEN = 55        # px, length of a fully bloomed petal (fits 135px height)
PETAL_WIDTH = 22          # px, widest part of a fully bloomed petal
BG_COLOR = (10, 10, 15)
CENTER_COLOR = (235, 180, 40)
PETAL_COLOR = (230, 90, 140)
TEXT_COLOR = (230, 230, 230)
FRAME_DELAY = 1 / 15      # Adafruit measured ~15 FPS max on this display


def bloom_progress(now=None):
    """
    Returns (seconds_elapsed_float, progress 0..1) for the CURRENT minute.
    seconds_elapsed_float includes the fractional second so growth is
    smooth instead of jumping once per second.
    """
    now = now if now is not None else time.time()
    local = time.localtime(now)
    frac = now - math.floor(now)
    seconds_elapsed = local.tm_sec + frac
    return seconds_elapsed, seconds_elapsed / 60.0


def eased(progress):
    """
    Ease linear 0..1 progress into a smooth blooming curve (quick growth
    early, settling into full bloom by the end of the minute).
    """
    return math.sin(progress * math.pi / 2)


def draw_flower(draw, cx, cy, progress):
    p = eased(progress)
    petal_len = MAX_PETAL_LEN * p

    for i in range(NUM_PETALS):
        angle = (2 * math.pi / NUM_PETALS) * i - math.pi / 2
        tip_x = cx + math.cos(angle) * petal_len
        tip_y = cy + math.sin(angle) * petal_len

        perp = angle + math.pi / 2
        half_w = (PETAL_WIDTH / 2) * p  # petals widen as they bloom too

        base1 = (cx + math.cos(perp) * half_w, cy + math.sin(perp) * half_w)
        base2 = (cx - math.cos(perp) * half_w, cy - math.sin(perp) * half_w)

        mid_x = cx + math.cos(angle) * (petal_len * 0.6)
        mid_y = cy + math.sin(angle) * (petal_len * 0.6)
        mid1 = (mid_x + math.cos(perp) * half_w * 0.6,
                mid_y + math.sin(perp) * half_w * 0.6)
        mid2 = (mid_x - math.cos(perp) * half_w * 0.6,
                mid_y - math.sin(perp) * half_w * 0.6)

        if petal_len > 1:
            draw.polygon(
                [base1, mid1, (tip_x, tip_y), mid2, base2],
                fill=PETAL_COLOR,
            )

    center_r = 8 + 5 * p
    draw.ellipse(
        (cx - center_r, cy - center_r, cx + center_r, cy + center_r),
        fill=CENTER_COLOR,
    )


def main():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    cx, cy = WIDTH // 2, HEIGHT // 2 - 6

    while True:
        seconds_elapsed, progress = bloom_progress()

        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=BG_COLOR)
        draw_flower(draw, cx, cy, progress)
        draw.text((4, HEIGHT - 14), f"{int(seconds_elapsed):02d}/60s", fill=TEXT_COLOR)

        disp.image(image)
        time.sleep(FRAME_DELAY)


if __name__ == "__main__":
    main()
