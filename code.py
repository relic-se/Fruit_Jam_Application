# SPDX-FileCopyrightText: 2025 Cooper Dalrymple (@relic-se)
#
# SPDX-License-Identifier: GPLv3

# load included modules if we aren't installed on the root path
if len(__file__.split("/")[:-1]) > 1:
    import adafruit_pathlib as pathlib
    if (modules_directory := pathlib.Path("/".join(__file__.split("/")[:-1])) / "lib").exists():
        import sys
        sys.path.append(str(modules_directory.absolute()))

import displayio
import sys
import supervisor
from terminalio import FONT
import time

from adafruit_display_text.label import Label
import adafruit_fruitjam.peripherals
import adafruit_usb_host_mouse

# get Fruit Jam OS config if available
try:
    import launcher_config
    config = launcher_config.LauncherConfig()
except ImportError:
    config = None

# setup display
displayio.release_displays()
try:
    adafruit_fruitjam.peripherals.request_display_config()  # user display configuration
except ValueError:  # invalid user config or no user config provided
    adafruit_fruitjam.peripherals.request_display_config(720, 400)  # default display size
display = supervisor.runtime.display

# setup audio, buttons, and neopixels
peripherals = adafruit_fruitjam.peripherals.Peripherals()

# user-defined audio output and volume
if config is not None:
    peripherals.audio_output = config.audio_output
    peripherals.volume = config.audio_volume
else:
    peripherals.audio_output = "headphone"
    peripherals.volume = 12

# create root group
root_group = displayio.Group()
display.root_group = root_group

# example text
root_group.append(Label(
    font=FONT, text="Hello, World!",
    anchor_point=(.5, .5),
    anchored_position=(display.width//2, display.height//2),
))

# mouse control
while True:
    if (mouse := adafruit_usb_host_mouse.find_and_init_boot_mouse("bitmaps/cursor.bmp")) is not None:
        mouse.tilegrid.x = display.width // 2
        mouse.tilegrid.y = display.height // 2
        root_group.append(mouse.tilegrid)

        timeouts = 0
        previous_pressed_btns = []
        while timeouts < 180:  # 3 seconds
            pressed_btns = mouse.update()
            if pressed_btns is None:
                timeouts += 1
            else:
                timeouts = 0
                if "left" in pressed_btns and (previous_pressed_btns is None or "left" not in previous_pressed_btns):
                    pass
            previous_pressed_btns = pressed_btns
            time.sleep(1/60)
        root_group.remove(mouse.tilegrid)
    time.sleep(1)
