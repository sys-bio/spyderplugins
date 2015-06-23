# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 17:34:12 2015

@author: Kiri Choi
"""
"Open SBML Plugin"
import os, time
import re
import tellurium as te
from spyderlib.baseconfig import get_translation
from spyderlib.config import CONF
from spyderlib.plugins import SpyderPluginMixin, PluginConfigPage
from spyderlib.py3compat import getcwd
from spyderlib.qt.QtCore import SIGNAL
from spyderlib.qt.QtGui import QVBoxLayout, QGroupBox, QWidget, QApplication, QMessageBox, QMenu
from spyderlib.qt.compat import getopenfilenames
from spyderlib.utils import encoding, sourcecode
from spyderlib.utils.qthelpers import get_icon, create_action, add_actions
from spyderlib.widgets.sourcecode.codeeditor import CodeEditor

_ = get_translation("p_opensbml", dirname="spyderplugins")

class openSBML(QWidget, SpyderPluginMixin):
    "Open sbml files and translate into antimony string"
    CONF_SECTION = 'openSBML'
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        SpyderPluginMixin.__init__(self, parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Initialize plugin
        self.initialize_plugin()
        
    #------ SpyderPluginWidget API --------------------------------------------
    def get_plugin_title(self):
        """Return widget title"""
        return _("Open SBML")
    
    def get_focus_widget(self):
        """
        Return the widget to give focus to when
        this plugin's dockwidget is raised on top-level
        """
        return None
    
    def get_plugin_actions(self):
        """Return a list of actions related to plugin"""
        return []

    def on_first_registration(self):
        """Action to be performed on first plugin registration"""
        self.main.tabify_plugins(self.main.inspector, self)
        self.dockwidget.hide()

    def register_plugin(self):
        """Register plugin in Spyder's main window"""
        self.connect(self, SIGNAL("edit_goto(QString,int,QString)"),
                     self.main.editor.load)
        self.connect(self, SIGNAL('redirect_stdio(bool)'),
                     self.main.redirect_internalshell_stdio)
        #self.main.add_dockwidget(self)
        
        opensbml = create_action(self, _("Open SBML file"),
                                   triggered=self.run_opensbml)
        opensbml.setEnabled(True)
        
        self.main.file_menu_actions.insert(4, opensbml)
        

    def refresh_plugin(self):
        """Refresh hello widget"""
        pass
        
    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed"""
        return True
            
    def apply_plugin_settings(self, options):
        """Apply configuration file's plugin settings"""
        pass
        
    def run_opensbml(self):
        """Prompt the user to load a SBML file, translate to antimony, and display in a new window"""
        editorwindow = None #Used in editor.load
        processevents=True  #Used in editor.load
        editor = self.main.editor
        basedir = getcwd()
        if CONF.get('workingdir', 'editor/open/browse_scriptdir'):
            c_fname = editor.get_current_filename()
            if c_fname is not None and c_fname != editor.TEMPFILE_PATH:
                basedir = os.path.dirname(c_fname)
        editor.emit(SIGNAL('redirect_stdio(bool)'), False)
        parent_widget = editor.get_current_editorstack()
        selectedfilter = ''
        filters = 'SBML files (*.sbml *.xml);;All files (*.*)'
        filenames, _selfilter = getopenfilenames(parent_widget,
                                     _("Open SBML file"), basedir, filters,
                                     selectedfilter=selectedfilter)
        editor.emit(SIGNAL('redirect_stdio(bool)'), True)
        if filenames:
            filenames = [os.path.normpath(fname) for fname in filenames]
            if CONF.get('workingdir', 'editor/open/auto_set_to_basedir'):
                directory = os.path.dirname(filenames[0])
                editor.emit(SIGNAL("open_dir(QString)"), directory)
        else:
            #The file dialog box was closed without selecting a file.
            return
        focus_widget = QApplication.focusWidget()
        if editor.dockwidget and not editor.ismaximized and\
           (not editor.dockwidget.isAncestorOf(focus_widget)\
            and not isinstance(focus_widget, CodeEditor)):
            editor.dockwidget.setVisible(True)
            editor.dockwidget.setFocus()
            editor.dockwidget.raise_()
        
        def _convert(fname):
            fname = os.path.abspath(encoding.to_unicode_from_fs(fname))
            if os.name == 'nt' and len(fname) >= 2 and fname[1] == ':':
                fname = fname[0].upper()+fname[1:]
            return fname

        if hasattr(filenames, 'replaceInStrings'):
            # This is a QStringList instance (PyQt API #1), converting to list:
            filenames = list(filenames)
        if not isinstance(filenames, list):
            filenames = [_convert(filenames)]
        else:
            filenames = [_convert(fname) for fname in list(filenames)]
        
        for index, filename in enumerate(filenames):
            p = re.compile( '(.xml$|.sbml$)')
            pythonfile = p.sub( '_antimony.py', filename)
            if (pythonfile == filename):
                pythonfile = filename + "_antimony.py"
            current_editor = editor.set_current_filename(pythonfile, editorwindow)
            if current_editor is not None:
                # -- TODO:  Do not open an already opened file
                pass
            else:
                # -- Not an existing opened file:
                if not os.path.isfile(filename):
                    continue
                # --
                current_es = editor.get_current_editorstack(editorwindow)

                # Creating the editor widget in the first editorstack (the one
                # that can't be destroyed), then cloning this editor widget in
                # all other editorstacks:
                finfo, newname = self.load_and_translate(filename, pythonfile, editor)
                finfo.path = editor.main.get_spyder_pythonpath()
                editor._clone_file_everywhere(finfo)
                current_editor = current_es.set_current_filename(newname)
                #if (current_editor is not None):
                #    editor.register_widget_shortcuts("Editor", current_editor)
                
                current_es.analyze_script()

            if (current_editor is not None):
                current_editor.clearFocus()
                current_editor.setFocus()
                current_editor.window().raise_()
            if processevents:
                QApplication.processEvents()

    def load_and_translate(self, sbmlfile, pythonfile, editor, set_current=True):
        """
        Read filename as combine archive, unzip, translate, reconstitute in 
        Python, and create an editor instance and return it
        *Warning* This is loading file, creating editor but not executing
        the source code analysis -- the analysis must be done by the editor
        plugin (in case multiple editorstack instances are handled)
        """
        sbmlfile = str(sbmlfile)
        self.emit(SIGNAL('starting_long_process(QString)'),
                  _("Loading %s...") % sbmlfile)
        text, enc = encoding.read(sbmlfile)
        sbmlstr = te.readFromFile(sbmlfile)
        text = "'''" + str(te.sbmlToAntimony(sbmlstr)) + "'''"
        widgeteditor = editor.editorstacks[0]
        finfo = widgeteditor.create_new_editor(pythonfile, enc, text, set_current, new=True)
        index = widgeteditor.data.index(finfo)
        widgeteditor._refresh_outlineexplorer(index, update=True)
        self.emit(SIGNAL('ending_long_process(QString)'), "")
        if widgeteditor.isVisible() and widgeteditor.checkeolchars_enabled \
         and sourcecode.has_mixed_eol_chars(text):
            name = os.path.basename(pythonfile)
            QMessageBox.warning(self, widgeteditor.title,
                                _("<b>%s</b> contains mixed end-of-line "
                                  "characters.<br>Spyder will fix this "
                                  "automatically.") % name,
                                QMessageBox.Ok)
            widgeteditor.set_os_eol_chars(index)
        widgeteditor.is_analysis_done = False
        finfo.editor.set_cursor_position('eof')
        finfo.editor.insert_text(os.linesep)
        return finfo, sbmlfile
        
#==============================================================================
# The following statements are required to register this 3rd party plugin:
#==============================================================================
PLUGIN_CLASS = openSBML

