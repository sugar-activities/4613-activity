#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# activity.py by:
#    Agustin Zubiaga <aguz@sugarlabs.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import os
import json

from gettext import gettext as _

from sugar.activity import activity
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.toggletoolbutton import ToggleToolButton

from notes import NotesArea

REMOVE_CURSOR = os.path.join(activity.get_bundle_path(),
                             'cursors',
                             'remove.png')


class Annotate(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle, True)

        self.max_participants = 1

        # CANVAS
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        self.notes_area = NotesArea()
        scroll.add_with_viewport(self.notes_area)

        self.set_canvas(scroll)

        # TOOLBARS
        toolbarbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbarbox.toolbar.insert(activity_button, 0)
        activity_button.show()

        separator = gtk.SeparatorToolItem()
        toolbarbox.toolbar.insert(separator, -1)

        note_add = ToolButton('gtk-add')
        note_add.set_tooltip(_('Add a note'))
        note_add.connect('clicked', self.__add_note_cb)
        toolbarbox.toolbar.insert(note_add, -1)

        note_remove = ToggleToolButton('gtk-remove')
        note_remove.set_tooltip(_('Remove notes'))
        note_remove.connect('clicked', self._active_remove)
        toolbarbox.toolbar.insert(note_remove, -1)

        separator = gtk.SeparatorToolItem()
        toolbarbox.toolbar.insert(separator, -1)

        back = ToolButton('go-left')
        back.set_tooltip(_('Select previous note'))
        back.set_sensitive(False)
        back.connect('clicked', lambda w: self.notes_area.select_note(-1))
        toolbarbox.toolbar.insert(back, -1)

        _next = ToolButton('go-right')
        _next.set_tooltip(_('Select next note'))
        _next.connect('clicked', lambda w: self.notes_area.select_note(+1))
        _next.set_sensitive(False)
        toolbarbox.toolbar.insert(_next, -1)

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        toolbarbox.toolbar.insert(separator, -1)

        stopbtn = StopButton(self)
        toolbarbox.toolbar.insert(stopbtn, -1)

        self.set_toolbar_box(toolbarbox)

        self.notes_area.connect('no-notes', self._no_notes,
                                           note_remove, back, _next)
        self.notes_area.connect('note-added', self._note_added, back, _next)

        self.show_all()

    def _no_notes(self, widget, note_remove, back, _next):
        note_remove.set_active(False)
        back.set_sensitive(False)
        _next.set_sensitive(False)

    def _note_added(self, widget, back, _next):
        back.set_sensitive(True)
        _next.set_sensitive(True)

    def __add_note_cb(self, widget):
        self.notes_area.add_note(True)

    def _active_remove(self, widget):
        self.notes_area.set_removing(widget.get_active())
        if widget.get_active():
            display = gtk.gdk.display_get_default()
            pixbuf = gtk.gdk.pixbuf_new_from_file(REMOVE_CURSOR)
            cursor = gtk.gdk.Cursor(display, pixbuf, 0, 0)
        else:
            cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
        self.notes_area.window.set_cursor(cursor)

    def read_file(self, file_path):
        f = open(file_path, 'r')

        try:
            data = json.load(f)
        finally:
            f.close()

        for i in data:
            note = self.notes_area.add_note(True)
            note.set_text(i)

    def write_file(self, file_path):
        self.notes_area.set_removing(True)

        f = open(file_path, 'w')
        data = [i.text for i in self.notes_area.notes]

        try:
            json.dump(tuple(data), f)
        finally:
            f.close()
