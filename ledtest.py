#!/usr/bin/env python3
import RPi.GPIO as GPIO
import atexit, time

# Globals
buttons = (6,)
leds = (12,)
states = [True for l in leds]

def buttonPress(channel):
    ix = buttons.index(channel)
    states[ix] = not states[ix]
    GPIO.output(leds[ix], states[ix])

def exit():
    print("GPIO Clean Up!")
    GPIO.cleanup()

def main():
    GPIO.setmode(GPIO.BCM)

    for led in leds:
        GPIO.setup(led, GPIO.OUT)
        GPIO.output(led, True)

    for btn in buttons:
        GPIO.setup(btn, GPIO.IN) # Set the switch to be an input
        GPIO.add_event_detect(btn, GPIO.RISING, bouncetime=500) # rising edge detection
        GPIO.add_event_callback(btn, buttonPress)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    atexit.register(exit)
    main()

