#!/usr/bin/python

import time
import os
import itertools
import yaml
import dbus
import select
import alsaaudio
from dbus.exceptions import DBusException
from dzentools import BarElement, ForegroundColour, Icon

BLUE = ForegroundColour("blue")
RED = ForegroundColour("red")
LBLUE = ForegroundColour("lightblue")
ICONS = Icon(os.path.dirname(__file__) + "/icons")

class Time(BarElement):
    update = lambda self: time.strftime("%A %d %b %H:%M:%S")


class Load(BarElement):
    def update(self):
        return BLUE(ICONS["load.xbm"] + " {0:.2f} {1:.2f} {2:.2f}".format(*os.getloadavg()))


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
        self.capacity = int(state["remaining capacity"].split()[0])
        #self.low = int(info["design capacity low"].split()[0])

        self.bat_status = state["charging state"].strip()
        if self.bat_status == "discharging":
            my_icon = "power-bat.xbm"
        else:
            my_icon = "power-ac.xbm"

        if self.capacity <= self.warning:
            my_col = RED
        else:
            my_col = LBLUE

        self.quantity = float(self.capacity)/self.max_capacity
        self.quality = float(self.max_capacity)/self.total_capacity
        ret = " {quantity:.0%}"
        return my_col(ICONS[my_icon] + ret.format(**self.__dict__))


class MprisPlayer(BarElement):
    def start(self):
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
    def start(self):
        self._poll = select.poll()
        self._poll.register(*alsaaudio.Mixer().polldescriptors()[0])

    def check_update(self):
        return self._poll.poll(0)
    
    def update(self):
        master = alsaaudio.Mixer()
        state = "vol-mute.xbm" if master.getmute()[0] else "vol-hi.xbm"
        vol = master.getvolume()[0]
        return LBLUE(ICONS[state] + " [{0}%]".format(vol))

class MocpPlayer(BarElement):
    def update(self):
        data = dict(line.split(":", 1) for line in os.popen("mocp -i"))
        ret = data.get("Title", "").strip() or data.get("File", "").strip()
        return ret or "Not Playing"


class Memory(BarElement):
    def update(self):
        with open("/proc/meminfo") as f:
            meminfo = yaml.load(f.read())
        mem_total = float(meminfo["MemTotal"][:-2])
        mem_needed = float(meminfo["Committed_AS"][:-2])
        return BLUE(ICONS["mem.xbm"] + " {0:0.2%}".format((mem_needed)/mem_total))


if __name__ == "__main__":
    lines = itertools.izip(Time(), Load(), Battery(), 
        MprisPlayer(), MocpPlayer(), Audio(), Memory(),
        )
    for line in lines:
        print(line)
        time.sleep(1)
