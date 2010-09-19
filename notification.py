#!/usr/bin/env python
'''notifications from dzen bar module
notification-daemon derived from 
http://github.com/halhen/statnot
'''
from thread import start_new_thread
import Queue
import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
from dzentools import BarElement
from basicelements import RED


class NotificationFetcher(dbus.service.Object):
    _id = 0
    queue = None

    @dbus.service.method("org.freedesktop.Notifications",
                         in_signature='susssasa{ss}i',
                         out_signature='u')
    def Notify(self, app_name, notification_id, app_icon,
               summary, body, actions, hints, expire_timeout):

        if not notification_id:
            self._id += 1
            notification_id = self._id
			
        text = ("%s %s" % (summary, body)).strip()
        self.queue.put(text)
        return notification_id
		
    @dbus.service.method("org.freedesktop.Notifications", in_signature='', out_signature='as')
    def GetCapabilities(self):
        return ("body")
	
    @dbus.service.signal('org.freedesktop.Notifications', signature='uu')
    def NotificationClosed(self, id_in, reason_in):
        pass

    @dbus.service.method("org.freedesktop.Notifications", in_signature='u', out_signature='')
    def CloseNotification(self, id):
        pass

    @dbus.service.method("org.freedesktop.Notifications", in_signature='', out_signature='ssss')
    def GetServerInformation(self):
        return ("statnot-like", "http://github.com/0Chuzz/dzentools", "0.0.1", "1")


class Notification(BarElement):
    DEFAULT_PARAMS = dict(
            colour=RED)

    def start(self):
        self.shown_notif = []

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        session_bus = dbus.SessionBus()
        self.name = dbus.service.BusName("org.freedesktop.Notifications",
                session_bus)
        self._nf = NotificationFetcher(session_bus,
        "/org/freedesktop/Notifications")
        self.queue = Queue.Queue()
        self._nf.queue = self.queue

        gobject.threads_init()
        self._loop = gobject.MainLoop()
        self._thread = start_new_thread(self._loop.run, tuple())

    def update(self):
        while not self.queue.empty():
            new = self.queue.get_nowait()
            self.shown_notif.append(new)
            self.queue.task_done()
        if self.shown_notif:
            show = self.shown_notif.pop(0)
            self.shown_notif.append(show)
        else:
            show = ' '
        return show


if __name__ == "__main__": #let's test
    import time
    for notif in Notification():
        print(notif)
        time.sleep(1)
