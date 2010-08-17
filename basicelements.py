#!/usr/bin/python

import time
import os
import itertools
import dbus
import select
import alsaaudio
from dbus.exceptions import DBusException
from mpdclient2 import connect
from dzentools import BarElement, ForegroundColour, Icon, DzenString

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
    DEFAULT_PARAMS = dict(app="org.mpris.vlc")

    def start(self):
        self.application = self.params['app']
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
            'colour': LBLUE,
            }
    def start(self):
        self._poll = select.poll()
        self._poll.register(*alsaaudio.Mixer().polldescriptors()[0])

    def check_update(self):
        return self._poll.poll(0)
    
    def update(self):
        master = alsaaudio.Mixer()
        state = self.params['icon_mute' if master.getmute()[0] else 'icon']
        vol = master.getvolume()[0]
        return self.params['colour'](ICONS[state] + " [{0}%]".format(vol))


class MocpPlayer(BarElement):
    def update(self):
        data = os.popen("mocp -i")
        data = dict(line.split(":", 1) for line in data if ":" in line)
        ret = data.get("Title", "").strip() or data.get("File", "").strip()
        return ret or "Not Playing"


class MpdPlayer(BarElement):
    def start(self):
        self.conn = connect()

    def update(self):
        _song = self.conn.currentsong()
        song = lambda x: _song.get(x, '')
        song_name = song('artist')
        if song_name: song_name += ' - '
        song_name += song('title') or song('file')
        return song_name or "Not Playing"

class Memory(BarElement):
    DEFAULT_PARAMS = {
            'icon': "mem.xbm",
            'colour': BLUE,
            }
    def update(self):
        with open("/proc/meminfo") as f:
            meminfo = procfile_parse(f)
        mem_total = float(meminfo["MemTotal"][:-2])
        mem_needed = float(meminfo["Committed_AS"][:-2])
        ret = ICONS[self.params['icon']] 
        ret += " {0:0.2%}".format((mem_needed)/mem_total)
        return self.params['colour'](ret)


class DiskUsage(BarElement):
    DEFAULT_PARAMS = {
        'partitions': [ "/", "/mnt/vista" ],
        'colour': BLUE,
        }

    def update(self):
        MPTS = self.params['partitions']
        data = os.popen("df -Ph")
        ret = dict(line.split()[:-3:-1] for line in data if "/" in line)
        ret = " ".join("{0}:{1}".format(k,v) for k, v in ret.iteritems() if k in MPTS)
        return self.params['colour'](ret)

class IMAPRecent(BarElement):
    DEFAULT_PARAMS = {
            'cmd' : "xclock",
            'acct-file': None,
            'wait' : 10*60,
            }
    def start(self):
        self._lasttime = time.time()

    def check_update(self):
        now = time.time()
        if now - self._lasttime > self.params['wait']:
            self._lasttime = now
            return True
        else:
            return False

    def update(self):
        return DzenString(("ca", self.params['cmd']), ("ca", ""))

if __name__ == "__main__":
    lines = itertools.izip(Time(), Load(), Battery(), 
        MprisPlayer(), MocpPlayer(), Audio(), Memory(),
        DiskUsage(),
        )
    for line in lines:
        print(line)
        time.sleep(1)
