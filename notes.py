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
import gobject
import pango
import gconf

from sugar.graphics import style

WHITE = gtk.gdk.Color('#FFFFFF')
BLACK = gtk.gdk.Color('#000000')

NOTE_WIDTH = style.zoom(279)
NOTE_HEIGHT = style.zoom(279)
MARGIN = style.zoom(21)
LAYOUT_WIDTH = NOTE_WIDTH - (MARGIN * 2)
BOX_SPACE = style.zoom(29)

SPACE_DEFAULT = int(gtk.gdk.screen_width() / (NOTE_WIDTH + BOX_SPACE))

ESC_KEY = 65307
TAB_KEY = 65289
SHIFT_TAB_KEY = 65056


def get_colors():
    client = gconf.client_get_default()
    colors = client.get_string('/desktop/sugar/user/color')
    colors = colors.split(',')

    stroke = style.Color(colors[0]).get_rgba()
    fill = style.Color(colors[1]).get_rgba()

    return stroke, fill


class NotesArea(gtk.EventBox):

    __gsignals__ = {'no-notes': (gobject.SIGNAL_RUN_FIRST, None, []),
                    'note-added': (gobject.SIGNAL_RUN_FIRST, None, [])}

    def __init__(self):
        gtk.EventBox.__init__(self)

        self.mainbox = gtk.VBox()
        self.notes = []

        self.add(self.mainbox)
        self.groups = []
        self.notes = []
        self.removing = False

        self.modify_bg(gtk.STATE_NORMAL, WHITE)

        self._add_box()

        self.show_all()

    def set_removing(self, removing=False):
        self.removing = removing

        if removing:
            for note in self.notes:
                note.hide_textview()

    def select_note(self, position):
        editing = None
        for note in self.notes:
            if note.editing:
                editing = note
        try:
            if editing:
                next_note = self.notes[self.notes.index(editing) + position]
                next_note.edit()
            else:
                self.notes[0].edit()
        except:
            self.notes[0].edit()

    def add_note(self, anim):
        note = Note(self, fade_in=anim)
        note.connect('editing', self.__editing_note_cb)

        if not self.groups[-1].space:
            self._add_box()

        last_box = self.groups[-1]
        last_box.pack_start(note.fixed, False, True, BOX_SPACE)
        last_box.space -= 1

        if last_box.space == SPACE_DEFAULT - 1:
            last_box.show_all()

        self.notes.append(note)

        note.fixed.show_all()
        note.textview.frame.hide()

        self.emit('note-added')

        return note

    def _add_box(self):
        box = gtk.HBox()
        box.space = SPACE_DEFAULT

        self.mainbox.pack_start(box, False, True, BOX_SPACE)
        self.groups.append(box)

    def set_note_text(self, note=-1, text=''):
        self.notes[note].set_text(text)

    def __editing_note_cb(self, note):
        for i in self.notes:
            if i != note:
                i.hide_textview()

    def relocate_notes(self):
        data = [i.text for i in self.notes]

        for i in self.groups:
            i.destroy()

        self.groups = []
        self._add_box()

        self.notes = []

        if not data:
            self.removing = False
            self.emit("no-notes")

        for i in data:
            note = self.add_note(False)
            note.set_text(i)

    def remove_note(self, index):
        self.notes[index]._remove_note(None)


class Note(gtk.DrawingArea):

    __gsignals__ = {'editing': (gobject.SIGNAL_RUN_FIRST, None, [])}

    def __init__(self, notes_area, fade_in=False):

        gtk.DrawingArea.__init__(self)

        self.set_size_request(NOTE_WIDTH, NOTE_HEIGHT)

        self.text = ''
        self.editing = False
        self._opacity = 0 if fade_in else 1

        pango_context = self.get_pango_context()
        self.layout = pango.Layout(pango_context)
        self.layout.set_width(LAYOUT_WIDTH * pango.SCALE)
        self.layout.set_wrap(pango.WRAP_WORD_CHAR)

        self.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK)

        self.connect('expose-event', self._expose_cb)
        self.connect('button-press-event', self.edit)

        self.fixed = gtk.Fixed()
        self.fixed.modify_bg(gtk.STATE_NORMAL, WHITE)
        self.fixed.put(self, 0, 0)

        self.textview = gtk.TextView()
        self.textview.set_left_margin(MARGIN)
        self.textview.set_right_margin(MARGIN)

        self.textview.set_wrap_mode(gtk.WRAP_WORD_CHAR)

        self.textview.set_property('width-request', NOTE_WIDTH)
        self.textview.set_property('height-request', NOTE_HEIGHT)

        self.textview.connect('key-press-event', self._key_press_event_cb)

        stroke, fill = get_colors()
        self.textview.modify_base(gtk.STATE_NORMAL,
                                  gtk.gdk.Color(fill[0], fill[1], fill[2]))
        self.textview.frame = gtk.Frame()
        self.textview.frame.modify_bg(gtk.STATE_NORMAL,
                                gtk.gdk.Color(stroke[0], stroke[1], stroke[2]))
        self.textview.frame.add(self.textview)

        self.fixed.put(self.textview.frame, 0, 0)

        if fade_in:
            gobject.timeout_add(50, self._fade_in_animation)

        self._notes_area = notes_area

    def _expose_cb(self, widget, event):
        context = self.window.cairo_create()
        gc = self.window.new_gc()

        x, y, w, h = self.get_allocation()

        stroke, fill = get_colors()

        # Black Frame:
        context.rectangle(0, 0, w, h)
        context.set_source_rgba(stroke[0], stroke[1], stroke[2], self._opacity)
        context.fill()

        # Background rectangle:
        context.rectangle(0, 0, w - 2, h - 2)
        context.set_source_rgba(fill[0], fill[1], fill[2], self._opacity)
        context.fill()

        # Write Text:
        self.layout.set_markup(self.text)
        self.window.draw_layout(gc, MARGIN, 0, self.layout)

    def _fade_in_animation(self):
        self._opacity += 0.1
        self.queue_draw()

        return True if self._opacity <= 1.0 else False

    def _fade_out_animation(self):
        self._opacity -= 0.1
        self.queue_draw()

        if self._opacity <= 0.0:
            self.fixed.destroy()
            self._notes_area.notes.remove(self)
            self._notes_area.relocate_notes()
            return False

        else:
            return True

    def set_text(self, text):
        self.text = text
        self.textview.get_buffer().set_text(text)
        self.queue_draw()

    def hide_textview(self):
        self._set_text(self.textview)

        self.textview.frame.hide()
        self.editing = False
        self.show()

    def _key_press_event_cb(self, widget, event):
        if event.keyval == ESC_KEY:
            self.hide_textview()

        elif event.keyval == TAB_KEY:
            self._notes_area.select_note(+1)

        elif event.keyval == SHIFT_TAB_KEY:
            self._notes_area.select_note(-1)

    def _set_text(self, widget):
        _buffer = widget.get_buffer()
        start, end = _buffer.get_bounds()
        text = _buffer.get_text(start, end)

        self.set_text(text)

    def edit(self, *kwargs):
        if not self._notes_area.removing:
            self.hide()
            buf = self.textview.get_buffer()
            buf.set_text(self.text)
            self.textview.frame.show_all()
            self.textview.props.is_focus = True

            self.editing = True
            self.emit('editing')
        else:
            self._remove_note(None)

    def _remove_note(self, widget):
        gobject.timeout_add(50, self._fade_out_animation)
