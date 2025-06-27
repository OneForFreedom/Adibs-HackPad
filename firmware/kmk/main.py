import board
import digitalio
import rotaryio
import busio
import time
from adafruit_ssd1306 import SSD1306_I2C
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# I2C for OLED
i2c = busio.I2C(board.GP15, board.GP14)
oled = SSD1306_I2C(128, 32, i2c)

# Rotary encoder setup
encoder = rotaryio.IncrementalEncoder(board.GP7, board.GP8)
last_position = encoder.position

# Keyboard HID
kbd = Keyboard()

# Keypad matrix pins
rows_pins = [board.GP2, board.GP3, board.GP4]
cols_pins = [board.GP5, board.GP6, board.GP9]

rows = []
for pin in rows_pins:
    r = digitalio.DigitalInOut(pin)
    r.direction = digitalio.Direction.OUTPUT
    r.value = True
    rows.append(r)

cols = []
for pin in cols_pins:
    c = digitalio.DigitalInOut(pin)
    c.direction = digitalio.Direction.INPUT
    c.pull = digitalio.Pull.DOWN
    cols.append(c)

key_map = {
    (0, 0): 'VOL_DOWN',
    (0, 1): 'MUTE',
    (0, 2): 'VOL_UP',
    (1, 0): 'PREV',
    (1, 1): 'PLAY_PAUSE',
    (1, 2): 'NEXT',
    (2, 0): 'CTRL_C',
    (2, 1): 'CTRL_V',
    (2, 2): 'CTRL_X',
}

def send_key(action):
    if action == 'VOL_DOWN':
        kbd.send(Keycode.VOLUME_DECREMENT)
    elif action == 'VOL_UP':
        kbd.send(Keycode.VOLUME_INCREMENT)
    elif action == 'MUTE':
        kbd.send(Keycode.MUTE)
    elif action == 'PREV':
        kbd.send(Keycode.MEDIA_PREVIOUS_TRACK)
    elif action == 'PLAY_PAUSE':
        kbd.send(Keycode.MEDIA_PLAY_PAUSE)
    elif action == 'NEXT':
        kbd.send(Keycode.MEDIA_NEXT_TRACK)
    elif action == 'CTRL_C':
        kbd.press(Keycode.CONTROL)
        kbd.send(Keycode.C)
        kbd.release_all()
    elif action == 'CTRL_V':
        kbd.press(Keycode.CONTROL)
        kbd.send(Keycode.V)
        kbd.release_all()
    elif action == 'CTRL_X':
        kbd.press(Keycode.CONTROL)
        kbd.send(Keycode.X)
        kbd.release_all()

volume = 50
last_activity = time.monotonic()
oled_on = True
OLED_TIMEOUT = 120
showing_volume = False

def draw_volume_bar(vol):
    oled.fill(0)
    height = int((vol / 100) * 32)
    for y in range(32 - height, 32):
        oled.fill_rect(60, y, 8, 1, 1)
    oled.text("VOL", 50, 0, 1)
    oled.show()

def draw_datetime():
    # For demo, use system time, replace with RTC if available
    from time import localtime
    t = localtime()
    days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    day_str = days[t.tm_wday - 1] if t.tm_wday > 0 else days[6]
    day_num = t.tm_mday
    month_str = months[t.tm_mon - 1]
    year_str = str(t.tm_year)

    oled.fill(0)
    oled.text(day_str, 0, 0, 1)
    oled.text(str(day_num), 0, 12, 1)
    oled.text(month_str, 40, 0, 1)
    oled.text(year_str, 40, 12, 1)
    oled.text(f"{t.tm_hour:02}:{t.tm_min:02}", 0, 24, 1)
    oled.show()

while True:
    now = time.monotonic()

    pressed_key = None
    for r_idx, row in enumerate(rows):
        row.value = False
        for c_idx, col in enumerate(cols):
            if col.value:
                pressed_key = (r_idx, c_idx)
        row.value = True

    if pressed_key:
        last_activity = now
        if showing_volume:
            showing_volume = False
            oled.poweron()
        action = key_map.get(pressed_key)
        if action:
            send_key(action)

    current_position = encoder.position
    if current_position != last_position:
        last_activity = now
        showing_volume = True
        oled.poweron()

        diff = current_position - last_position
        last_position = current_position

        volume += diff
        if volume < 0:
            volume = 0
        elif volume > 100:
            volume = 100

        draw_volume_bar(volume)

    if not showing_volume and oled_on:
        draw_datetime()

    if now - last_activity > OLED_TIMEOUT:
        if oled_on:
            oled.fill(0)
            oled.show()
            oled.poweroff()
            oled_on = False
    else:
        if not oled_on:
            oled.poweron()
            oled_on = True

    time.sleep(0.1)
