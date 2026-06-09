# main.py on the Pico
import machine
import sys
import time

PIN_SWIM  = 16
PIN_SHOOT = 17

btn_swim  = machine.Pin(PIN_SWIM,  machine.Pin.IN, machine.Pin.PULL_UP)
btn_shoot = machine.Pin(PIN_SHOOT, machine.Pin.IN, machine.Pin.PULL_UP)

prev_swim  = 1
prev_shoot = 1

while True:
    s = btn_swim.value()
    f = btn_shoot.value()

    # Send on falling edge (button just pressed, active-low)
    if s == 0 and prev_swim == 1:
        sys.stdout.write("S")   # Swim
    if f == 0 and prev_shoot == 1:
        sys.stdout.write("F")   # Fire

    prev_swim  = s
    prev_shoot = f
    time.sleep_ms(20)