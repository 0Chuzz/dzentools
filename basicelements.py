#!/usr/bin/python

import time
import os
import itertools
from operator import methodcaller
import dbus
import select
import alsaaudio
from dbus.exceptions import DBusException
from dzentools import BarElement, ForegroundColour, Icon

BLUE = ForegroundColour("blue")
RED = ForegroundColour("red")
LBLUE = ForegroundColour("lightblue")
ICONS = Icon(os.path.dirname(__file__) + "/icons")

def procfile_parse(stream):
    ret = (line.split(':', 1) for line in stream if ':' in line)
    return dict((k.strip(), v.strip()) for k,v in ret)

class Time(BarElement):
    DEFAULT_PARAMS = dict(fmt="%A %d %b %H:%M:%S")
    update = lambda self: time.strftime(self.params['fmt'])


class Load(BarElement):
    DEFAULT_PARAMS = dict(colour=BLUE, icon="load.xbm")
    def update(self):
        ret = ICONS[self.params['icon']]
        ret += " {0:.2f} {1:.2f} {2:.2f}".format(*os.getloadavg())
        return self.params['colour'](ret)


class Battery(BarElement):
    DEFAULT_PARAMS = {
        'battdir': "/proc/acpi/battery/BAT0", 
        'icon_bat': "power-bat.xbm",
        'icon_ac': "power-ac.xbm",
        'colour': LBLUE, 
        'colour_warning': RED,
        }
    def update(self):
        battdir = self.params['battdir']
        info = {}
        with open(battdir + "/info") as f:
            info = procfile_parse(f)
        with open(battdir +  "/state") as f:
            state = procfile_parse(f)
        self.total_capacity = int(info["design capacity"].split()[0])
        self.max_capacity = int(info["last full capacity"].split()[0])
        self.warning = int(info["design capacity warning"].split()[0])
        self.capacity = int(state["remaining capacity"].split()[0])
        #self.low = int(info["design capacity low"].split()[0])

        self.bat_status = state["charging state"].strip()
        if self.bat_status == "discharging":
            my_icon = self.params['icon_bat'] 
        else:
            my_icon = self.params['icon_ac']

        if self.capacity <= self.warning:
            my_col = self.params['colour_warning']
        else:
            my_col = self.params['colour']

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
    DEFAULT_PARAMS = {
            'icon': 'vol-hi.xbm',
            'icon_mute': 'vol-mute.xbm',
            }
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
        data = os.popen("mocp -i")
        data = dict(line.split(":", 1) for line in data if ":" in line)
        ret = data.get("Title", "").strip() or data.get("File", "").strip()
        return ret or "Not Playing"


class Memory(BarElement):
    def update(self):
        with open("/proc/meminfo") as f:
            meminfo = procfile_parse(f)
        mem_total = float(meminfo["MemTotal"][:-2])
        mem_needed = float(meminfo["Committed_AS"][:-2])
        return BLUE(ICONS["mem.xbm"] + " {0:0.2%}".format((mem_needed)/mem_total))


class DiskUsage(BarElement):
    MPTS = [ "/", "/mnt/vista" ] # XXX
    def update(self):
        data = os.popen("df -Ph")
        ret = dict(line.split()[:-3:-1] for line in data if "/" in line)
        ret = " ".join("{0}:{1}".format(k,v) for k, v in ret.iteritems() if k in self.MPTS)
        return BLUE(ret)


if __name__ == "__main__":
    lines = itertools.izip(Time(), Load(), Battery(), 
        MprisPlayer(), MocpPlayer(), Audio(), Memory(),
        DiskUsage(),
        )
    for line in lines:
        print(line)
        time.sleep(1)
