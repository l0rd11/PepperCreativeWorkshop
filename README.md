
#Pepper Creative Workshop (PCW)
##It is Repository for Pepper workshop with children



### MQTT Topicks
#### Broker addres
```python
192.168.1.101
```
#### Speak in polish
```python
pepper/textToSpeech
```
#### camera topic
```python
pepper/video
```
##### start recording msg
```python
"start_recording" + " " + file_name
```
file_name is string with name of result file without extension 
##### stop recording msg
```python
"stop_recording" + " "
```

#### Sending message to mqtt broker
```python
import paho.mqtt.publish as publish

publish.single(topic,"cześć jak się masz", hostname=broker_address)
```

#### Choreography example speaking polish

```python
import paho.mqtt.publish as publish


class MyClass(GeneratedClass):
    def __init__(self):
        GeneratedClass.__init__(self)
        self.topic = "pepper/textToSpeech"
        self.broker_address="192.168.1.101"


    def onLoad(self):
        #put initialization code here
        pass

    def onUnload(self):
        #put clean-up code here
        pass

    def onInput_onStart(self):
        #self.onStopped() #activate the output of the box
        publish.single(self.topic, "jak się masz", hostname=self.broker_address)
        pass

    def onInput_onStop(self):
        self.onUnload() #it is recommended to reuse the clean-up as the box is stopped
        self.onStopped() #activate the output of the box
```

####Starting previously installed choreography activity 

documentation http://doc.aldebaran.com/2-5/naoqi/core/albehaviormanager.html

```python
behavior_mng_service = session.service("ALBehaviorManager")

#start the behavior
    # Check that the behavior exists.
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


# Stop the behavior.
    if (behavior_mng_service.isBehaviorRunning(behavior_name)):
        behavior_mng_service.stopBehavior(behavior_name)
        time.sleep(1.0)
    else:
        print "Behavior is already stopped."



```

