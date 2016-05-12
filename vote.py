#!/usr/bin/env python3
import RPi.GPIO as GPIO
import atexit, time, threading, requests, logging, json
import snowflake
from itertools import chain

# Set up logger                                                                                                                                                
log = logging.getLogger(__name__)   

# Globals
buttons = (6,4,18,22,25)
leds = (12,17,27,23,5)
pressed = [0 for l in leds]
pwm = []

pause_time = 0.04   # s   LED fade speed 
bouncetime = 400    # ms  Switch debounce time
frame_rate = 100    # hz  duty cycle rate
max_bright = 90     # %   maximum duty rate percent
flash_time = 3000   # ms  LED flashing time
flash_each = 250    # ms  LED flash length (individual)

VOTE_URL = 'https://openlab.ncl.ac.uk/votebox/vote'


# Threaded worker for sending presses to server
def send_vote(index):
   payload = {'button': index, 'uuid': snowflake.snowflake()}
   headers = {'content-type': 'application/json'}
   
   log.debug(json.dumps(payload))
   response = requests.post(VOTE_URL, data=json.dumps(payload), headers=headers)
   if response.status_code != 200:
       log.error("(Status: {0}) {1}".format(response.status_code, response.text[:100].replace('\n',' ')))


def millis():
    return int(round(time.time() * 1000)) # time.time() returns a float in python 


def buttonPress(channel):
    ix = buttons.index(channel)
    pressed[ix] = millis()

    log.info("Pressed: {}".format(ix))

    # Send to server
    thread = threading.Thread(target=send_vote, args=(ix,))
    thread.start()


def exit():
    GPIO.cleanup()


def run_leds():
    # brightness 0 to 101 (and back)
    for i in chain(range(0,max_bright), range(max_bright,0,-1)):

        now = millis() # Do this once per inner loop (CPU usage)
        for j,p in enumerate(pwm):
            # flash LED if pressed
            if pressed[j]:
                if pressed[j] < (now - flash_time):
                    pressed[j] = 0 # Stop flashing
                else:
                    led_on = (now // flash_each) %2 
                    p.ChangeDutyCycle(led_on * 100)
            else: 
                p.ChangeDutyCycle(i)
        
        time.sleep(pause_time)


def main():
    GPIO.setmode(GPIO.BCM)

    for led in leds:
        GPIO.setup(led, GPIO.OUT)
        pwm.append(GPIO.PWM(led, frame_rate)) # @ 100Hz
        pwm[-1].start(0)

    for btn in buttons:
        GPIO.setup(btn, GPIO.IN) # Set the switch to be an input
        GPIO.add_event_detect(btn, GPIO.RISING, bouncetime=bouncetime) # rising edge detection
        GPIO.add_event_callback(btn, buttonPress)

    try:
        while True:
            run_leds()
    except KeyboardInterrupt:
        pass


def setup_logging():
    strh = logging.StreamHandler()
    strh.setLevel(logging.INFO)
    strh.setFormatter(logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s'))
    log.addHandler(strh) 
    log.setLevel(logging.INFO)


if __name__ == "__main__":
    atexit.register(exit)
    setup_logging()
    main()

