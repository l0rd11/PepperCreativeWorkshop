#!/bin/sh
"exec" "`dirname $0`/venv/bin/ipython" "-i" "$0" "$@"
# shebang for virtualenv execution from any location
# credit: stackoverflow.com/questions/20095351
import datetime
import logging
import random
import sys
import textwrap
import time
from collections import OrderedDict
import socket

import math
import paho.mqtt.publish as publish
import qi
from IPython import get_ipython
from pyfiglet import figlet_format
import paramiko

from data.speech_samples import *


logger = logging.getLogger('pepperer')
NAO_IP = '192.168.1.101'
NAO_PORT = 9559

def lunch_tablet_settings(password):
    p = paramiko.SSHClient()
    p.set_missing_host_key_policy(
        paramiko.AutoAddPolicy())  # This script doesn't work for me unless this line is added!
    p.connect(NAO_IP, port=22, username="nao", password=password)
    stdin, stdout, stderr = p.exec_command("qicli call ALTabletService._openSettings")
    opt = stdout.readlines()
    opt = "".join(opt)
    print(opt)


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


def head_camera_start(_):

    videoRecorderProxy.setFrameRate(10.0)
    videoRecorderProxy.setResolution(2)  # Set resolution to VGA (640 x 480)
    # We'll save a 5 second video record in /home/nao/recordings/cameras/
    timestamp = datetime.datetime.now().isoformat()
    videoRecorderProxy.startRecording("/home/nao/video", timestamp)
    print "Video record started."


def head_camera_stop(_):
    videoInfo = videoRecorderProxy.stopRecording()
    print "Video was saved on the robot: ", videoInfo[1]
    print "Total number of frames: ", videoInfo[0]


def get_behaviors(_):
    """
    Know which behaviors are on the robot.
    """
    # based on http://doc.aldebaran.com/2-5/naoqi/core/albehaviormanager.html

    names = behavior_mng_service.getInstalledBehaviors()
    print "Behaviors on the robot:"
    print names

    names = behavior_mng_service.getRunningBehaviors()
    print "Running behaviors:"
    print names


def launch_behavior(behavior_name):
    """
    Launch behavior.

    Example:
        l dance
    """
    # Check that the behavior exists.
    if not behavior_mng_service.isBehaviorInstalled(behavior_name):
        print "Behavior not found."
        return

    # Check that it is not already running.
    if behavior_mng_service.isBehaviorRunning(behavior_name):
        print "Behavior is already running."
        return

    # Launch behavior. This is a blocking call, use _async=True if you do not
    # want to wait for the behavior to finish.
    behavior_mng_service.runBehavior(behavior_name, _async=True)
    time.sleep(0.5)


def kill_behavior(behavior_name):
    """
    Kill behavior.

    Example:
        k dance
    """
    if behavior_mng_service.isBehaviorRunning(behavior_name):
        behavior_mng_service.stopBehavior(behavior_name)
        time.sleep(1.0)
    else:
        print "Behavior is already stopped."


def show_image(image_name):
    tabletService.preLoadImage(RESOURCES_SERVER + image_name)
    tabletService.showImage(RESOURCES_SERVER + image_name)


def play_video(video_name):
    tabletService.playVideo(RESOURCES_SERVER + video_name)


def grep_installed_behaviors(behavior_name):
    if behavior_name is None:
        behavior_name = ''
    for beh in behavior_mng_service.getInstalledBehaviors():
        if behavior_name in beh:
            print beh


def grep_running_behaviors(behavior_name):
    if behavior_name is None:
        behavior_name = ''
    for beh in behavior_mng_service.getRunningBehaviors():
        if behavior_name in beh:
            print beh


def quit_(_):
    """
    Quit whole program.
    """
    exec('quit()')


def print_help(_):
    print(textwrap.dedent('''
    to create your own alias type:
    aliases['cmd'] = your_function
    after that typing:
    cmd message   <=>   your_function('message')
    cmd           <=>   your_function(None)
    
    alias    function
    --------------------'''))
    for key, value in aliases.items():
        print('{:8} {}'.format(key, value.__name__))

    print(textwrap.dedent('''
    for more info about some alias, type "<alias> ?"
    '''))

def move_forward(_):
    posture_service.goToPosture("StandInit", 0.5)
    motion_service.moveTo(0.3, 0.0, 0.0, 5.0)

def move_back(_):
    posture_service.goToPosture("StandInit", 0.5)
    motion_service.moveTo(-0.3, 0.0, 0.0, 5.0)

def move(dist=0.3):
    posture_service.goToPosture("StandInit", 0.5)
    dist = float(dist)
    time = dist * 10.0
    motion_service.moveTo(dist, 0.0, 0.0, time)

def turn_around(rounds=0.5):
    posture_service.goToPosture("StandInit", 0.5)
    rounds = float(rounds)
    turns = rounds  * 2.0 * math.pi
    time = rounds * 8.0
    motion_service.moveTo(0.0, 0.0, turns, time)

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

def play_animation(gesture = "animations/Stand/Gestures/Hey_3"):
    future = _play_animation(gesture)
    future.value()

def _play_animation(gesture = "animations/Stand/Gestures/Hey_3"):
    return animation_player_service.run(gesture, _async=True)

def say_with_animation(message):
    gesture = message.split(' ')[-1]
    message = ' '.join(message.split(' ')[0:-1])
    future = _play_animation(gesture)
    publish.single('pepper/textToSpeech', message, hostname=NAO_IP)
    future.value()

aliases = OrderedDict([
    ('s', say),
    ('ss', say_saved),
    ('p', publish_to_topic),
    ('vb', video_begin),
    ('ve', video_end),
    ('g', get_behaviors),
    ('gi', grep_installed_behaviors),
    ('gr', grep_running_behaviors),
    ('l', launch_behavior),
    ('k', kill_behavior),
    ('si', show_image),
    ('pv', play_video),
    ('q', quit_),
    ('h', print_help),
    ('lts', lunch_tablet_settings),
    ('mf', move_forward),
    ('mb', move_back),
    ('m', move),
    ('tu', turn_around),
    ('pa', play_animation),
    ('swa', say_with_animation),
])




def exc_handler(self, etype, value, tb, tb_offset=None):
    """
    Replace default ipython behavior when input cannot be parsed normally.

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
        # no such alias defined, so use default ipython behavior
        return self.showtraceback()

    # run
    func = aliases[cmd]
    if message == '?':
        print('Alias for function "{}".'.format(func.__name__))
        print(textwrap.dedent(func.__doc__))
    else:
        func(message)



if __name__ == '__main__':
    get_ipython().set_custom_exc((SyntaxError, NameError), exc_handler)

    LOCAL_IP = get_ip()
    RESOURCES_SERVER = "http://" + LOCAL_IP + ":8000/"

    session = qi.Session()
    try:
        session.connect("tcp://{}:{}".format(NAO_IP, NAO_PORT))
    except RuntimeError:
        print("Can't connect to Naoqi at ip \"" + NAO_IP + "\" on port " + str(NAO_PORT) + ".\n"
              "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)

    tabletService = session.service("ALTabletService")
    behavior_mng_service = session.service("ALBehaviorManager")
    videoRecorderProxy = session.service("ALVideoRecorder")
    motion_service = session.service("ALMotion")
    posture_service = session.service("ALRobotPosture")
    animation_player_service = session.service("ALAnimationPlayer")

    print(figlet_format('Pepperer', font='graffiti'))
    print('\nfor help type h')
