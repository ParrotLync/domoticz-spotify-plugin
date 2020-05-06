# Spotify Plugin for Domoticz
#
# Author: ParrotLync
#
"""
<plugin key="SpotifyPlugin" name="Spotify Plugin" author="parrotlync" version="0.0.1" externallink="https://gitlab.com/parrotlync/domoticz-spotify-plugin">
    <description>
        <h2>Spotify Plugin</h2><br/>
    </description>
    <params>
        <param field="Mode1" label="Client ID" width="200px" required="true"/>
        <param field="Mode2" label="Client secret" width="200px" required="true"/>
        <param field="Mode3" label="Authorization code" width="300px" required="true"/>
        <param field="Mode4" label="Poll Interval (seconds)" width="100px" required="true" default=30/>
        <param field="Mode5" label="Debug" width="100px">
            <options>
                <option label="True" value="True"/>
                <option label="False" value="False" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
try:
    from Spotify import SpotifyConnection, SpotifyError
except ImportError:
    Domoticz.Error("Error importing SpotifyConnection. Is spotipy installed?")

# Unit defines
SPOTDEVICE = 1
SPOTVOLUME = 2
SPOTCONTROLS = 3


class BasePlugin:
    enabled = False
    hasTimedOut = False

    def __init__(self):
        self.spotify_devices = {}
        self.credentials = None
        self.spotify = None

    def register_devices(self):
        if SPOTDEVICE not in Devices:
            Domoticz.Debug("Device selector doesn't exist. Creating now.")
            devices = self.spotify.get_devices()
            selector_names = "Off"
            selector_actions = ""
            for device in devices:
                selector_names += "|{}".format(device.name)
                selector_actions += "|"
            dictOptions = {"LevelActions": selector_actions, "LevelNames": selector_names,
                           "LevelOffHidden": "false", "SelectorStyle": "1"}
            Domoticz.Device(Name="Playback device", Unit=SPOTDEVICE, TypeName="Selector Switch",
                            Image=5, Options=dictOptions, Used=1).Create()
        else:
            Domoticz.Debug("Device selector exists.")

        if SPOTVOLUME not in Devices:
            Domoticz.Debug("Device volume doesn't exist. Creating now.")
            Domoticz.Device(Name="Volume", Unit=SPOTVOLUME, Type=244, Subtype=73,
                            Switchtype=7, Image=8, Used=1).Create()
        else:
            Domoticz.Debug("Device volume exists.")

        if SPOTCONTROLS not in Devices:
            Domoticz.Debug("Device controls doesn't exist. Creating now.")
            
        else:
            Domoticz.Debug("Device controls exists.")

    def set_selector(self, name):
        dictOptions = Devices[SPOTDEVICE].Options
        list_names = dictOptions['LevelNames'].split('|')
        level = 0
        for level_name in list_names:
            if level_name == name:
                Devices[SPOTDEVICE].Update(1, str(level))
            level += 10

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters['Mode5'] == "True":
            Domoticz.Debugging(1)
        self.credentials = {'id': Parameters['Mode1'], 'secret': Parameters['Mode2']}
        try:
            self.spotify = SpotifyConnection(self.credentials, Parameters['Mode3'])
            Domoticz.Log("Connected to Spotify API")
        except SpotifyError as e:
            Domoticz.Error(e.msg)
        self.register_devices()
        Domoticz.Heartbeat(int(Parameters['Mode4']))

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if Unit == SPOTDEVICE:
            if Command == 'Set Level':
                devices = self.spotify.get_devices()
                index = int((Level / 10) - 1)
                device = devices[index]
                self.spotify.transfer_playback(device.id)
                Devices[SPOTDEVICE].Update(1, str(Level))
        elif Unit == SPOTVOLUME:
            if Command == 'Set Level':
                Devices[SPOTVOLUME].Update(2, str(Level))
                self.spotify.set_volume(Level)
            elif Command == 'Off':
                Devices[SPOTVOLUME].Update(0, 'Off')
                self.spotify.set_volume(0)
            elif Command == 'On':
                Devices[SPOTVOLUME].Update(1, 'On')
                self.spotify.set_volume(Level)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        if self.spotify is None:
            Domoticz.Log("No Spotify client detected. Requesting one now.")
            self.onStart()
        playback = self.spotify.get_current_playback()
        if playback is not None:
            volume = playback.device.volume
            Devices[SPOTVOLUME].Update(2, str(volume))

        # Update device selector
        devices = self.spotify.get_devices()
        selector_names = "Off"
        selector_actions = ""
        for device in devices:
            selector_names += "|{}".format(device.name)
            selector_actions += "|"
        dictOptions = {"LevelActions": selector_actions, "LevelNames": selector_names,
                       "LevelOffHidden": "false", "SelectorStyle": "1"}
        nValue, sValue = Devices[SPOTDEVICE].nValue, Devices[SPOTDEVICE].sValue
        Devices[SPOTDEVICE].Update(nValue, sValue, Options=dictOptions)


_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
