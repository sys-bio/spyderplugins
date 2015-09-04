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
import phrasedml

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

    def readfile(self, f):
        with open(f) as x: return x.read()

    # converts a phrasedml extension to a sedml extension
    def replace_pml_ext(self, filename):
        r = re.compile(r'.*\.([^.]*)')
        m = r.match(filename)
        if m is None:
            raise RuntimeError('Unrecognized file name: {}'.format(filename))
        return filename.replace(m.groups()[0], 'xml')

    def write(self, outfile):
        manifest = ''
        with ZipFile(outfile, 'w') as z:
            manifest += '<?xml version="1.0"  encoding="utf-8"?>\n<omexManifest  xmlns="http://identifiers.org/combine.specifications/omex-manifest">\n'
            manifest += '    <content location="./manifest.xml" format="http://identifiers.org/combine.specifications/omex-manifest"/>'

            for f in self.sbmlfiles:
                z.write(f, self.getbasename(f))
                manifest += '    <content location="./{}" format="http://identifiers.org/combine.specifications/sbml"/>'.format(
                    self.getbasename(f))

            for f in self.sedmlfiles:
                z.write(f, self.getbasename(f))
                manifest += '    <content location="./{}" master="true" format="http://identifiers.org/combine.specifications/sed-ml"/>'.format(
                    self.getbasename(f))

            for f in self.phrasedmlfiles:
                sedml = phrasedml.convertString(self.readfile(f))
                z.writestr(self.replace_pml_ext(self.getbasename(f)), sedml)
                manifest += '    <content location="./{}" master="true" format="http://identifiers.org/combine.specifications/sed-ml"/>'.format(
                    self.replace_pml_ext(self.getbasename(f)))

            manifest += '</omexManifest>\n'

            z.writestr('manifest.xml', manifest)

print('from ExportCombine1')

"""Import Combine Archive to Python Plugin"""
import os, time
import re
import zipfile
import string
import tempfile, shutil, errno
from xml.etree import ElementTree

#try:
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWizard, QWizardPage, QLabel, QVBoxLayout
#except ImportError:
    #pass

def createSBMLPage():
    sbmlpage = QWizardPage()
    sbmlpage.setTitle('Select SBML file')

    l = QLabel('Please select an SBML file')

    layout = QVBoxLayout()
    layout.addWidget(l)
    sbmlpage.setLayout(layout)

    return sbmlpage

def createWizard():
    w = QWizard()
    w.addPage(createSBMLPage())

    w.setWindowTitle('COMBINE Export')
    w.show()
    return w

import sys

app = QtWidgets.QApplication([])
w = createWizard()
sys.exit(app.exec_())

try:
    from spyderlib.baseconfig import get_translation
    from spyderlib.config import CONF
    from spyderlib.plugins import SpyderPluginMixin, PluginConfigPage
    from spyderlib.py3compat import getcwd, to_text_string, is_text_string
    from spyderlib.qt.QtCore import SIGNAL
    from spyderlib.qt.QtGui import QVBoxLayout, QGroupBox, QWidget, QApplication, QMessageBox
    from spyderlib.qt.QtGui import QWizard, QWizardPage
    from spyderlib.qt.compat import getopenfilenames
    from spyderlib.utils import encoding, sourcecode
    from spyderlib.utils.qthelpers import get_icon, create_action, add_actions
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
            """Register plugin in Spyder's main window"""
            self.connect(self, SIGNAL("edit_goto(QString,int,QString)"),
                        self.main.editor.load)
            self.connect(self, SIGNAL('redirect_stdio(bool)'),
                        self.main.redirect_internalshell_stdio)
            self.main.add_dockwidget(self)

            print('Export combine register_plugin ------')
            export_combine_act = create_action(self, _("Export COMBINE archive (.omex)"),
                                    triggered=self.export_combine)
            export_combine_act.setEnabled(True)

            add_actions(self.main.file_menu, [export_combine_act])
            #self.main.file_menu_actions.addAction(export_combine_act)
            #for item in self.main.file_menu_actions:
                #try:
                    #menu_title = item.title()
                #except AttributeError:
                    #pass
                #else:
                    #if not is_text_string(menu_title): # string is a QString
                        #menu_title = to_text_string(menu_title.toUtf8)
                    #print('  trying menu item {}'.format(menu_title))
                    #if item.title() == str("Import"):
                        #item.addAction(export_combine_act)
                        #print('    succeeded')
                    #else:
                        #print('    failed')

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

