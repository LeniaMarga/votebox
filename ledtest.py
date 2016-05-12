#!/usr/bin/env python3
import RPi.GPIO as GPIO
import atexit, time

# Globals
buttons = (6,4,18,22,25)
leds = (12,17,27,23,5)
states = [True for l in leds]

def buttonPress(channel):
    print(channel)
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

    try:
        while True:
            time.sleep(9999999999)  
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    atexit.register(exit)
    main()

