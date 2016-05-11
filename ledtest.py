#!/usr/bin/env python3
import RPi.GPIO as GPIO
import atexit, time
from itertools import chain

# Globals
buttons = (6,4,18,22,25)
leds = (12,17,27,23,5)
states = [True for l in leds]
pwm = []

pause_time = 0.02   # Pulse speed

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
        pwm.append(GPIO.PWM(led, 100))
        pwm[-1].start(100)
        #GPIO.output(led, True)

    for btn in buttons:
        GPIO.setup(btn, GPIO.IN) # Set the switch to be an input
        GPIO.add_event_detect(btn, GPIO.RISING, bouncetime=500) # rising edge detection
        GPIO.add_event_callback(btn, buttonPress)

    while True:
        time.sleep(1)
        # brightness 0 to 101 (and back)
        for i in chain(range(100,0,-1),range(0,100)):
            for j,p in enumerate(pwm):
                p.ChangeDutyCycle(i if states[j] else 0)
            time.sleep(pause_time)  

if __name__ == "__main__":
    atexit.register(exit)
    main()

