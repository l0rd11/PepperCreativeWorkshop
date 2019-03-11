#!/bin/sh
"exec" "`dirname $0`/venv/bin/ipython" "-i" "$0" "$@"
# shebang for virtualenv execution from any location
# credit: stackoverflow.com/questions/20095351
import datetime
import logging
import random

import paho.mqtt.publish as publish
from IPython import get_ipython
from pyfiglet import figlet_format

from data.speech_samples import *

logger = logging.getLogger('pepperer')
NAO_IP = '192.168.1.101'


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


aliases = {
    's': say,
    'ss': say_saved,
    'p': publish_to_topic,
    'vb': video_begin,
    've': video_end,
    'q': quit_,
    'h': print_help,
}

print(figlet_format('Pepperer', font='graffiti'))
print('\nfor help type h')
