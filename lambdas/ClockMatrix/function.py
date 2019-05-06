#
# GG Lambda
#
# gg-er-clock-matrix

# resource that must be affiliated with the lambda:
# /dev/gpiomem, OS group gpio, rw
# /dev/spidev0.0, OS group spi, rw
# /dev/spidev0.1, OS group spi, rw


import greengrasssdk
import json
import logging
import os
import sys
import time

from datetime import datetime, timedelta
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, LCD_FONT
from threading import Timer

# globals
code = '{}'.format(os.environ['ESCAPE_CODE'])
display_mode = '{}'.format(os.environ['ESCAPE_DISPLAY_MODE'])
topic = 'data/er/{}/monitoring'.format(os.environ['AWS_IOT_THING_NAME'])

show_code = False
show_code_times = 10
show_code_counter = 0

switch_state = None

cascaded = 5
orientation = 90
rotate = 0

prev_time_of_day = '99:99'
displaying_code = False

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(filename)s:%(lineno)s - %(funcName)s: %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)


def display_time():
    global displaying_code, prev_time_of_day
    displaying_code = False
    daylight_saving_time = datetime.now() + timedelta(hours=1)  # change hour to zero for winter time
    time_of_day = daylight_saving_time.strftime('%H:%M')

    if time_of_day == prev_time_of_day:
        return
    else:
        logger.info("time changed: time_of_day: {} prev_time_of_day: {}".format(time_of_day, prev_time_of_day))
        prev_time_of_day = time_of_day

    if display_mode == 'static':
        with canvas(device) as draw:
            text(draw, (1, 0), time_of_day, fill="white", font=proportional(CP437_FONT))
    else:
        show_message(device, time_of_day, fill="white", font=proportional(CP437_FONT))


def display_code():
    global displaying_code, prev_time_of_day
    prev_time_of_day = '99:99'

    if displaying_code:
        return

    if display_mode == 'static':
        with canvas(device) as draw:
            text(draw, (6, 0), code, fill="white", font=proportional(LCD_FONT))
    else:
        show_message(device, code, fill="white", font=proportional(LCD_FONT), scroll_delay=0.1)

    displaying_code = True


def show_clock():
    global show_code, show_code_counter, switch_state
    logger.info("in show_clock")

    if show_code_counter > show_code_times:
        show_code = False

    logger.info(
        "show_code: {} show_code_counter: {} show_code_times: {} switch_state: {}".format(show_code, show_code_counter,
                                                                                          show_code_times,
                                                                                          switch_state))

    if not show_code and switch_state == 'off':
        display_time()
    elif switch_state == 'on':
        display_code()
    elif show_code:
        display_code()
        show_code_counter += 1
    else:
        display_time()

    Timer(0.2, show_clock).start()


#####################
# Creating a greengrass core sdk client
logger.info("creating gg client")
c_gg = greengrasssdk.client('iot-data')

os.environ['TZ'] = 'BST'
time.tzset()
logger.info("timezone: {}".format(time.tzname))

logger.info("creating serial and device for matrix")
serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, cascaded=cascaded,
                 block_orientation=orientation, rotate=rotate)
logger.info("serial: {} device: {}".format(serial, device))

logger.info("starting clock")
show_clock()


# This is a dummy handler because our lambda function is long-lived and will not be invoked
# Instead the code above will be executed in an infinite loop for our example
def lambda_handler(event, context):
    global switch_state
    logger.info("event: {}".format(event))

    response = c_gg.publish(
        topic=topic,
        payload=json.dumps({"event": '{}'.format(event)})
    )
    logger.info("response: {}".format(response))

    try:
        if event['state']['reported']['switch'] == 'on' or event['state']['reported']['switch'] == 'off':
            switch_state = event['state']['reported']['switch']
            logger.info("switch_state: {}".format(switch_state))
        else:
            logger.error("unknown switch state: {}".format(event['state']['reported']['switch']))

    except Exception as e:
        logger.error("event processing: {}".format(e))

    return
