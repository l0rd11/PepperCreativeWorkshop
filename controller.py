#!/bin/sh
"exec" "`dirname $0`/venv/bin/ipython" "-i" "$0" "$@"
# shebang for virtualenv execution from any location
# credit: stackoverflow.com/questions/20095351
import datetime
import logging
import random
import qi
import time
import socket

import paho.mqtt.publish as publish
from IPython import get_ipython
from pyfiglet import figlet_format

from data.speech_samples import *





logger = logging.getLogger('pepperer')
NAO_IP = '192.168.1.101'
NAO_PORT = 9559


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP



LOCAL_IP = get_ip()
RESOURCES_SERVER = "http://" + LOCAL_IP + ":8000/"

session = qi.Session()
session.connect("tcp://" + NAO_IP + ":" + str(NAO_PORT))
tabletService = session.service("ALTabletService")
behavior_mng_service = session.service("ALBehaviorManager")



def exc_handler(self, etype, value, tb, tb_offset=None):
    """
    Replace default ipython behaviour when input cannot be parsed normally.

    Instead of raising SyntaxError or NameError, first check if input can
    be interpreted as some alias.
    """
    # parse
    if etype == SyntaxError:
        cmd, message = value.text.split(' ', 1)
        message = message.strip()
    else:
        # etype == NameError
        cmd = str(value)[6:-16]
        # because str(value) has form: "name '...' is not defined"
        message = None

    if cmd not in aliases:
        # no such alias defined, so use default ipython behaviour
        return self.showtraceback()

    # run
    func = aliases[cmd]
    if message == '?':
        print('Alias for function "{}".'.format(func.__name__))
        print(func.__doc__)
    else:
        func(message)


get_ipython().set_custom_exc((SyntaxError, NameError), exc_handler)


def say(message):
    """
    Say some message.

    It publishes to topic 'pepper/textToSpeech'.
    Examples:
        s hi
        s how are you doing?

    """
    publish.single('pepper/textToSpeech', message, hostname=NAO_IP)


def say_saved(expression):
    """
    Say some saved message.

    It publishes to topic 'pepper/textToSpeech'.
    Examples:
        # say some saved string
        msg = "greetings children!"
        ss msg

        # if given expression is a list, it will choose some random message from it to say
        yay = ['nice!', 'great!', 'awesome!']
        ss yay

        # if you don't want messages to repeat, call
        ss yay.pop()
        # after each message is said, it will be deleted from the list

    You can predefine those messages in data/speech_samples.py.

    """
    try:
        message = eval(expression)
    except NameError:
        logger.warning('There is no "{}" defined'.format(expression))
        return
    except Exception as exc:
        logger.warning('Couldn\'t evaluate "{}": {}'.format(expression, exc))
        return

    if type(message) == str:
        say(message)
    elif type(message) == list:
        say(random.choice(message))
    else:
        logger.warning('"{}" is a {}, and it should be a string or a list'
                       .format(expression, type(message)))


def publish_to_topic(topic):
    """
    Publish to a given topic using mqtt protocol.

    Examples:
        p pepper/textToSpeech

    """
    publish.single(topic, hostname=NAO_IP)


def video_begin(_):
    """
    Begin recording a video using robot camera.

    Uses topic 'pepper/video'.

    """
    timestamp = datetime.datetime.now().isoformat()
    publish.single('pepper/video',
                   "start_recording video-{}".format(timestamp),
                   hostname=NAO_IP)


def video_end(_):
    """
    End recording a video using robot camera.

    Uses topic 'pepper/video'.

    """
    publish.single('pepper/video',
                   "stop_recording",
                   hostname=NAO_IP)


def quit_(_):
    """
    Quit whole program.
    """
    exec('quit()')


def print_help(_):
    print('\nalias \tfunction')
    print('--------------------')
    for key, value in aliases.items():
        print('{} \t{}'.format(key, value.__name__))
    print('\nfor more info about some alias, type "<alias> ?"')


def show_image(image_name):
    tabletService.preLoadImage(RESOURCES_SERVER + image_name)
    tabletService.showImage(RESOURCES_SERVER + image_name)


def play_video(video_name):
    tabletService.playVideo(RESOURCES_SERVER + video_name)



def start_behavior(behavior_name):
    if (behavior_mng_service.isBehaviorInstalled(behavior_name)):
        # Check that it is not already running.
        if (not behavior_mng_service.isBehaviorRunning(behavior_name)):
            # Launch behavior. This is a blocking call, use _async=True if you do not
            # want to wait for the behavior to finish.
            behavior_mng_service.runBehavior(behavior_name, _async=True)
            time.sleep(0.5)
        else:
            print "Behavior is already running."

    else:
        print "Behavior not found."
        return


def stop_behavior(behavior_name):
    if (behavior_mng_service.isBehaviorRunning(behavior_name)):
        behavior_mng_service.stopBehavior(behavior_name)
        time.sleep(1.0)
    else:
        print "Behavior is already stopped."


def get_Behaviors(_):
    names = behavior_mng_service.getInstalledBehaviors()
    print "Behaviors on the robot:"
    print names

    names = behavior_mng_service.getRunningBehaviors()
    print "Running behaviors:"
    print names


aliases = {
    's': say,
    'ss': say_saved,
    'p': publish_to_topic,
    'vb': video_begin,
    've': video_end,
    'q': quit_,
    'si': show_image,
    'pv': play_video,
    'start_b': start_behavior,
    'stop_b': stop_behavior,
    'get_b': get_Behaviors,
    'h': print_help,
}

print(figlet_format('Pepperer', font='graffiti'))
print('\nfor help type h')
