# -*- coding:utf-8 -*-
#
# Copyright © 2015 J Kyle Medley
# Based on the 'pylint' plugin, and the spyderlib/plugins/editor core plugin.
# Licensed under the terms of the Apache License ver 2.0
# (see spyderlib/__init__.py for details)

#from __future__ import print_function
print('from ExportCombine')

import os.path
from os.path import exists, isfile, basename
from zipfile import ZipFile

class MakeCombine:
    def __init__(self):
        self.sbmlfiles = []
        self.sedmlfiles = []
        self.phrasedmlfiles = []

    def getbasename(self, f):
        return basename(f)

    def checkfile(self, filename):
        if not exists(filename) or not isfile(filename):
            raise RuntimeError('No such file: {}'.format(filename))

    def addSBMLFile(self, sbmlfile):
        self.checkfile(sbmlfile)
        self.sbmlfiles.append(sbmlfile)

    def addSEDMLFile(self, sedmlfile):
        self.checkfile(sedmlfile)
        self.sedmlfiles.append(sedmlfile)

    def addPhrasedmlFile(self, phrasedmlfile):
        self.checkfile(phrasedmlfile)
        self.phrasedmlfiles.append(phrasedmlfile)

    def write(self, outfile):
        with ZipFile(outfile, 'w') as z:
            for f in self.sbmlfiles:
                z.write(f, self.getbasename(f))

            for f in self.sedmlfiles:
                z.write(f, self.getbasename(f))

            for f in self.phrasedmlfiles:
                z.write(f, self.getbasename(f))

print('from ExportCombine1')

"""Import Combine Archive to Python Plugin"""
import os, time
import re
import zipfile
import string
import tempfile, shutil, errno
from xml.etree import ElementTree
try:
    from spyderlib.baseconfig import get_translation
    from spyderlib.config import CONF
    from spyderlib.plugins import SpyderPluginMixin, PluginConfigPage
    from spyderlib.py3compat import getcwd, to_text_string, is_text_string
    from spyderlib.qt.QtCore import SIGNAL
    from spyderlib.qt.QtGui import QVBoxLayout, QGroupBox, QWidget, QApplication, QMessageBox
    from spyderlib.qt.compat import getopenfilenames
    from spyderlib.utils import encoding, sourcecode
    from spyderlib.utils.qthelpers import get_icon, create_action
    from spyderlib.widgets.sourcecode.codeeditor import CodeEditor

    print('from ExportCombine2')

    _ = get_translation("p_export_combine", dirname="spyderplugins")

    class ExportCombine(QWidget, SpyderPluginMixin):
        """Import a combine archive as a python script"""
        CONF_SECTION = 'exportcombine'
        def __init__(self, parent=None):
            QWidget.__init__(self, parent=parent)
            SpyderPluginMixin.__init__(self, parent)
            print('Export combine loaded **zz** ------')
            layout = QVBoxLayout()
            self.setLayout(layout)

            # Initialize plugin
            self.initialize_plugin()

        #------ SpyderPluginWidget API --------------------------------------------
        def get_plugin_title(self):
            """Return widget title"""
            return _("Combine archive to Python exporter")

    #    def get_plugin_icon(self):
    #        """Return widget icon"""
    #        return get_icon('hello.png')

        def get_focus_widget(self):
            """
            Return the widget to give focus to when
            this plugin's dockwidget is raised on top-level
            """
            return None

        def get_plugin_actions(self):
            """Return a list of actions related to plugin"""
            # Font
            return []

        def on_first_registration(self):
            """Action to be performed on first plugin registration"""
            self.main.tabify_plugins(self.main.inspector, self)
            self.dockwidget.hide()
            #pass

        def register_plugin(self):
            print('Export combine register_plugin ------')
            export_combine_act = create_action(self, _("Export COMBINE archive (.omex)"),
                                    triggered=self.export_combine)
            export_combine_act.setEnabled(True)

            #self.main.file_menu_actions.addAction(export_combine_act)
            for item in self.main.file_menu_actions:
                try:
                    menu_title = item.title()
                except AttributeError:
                    pass
                else:
                    print('  trying menu item {}'.format(item))
                    if not is_text_string(menu_title): # string is a QString
                        menu_title = to_text_string(menu_title.toUtf8)
                    if item.title() == str("Import"):
                        item.addAction(export_combine_act)

        def refresh_plugin(self):
            """Refresh hello widget"""
            pass

        def closing_plugin(self, cancelable=False):
            """Perform actions before parent main window is closed"""
            return True

        def export_combine(self):
            pass


    print('from ExportCombine4')

    #==============================================================================
    # The following statements are required to register this 3rd party plugin:
    #==============================================================================
    PLUGIN_CLASS = ExportCombine
    print('from ExportCombine5')
except ImportError:
    pass

