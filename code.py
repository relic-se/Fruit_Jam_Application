# SPDX-FileCopyrightText: 2025 Cooper Dalrymple (@relic-se)
#
# SPDX-License-Identifier: GPLv3

# load included modules if we aren't installed on the root path
if len(__file__.split("/")[:-1]) > 1:
    lib_path = "/".join(__file__.split("/")[:-1]) + "/lib"
    try:
        import os
        os.stat(lib_path)
    except:
        pass
    else:
        import sys
        sys.path.append(lib_path)

import atexit
import displayio
import sys
from terminalio import FONT
import time

import adafruit_imageload
from adafruit_display_text.label import Label
import adafruit_usb_host_mouse
import relic_usb_host_gamepad

DISPLAY_REFRESH = 60
DISPLAY_WIDTH = 720
DISPLAY_HEIGHT = 400

try:
    import supervisor

except ImportError:
    import pygame
    from blinka_displayio_pygamedisplay import PyGameDisplay
    import relic_usb_host_gamepad.pygame

    BLINKA = True
    DISPLAY_SCALE = 2

else:
    import adafruit_fruitjam.peripherals

    BLINKA = False
    DISPLAY_SCALE = 1

if BLINKA:

    display = PyGameDisplay(
        width=DISPLAY_WIDTH*DISPLAY_SCALE, height=DISPLAY_HEIGHT*DISPLAY_SCALE,  # default display size
        icon="icon.bmp",
        caption="Application",
        native_frames_per_second=DISPLAY_REFRESH,
    )

else:

    # get Fruit Jam OS config if available
    try:
        import launcher_config
        config = launcher_config.LauncherConfig()
    except ImportError:
        config = None

    # setup display
    try:
        adafruit_fruitjam.peripherals.request_display_config()  # user display configuration
    except ValueError:  # invalid user config or no user config provided
        adafruit_fruitjam.peripherals.request_display_config(DISPLAY_WIDTH, DISPLAY_HEIGHT)  # default display size
    display = supervisor.runtime.display
    DISPLAY_WIDTH, DISPLAY_HEIGHT = display.width, display.height

    # setup audio, buttons, and neopixels
    peripherals = adafruit_fruitjam.peripherals.Peripherals(
        safe_volume_limit=(config.audio_volume_override_danger if config is not None else 0.75),
    )

    # user-defined audio output and volume
    peripherals.audio_output = config.audio_output if config is not None else "headphone"
    peripherals.volume = config.audio_volume if config is not None else 0.7

# create root group
root_group = displayio.Group(scale=DISPLAY_SCALE)
display.root_group = root_group

# example text
root_group.append(Label(
    font=FONT, text="Hello, World!",
    anchor_point=(0.5, 0.5),
    anchored_position=(DISPLAY_WIDTH//2, DISPLAY_HEIGHT//2),
))

def handle_key(key: str) -> None:
    pass

def handle_click(button: str, x: int, y: int) -> None:
    pass

def handle_button(id: int, pressed: bool) -> None:
    pass

def update() -> None:
    pass

if BLINKA:

    # setup mouse cursor
    mouse_bitmap, mouse_palette = adafruit_imageload.load(
        "/".join(adafruit_usb_host_mouse.__file__.split("/")[:-1]) + "/mouse_cursor.bmp",
        bitmap=displayio.Bitmap, palette=displayio.Palette
    )
    mouse_palette.make_transparent(0)
    mouse_tg = displayio.TileGrid(
        bitmap=mouse_bitmap, pixel_shader=mouse_palette,
        x=DISPLAY_WIDTH//2, y=DISPLAY_HEIGHT//2,
    )
    root_group.append(mouse_tg)

    # gamepad device
    gamepad = relic_usb_host_gamepad.pygame.Gamepad()

    def handle_event(event) -> None:
        if event.type == pygame.KEYDOWN:
            handle_key(event.unicode)

        elif event.type == pygame.MOUSEMOTION:
            mouse_tg.x = event.pos[0] // DISPLAY_SCALE
            mouse_tg.y = event.pos[1] // DISPLAY_SCALE

        elif event.type == pygame.MOUSEBUTTONDOWN:
            for i, btn in enumerate(adafruit_usb_host_mouse.BUTTONS):
                if event.button & (1 << i):
                    handle_click(btn, mouse_tg.x, mouse_tg.y)
                    break
                    
        else:
            gamepad.process_event(event)

    def prepare_update() -> None:
        for event in gamepad.events:
            handle_button(event.key_number, event.pressed)
        update()
        gamepad.reset_button_changes()

    display.event_loop(
        on_time=prepare_update,
        on_event=handle_event,
        events=(
            pygame.KEYDOWN,
            pygame.KEYUP,
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
        ) + relic_usb_host_gamepad.pygame.EVENT_TYPES,
        delay=1 / DISPLAY_REFRESH,
    )

else:

    # mouse device
    mouse = None
    if config is not None and config.use_mouse and (mouse := adafruit_usb_host_mouse.find_and_init_boot_mouse()) is not None:
        root_group.append(mouse.tilegrid)

    def atexit_callback() -> None:
        if mouse and mouse.was_attached and not mouse.device.is_kernel_driver_active(0):
            mouse.device.attach_kernel_driver(0)
    atexit.register(atexit_callback)

    # gamepad device
    gamepad = relic_usb_host_gamepad.Gamepad()

    # flush input buffer
    while supervisor.runtime.serial_bytes_available:
        sys.stdin.read(1)

    try:
        previous_pressed_btns = None
        last_timestamp = time.monotonic()
        while True:

            # keyboard input
            if (available := supervisor.runtime.serial_bytes_available) > 0:
                buffer = sys.stdin.read(available)
                while buffer:
                    key = buffer[0]
                    buffer = buffer[1:]
                    if key == "\x1b" and buffer and buffer[0] == "[" and len(buffer) >= 2:
                        key += buffer[:2]
                        buffer = buffer[2:]
                        if buffer and buffer[0] == "~":
                            key += buffer[0]
                            buffer = buffer[1:]
                    handle_key(key)
            
            # mouse input
            if mouse is not None and mouse.update() is not None:
                for btn in mouse.pressed_btns:
                    if previous_pressed_btns is None or btn not in previous_pressed_btns:
                        handle_click(btn, mouse.x, mouse.y)
                previous_pressed_btns = mouse.pressed_btns

            # gamepad input
            if gamepad.update():
                for event in gamepad.events:
                    handle_button(event.key_number, event.pressed)

            if (current_timestamp := time.monotonic()) - last_timestamp >= 1 / DISPLAY_REFRESH:
                update()
                last_timestamp = current_timestamp

    except KeyboardInterrupt:
        peripherals.deinit()
