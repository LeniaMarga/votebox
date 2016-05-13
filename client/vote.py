#!/usr/bin/env python3
import RPi.GPIO as GPIO
import atexit, os, time, threading, requests, logging, json, itsdangerous, base64
import snowflake
from itertools import chain

# Set up logger                                                                                                                                                
log = logging.getLogger(__name__)   

# Globals
buttons = (6,25,22,18,4)
leds = (12,5,23,27,17)
pressed = [0 for l in leds]
pwm = []

pause_time = 0.08   # s   LED fade speed 
bouncetime = 400    # ms  Switch debounce time
frame_rate = 100    # hz  duty cycle rate
max_bright = 50     # %   maximum duty rate percent
min_bright = 5      # %   minimum  "
flash_time = 3000   # ms  LED flashing time
flash_each = 250    # ms  LED flash length (individual)

SERVICE_URL = 'https://openlab.ncl.ac.uk/votebox/'
CONFIG_FILE = 'auth.json'
UUID = snowflake.snowflake()
state_ok = False

config = {}
with open(CONFIG_FILE) as fil:
    config = json.load(fil)


# Generate an auth token
def get_auth_token():
    # Generate a cryptographically random number for the token
    tok = base64.b64encode(os.urandom(32))
    # Sign it with the API key, giving us a token!
    s = itsdangerous.TimestampSigner(config['key'])
    return s.sign(tok).decode('utf-8')


# Threaded worker for sending presses to server
def send_vote(index):
    payload = {'button': index, 'uuid': UUID}
    headers = {'content-type': 'application/json'}
   
    log.debug(json.dumps(payload))
    response = requests.post(SERVICE_URL + 'vote', data=json.dumps(payload), headers=headers, auth=(UUID, get_auth_token()))
    if response.status_code != 200:
        error_state("(Status: {0}) {1}".format(response.status_code, response.text[:100].replace('\n',' ')))
    else:
        error_state(clear=True)


def test_connection():
    try:
        response = requests.get(SERVICE_URL + 'ping', timeout=10, auth=(UUID, get_auth_token()))
    except Exception as e:
        if not connection_error: # Only log these messages once
            error_state("Could not ping SERVICE_URL {0}. Exception: {1}".format(SERVICE_URL, e))
        test_connection.error = True
    else:
        if response.status_code == 200:
            error_state(clear=True)
            log.info("Connection tested and working")
            test_connection.error = False
        elif not test_connection.error: # Only log these messages once
            error_state("Connection opened but bad response ({}) from server!".format(response.status_code))
            test_connection.error = True
#static
test_connection.error = False


def error_state(msg=None, clear=False):
    global state_ok

    state_ok = False or clear
    if not state_ok:
        log.error("Entered error state" if not msg else msg)


def millis():
    return int(round(time.time() * 1000)) # time.time() returns a float in python 


def buttonPress(channel):
    ix = buttons.index(channel)
    pressed[ix] = millis()

    log.info("Pressed: {}, GPIO {}".format(ix, channel))

    # Send to server
    thread = threading.Thread(target=send_vote, args=(ix,))
    thread.start()


def exit():
    GPIO.cleanup()


def service_leds():
    # brightness 0 to 101 (and back)
    for i in chain(range(min_bright,max_bright), range(max_bright,min_bright,-1)):

        now = millis() # Do this once per inner loop (CPU usage)
        led_on = (now // flash_each) %2 

        for j,p in enumerate(pwm):

            # Service error state 
            if not state_ok:
                p.ChangeDutyCycle(led_on * max_bright if j==0 else 0)
                continue

            # flash LED if pressed
            elif pressed[j]:
                if pressed[j] < (now - flash_time):
                    pressed[j] = 0 # Stop flashing
                else:
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
            service_leds()

            if not state_ok:
                test_connection()

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
    test_connection()
    main()

