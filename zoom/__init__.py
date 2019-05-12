# -*- mode: Python ; coding: utf-8 -*-
# Copyright © 2012–2013 Roland Sieker <ospalh@gmail.com>
# Based in part on code by Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""Add-on for Anki 2.1 to zoom in or out."""
import ctypes

from types import MethodType

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QMenu

from aqt import mw
from aqt.webview import AnkiWebView, QWebEngineView
from anki.hooks import addHook, runHook, wrap
from aqt.utils import showInfo
from anki.lang import _

__version__ = "1.1.1"

# Standard zoom factors for the main views of the central area
# Before you change the review_standard_zoom size, maybe you should
# use larger fonts in your decks.


# How much to increase or decrease the zoom factor with each step. The
# a little odd looking number is the fourth root of two. That means
# with four clicks you double or half the size, as precisely as
# possible.
zoom_step = 2.0**0.25

config = mw.addonManager.getConfig(__name__)


def zoom_in(step=None):
    """Increase the text size."""
    if not step:
        step = zoom_step
    
    change_zoom(mw.web.zoomFactor() * step)


def zoom_out(step=None):
    """Decrease the text size."""
    if not step:
        step = zoom_step
    change_zoom(mw.web.zoomFactor() / step)
    

def set_zoom(state=None, *args):
    """Set the zoom on state change"""
    state = mw.state
    
    if state in ['deckBrowser', 'overview']:
        mw.web.setZoomFactor( config[ 'overview_zoom' ] )
    elif state == 'review':
        mw.web.setZoomFactor( config[ 'review_zoom' ] )

def change_zoom(new_zoom_level):
    """When zoom is changed, save the values"""
    state = mw.state
    
    if state in ['deckBrowser', 'overview']:
        config[ 'overview_zoom' ] = new_zoom_level
    elif state == 'review':
        config[ 'review_zoom' ] = new_zoom_level
    
    mw.addonManager.writeConfig(__name__, config)
    mw.web.setZoomFactor( new_zoom_level )

def reset_zoom(state=None, *args):
    """Reset the text size."""
    if not state:
        state = mw.state
    
    if state in ['deckBrowser', 'overview']:
        change_zoom( config[ 'overview_zoom_default' ] )
    elif state == 'review':
        change_zoom( config[ 'review_zoom_default' ] )

def add_action(submenu, label, callback, shortcut=None):
    """Add action to menu"""
    action = QAction(_(label), mw)
    action.triggered.connect(callback)
    if shortcut:
        action.setShortcut(QKeySequence(shortcut))
    submenu.addAction(action)


def setup_menu():
    """Set up the zoom menu."""
    try:
        mw.addon_view_menu
    except AttributeError:
        mw.addon_view_menu = QMenu(_('&View'), mw)
        mw.form.menubar.insertMenu(
            mw.form.menuTools.menuAction(),
            mw.addon_view_menu
        )

    mw.zoom_submenu = QMenu(_('&Zoom'), mw)
    mw.addon_view_menu.addMenu(mw.zoom_submenu)

    add_action(mw.zoom_submenu, 'Zoom &In', zoom_in, 'Ctrl++')
    add_action(mw.zoom_submenu, 'Zoom &Out', zoom_out, 'Ctrl+-')
    mw.zoom_submenu.addSeparator()

    add_action(mw.zoom_submenu, '&Reset', reset_zoom, 'Ctrl+0')


def handle_wheel_event(event):
    """
    Zoom on mouse wheel events with Ctrl.

    Zoom in our out on mouse wheel events when Ctrl is pressed.  A
    standard mouse wheel click is 120/8 degree. Zoom by one step for
    that amount.
    """
    if event.modifiers() & Qt.ControlModifier:
        step = event.angleDelta().y()
        if step > 0:
            zoom_in()
        elif step < 0:
            zoom_out()
    else:
        original_mw_web_wheelEvent(event)

def real_zoom_factor(self):
    """Use the default zoomFactor.

    Overwrites Anki's effort to support hiDPI screens.
    """
    return QWebEngineView.zoomFactor(self)


addHook('afterStateChange', set_zoom)
original_mw_web_wheelEvent = mw.web.wheelEvent
mw.web.wheelEvent = handle_wheel_event
mw.web.zoomFactor = MethodType(real_zoom_factor, mw.web)
AnkiWebView.zoomFactor = real_zoom_factor
setup_menu()
