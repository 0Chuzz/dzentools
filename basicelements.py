#!/usr/bin/python

import time
import os
import itertools
import yaml
import dbus
from dbus.exceptions import DBusException
from dzentools import BarElement, ForegroundColour

BLUE = ForegroundColour("blue")
GREEN = ForegroundColour("green")
ORANGE = ForegroundColour("orange")

class Time(BarElement):
    update = lambda self: time.strftime("%A %d %b %H:%M:%S")


class Load(BarElement):
    update = lambda self: BLUE("{0:.2f} {1:.2f} {2:.2f}".format(*os.getloadavg()))


class Battery(BarElement):
    def update(self):
        battdir = "/proc/acpi/battery/BAT0"
        with open(battdir + "/info") as f:
            info = yaml.load(f)
        with open(battdir +  "/state") as f:
            state = yaml.load(f)
        self.total_capacity = int(info["design capacity"].split()[0])
        self.max_capacity = int(info["last full capacity"].split()[0])
        self.warning = int(info["design capacity warning"].split()[0])
        self.low = int(info["design capacity low"].split()[0])
        self.bat_status = state["charging state"].strip()
        self.capacity = int(state["remaining capacity"].split()[0])
        self.quantity = float(self.capacity)/self.max_capacity
        self.quality = float(self.max_capacity)/self.total_capacity
        ret = "{bat_status} {quantity:.0%}"
        return GREEN(ret.format(**self.__dict__))


class MprisPlayer(BarElement):
    def __init__(self, **kw):
        super(MprisPlayer, self).__init__(**kw)
        self.application = "org.mpris.vlc"
        self.bus = dbus.SessionBus()

    def update(self):
        try:
            mpris = self.bus.get_object(self.application, "/Player")
            metadata = mpris.GetMetadata()
            if not metadata :
                raise DBusException
        except DBusException:
            return "Not Playing"
        else:
            metadata = dict((str(k), unicode(v).encode("utf-8", "replace")) 
                        for k, v in metadata.iteritems())
            return (metadata.get('nowplaying') or 
            (metadata.get('title', 'No title') + ' - ' 
            + metadata.get('artist', "No artist")))

class Audio(BarElement):
    def update(self):
        master = os.popen("amixer").read().split("Simple mixer control")[1]
        master = [x.strip() for x in master.strip().split("\n")]
        volume = master[-1].split()
        return ORANGE("Vol: {3} {5}".format(*volume))


if __name__ == "__main__":
    lines = itertools.izip( Time(), Load(), Battery(), MprisPlayer(), Audio())
    for line in lines:
        print(line)
        time.sleep(1)
