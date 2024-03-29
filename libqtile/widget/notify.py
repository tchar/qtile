# -*- coding: utf-8 -*-
# Copyright (c) 2011 Florian Mounier
# Copyright (c) 2011 Mounier Florian
# Copyright (c) 2012 roger
# Copyright (c) 2012-2014 Tycho Andersen
# Copyright (c) 2012-2013 Craig Barnes
# Copyright (c) 2013 Tao Sauvage
# Copyright (c) 2014 Sean Vig
# Copyright (c) 2014 Adi Sieker
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from os import path

from libqtile import bar, pangocffi, utils
from libqtile.notify import Notification, notifier
from libqtile.widget import base


class Notify(base._TextBox):
    """A notify widget"""
    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("foreground_urgent", "ff0000", "Foreground urgent priority colour"),
        ("foreground_low", "dddddd", "Foreground low priority  colour"),
        (
            "default_timeout",
            None,
            "Default timeout (seconds) for notifications"
        ),
        ("audiofile", None, "Audiofile played during notifications"),
    ]

    def __init__(self, width=bar.CALCULATED, **config):
        base._TextBox.__init__(self, "", width, **config)
        self.add_defaults(Notify.defaults)
        notifier.register(self.update)
        notifier.register_delete(self.delete)
        self.current_notif = None

        self.add_callbacks({
            'Button1': self.clear,
            'Button3': self.clear_all,
            'Button4': self.prev,
            'Button5': self.next,
        })

    def _configure(self, qtile, bar):
        base._TextBox._configure(self, qtile, bar)
        self.layout = self.drawer.textlayout(
            self.text,
            self.foreground,
            self.font,
            self.fontsize,
            self.fontshadow,
            markup=True
        )

    def set_notif_text(self, notif):
        self.text = pangocffi.markup_escape_text(notif.summary)
        urgency = Notification.Urgency(notif)
        if urgency != Notification.Urgency.NORMAL:
            self.text = '<span color="%s">%s</span>' % (
                utils.hex(
                    self.foreground_urgent
                    if urgency == Notification.Urgency.CRITICAL
                    else self.foreground_low
                ),
                self.text
            )
        if notif.body:
            self.text = '<span weight="bold">%s</span> - %s' % (
                self.text, pangocffi.markup_escape_text(notif.body)
            )
        if self.audiofile and path.exists(self.audiofile):
            self.qtile.cmd_spawn("aplay -q '%s'" % self.audiofile)

    def update(self, notif):
        self.qtile.call_soon_threadsafe(self.real_update, notif)

    def real_update(self, notif):
        self.set_notif_text(notif)
        self.current_notif = notif
        if notif.timeout and notif.timeout > 0:
            self.timeout_add(notif.timeout / 1000, notifier.delete, (notif, ))
        elif self.default_timeout:
            self.timeout_add(self.default_timeout, notifier.delete, (notif, ))
        self.bar.draw()
        return True

    def delete(self, *notifs):
        self.qtile.call_soon_threadsafe(self.real_delete, *notifs)

    def real_delete(self, *notifs):
        if not self.current_notif:
            return False

        notif_ids = set(notif.id for notif in notifs)
        if self.current_notif.id not in notif_ids:
            return False

        # Show next notification on delete
        # If there is no next show a previous one
        next_notif = notifier.next(self.current_notif)
        if not next_notif:
            next_notif = notifier.prev(self.current_notif)

        self.current_notif = next_notif
        # If there is neither next or prev notif text should be empty
        if not next_notif:
            self.text = ''
        else:
            self.set_notif_text(next_notif)
        self.bar.draw()

    def display(self):
        self.set_notif_text(self.current_notif)
        self.bar.draw()

    def clear_all(self):
        notifier.delete_all()

    def clear(self):
        notifier.delete(self.current_notif)

    def prev(self):
        prev_notif = notifier.prev(self.current_notif)
        if prev_notif:
            self.current_notif = prev_notif
            self.display()

    def next(self):
        next_notif = notifier.next(self.current_notif)
        if next_notif:
            self.current_notif = next_notif
            self.display()

    def cmd_display(self):
        """Display the notifcication"""
        self.display()

    def cmd_clear(self):
        """Clear the notification"""
        self.clear()

    def cmd_toggle(self):
        """Toggle showing/clearing the notification"""
        if self.text == '':
            self.display()
        else:
            self.clear()

    def cmd_prev(self):
        """Show previous notification"""
        self.prev()

    def cmd_next(self):
        """Show next notification"""
        self.next()
