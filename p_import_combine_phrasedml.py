# -*- coding:utf-8 -*-
#
# Copyright © 2014 Lucian Smith
# Based on the 'pylint' plugin, and the spyderlib/plugins/editor core plugin.
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Import Combine Archive to Python Plugin"""
import os, time
import re
import zipfile
import phrasedml as pl
import tellurium as te
import string
import tempfile, shutil, errno
from xml.etree import ElementTree
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

_ = get_translation("p_import_combine_phrasedml", dirname="spyderplugins")

#Temp. disabled (Not needed)
#class C2PConfigPage(PluginConfigPage):
#    def setup_page(self):
#        settings_group = QGroupBox(_("Settings"))
#        save_box = self.create_checkbox(_("Placeholder in case we at some point need a settings page."),
#                                        'tick_value', default=True)
#
#        settings_layout = QVBoxLayout()
#        settings_layout.addWidget(save_box)
#        settings_group.setLayout(settings_layout)
#
#        vlayout = QVBoxLayout()
#        vlayout.addWidget(settings_group)
#        vlayout.addStretch(1)
#        self.setLayout(vlayout)


class C2PWP(QWidget, SpyderPluginMixin):
    """Import a combine archive as a python script with phrasedml"""
    CONF_SECTION = 'c2pwp'
    #CONFIGWIDGET_CLASS = C2PConfigPage
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
        return _("Import COMBINE as PhrasedML")
    
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

    def register_plugin(self):
        """Register plugin in Spyder's main window"""
        self.connect(self, SIGNAL("edit_goto(QString,int,QString)"),
                     self.main.editor.load)
        self.connect(self, SIGNAL('redirect_stdio(bool)'),
                     self.main.redirect_internalshell_stdio)
        self.main.add_dockwidget(self)
        
        c2pwp_act = create_action(self, _("Import COMBINE as PhrasedML"),
                                   triggered=self.run_c2pwp)
        c2pwp_act.setEnabled(True)
        #self.register_shortcut(c2p_act, context="Combine to Python",
        #                       name="Import combine archive", default="Alt-C")
        
        for item in self.main.file_menu_actions:
            try:
                menu_title = item.title()
            except AttributeError:
                pass
            else:
                if not is_text_string(menu_title): # string is a QString
                    menu_title = to_text_string(menu_title.toUtf8)
                if item.title() == str("Import"):
                    item.addAction(c2pwp_act)

    def refresh_plugin(self):
        """Refresh hello widget"""
        pass
        
    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed"""
        return True
            
    def apply_plugin_settings(self, options):
        """Apply configuration file's plugin settings"""
        pass
        
    def run_c2pwp(self):
        """Prompt the user to load a combine archive, translate to Python, and display in a new window"""
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
        filters = 'Combine archives (*.zip *.omex);;All files (*.*)'
        filenames, _selfilter = getopenfilenames(parent_widget,
                                     _("Open combine archive"), basedir, filters,
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
            p = re.compile( '(.zip$|.omex$)')
            pythonfile = p.sub( '.py', filename)
            if (pythonfile == filename):
                pythonfile = filename + ".py"
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

    def load_and_translate(self, combine, pythonfile, editor, set_current=True):
        """
        Read filename as combine archive, unzip, translate, reconstitute in 
        Python, and create an editor instance and return it
        *Warning* This is loading file, creating editor but not executing
        the source code analysis -- the analysis must be done by the editor
        plugin (in case multiple editorstack instances are handled)
        """
        combine = str(combine)
        self.emit(SIGNAL('starting_long_process(QString)'),
                  _("Loading %s...") % combine)
        text, enc = encoding.read(combine)
        text = Translatecombine(combine)
        zipextloctemp, sbmlloclisttemp, sedmlloclisttemp = manifestsearch(combine)
        for i in range(len(text)):
            widgeteditor = editor.editorstacks[0]
            sedmlfname = os.path.basename(sedmlloclisttemp[i])
            finfo = widgeteditor.create_new_editor(os.path.splitext(sedmlfname)[0] + '_phrasedml.py', enc, text[i], set_current, new=True)
            index = widgeteditor.data.index(finfo)
            widgeteditor._refresh_outlineexplorer(index, update=True)
            self.emit(SIGNAL('ending_long_process(QString)'), "")
            if widgeteditor.isVisible() and widgeteditor.checkeolchars_enabled \
             and sourcecode.has_mixed_eol_chars(text[i]):
                name = os.path.basename(pythonfile[:-3] + '_phrasedml.py')
                QMessageBox.warning(self, widgeteditor.title,
                                    _("<b>%s</b> contains mixed end-of-line "
                                      "characters.<br>Spyder will fix this "
                                      "automatically.") % name,
                                    QMessageBox.Ok)
                widgeteditor.set_os_eol_chars(index)
            widgeteditor.is_analysis_done = False
            finfo.editor.set_cursor_position('eof')
            finfo.editor.insert_text(os.linesep)
        return finfo, combine

#Extracts combine archive to a temporary directory
def zipext(combine):
    tarzip = zipfile.ZipFile(combine)
    extloc = tempfile.mkdtemp()
    tarzip.extractall(extloc)
    tarzip.close()
    return extloc
    
#Searches the manifest to acquire correct sbml and sedml file location
def manifestsearch(combine):
    __manifest = True
    sbmlloclist = []
    sedmlloclist = []
    zipextloc = zipext(combine)
    manifestloc = os.path.join(zipextloc, 'manifest.xml')
    try:
        manifest = ElementTree.parse(manifestloc)
    except IOError:
        __manifest = False
    if __manifest == True:
        root = manifest.getroot()
        for child in root:
            attribute = child.attrib
            formtype = attribute.get('format')
            loc = attribute.get('location')
            if formtype == "http://identifiers.org/combine.specifications/sbml":
                sbmlloc = loc
                sbmlloc = sbmlloc[1:]
                sbmlloclist.append(sbmlloc)
            elif formtype == "http://identifiers.org/combine.specifications/sed-ml":
                sedmlloc = loc
                sedmlloc = sedmlloc[1:]
                sedmlloclist.append(sedmlloc)
        return (zipextloc, sbmlloclist, sedmlloclist)
    else:
        print ("Manifest file not found. Import Combine will search for the model file...")

#Customized from Ipythonify
def Translatecombine(combine):

    def getbasename(path):
        e = re.compile(r'.*[/\\]([^/\\]*\.[^/\\]*)')
        m = e.match(path)
        if m is None:
            raise RuntimeError('Path not recognized: {}'.format(path))
        return m.groups()[0]
						
    #Creates a string with both SBML and SEDML included
    def translate(combine, filename):
        sbmlstrlist = []
        sedmlstrlist = []
        outputstrlist = []
        outputstr = "# -*- coding: utf-8 -*-\n\n" + '"Generated by Import Combine with PhrasedML plugin ' + time.strftime("%m/%d/%Y") + '"\n"Extracted from ' + filename + '"\n\n# Translated SBML\n'		
        zipextloc, sbmlloclist, sedmlloclist = manifestsearch(combine)
        for i in range(len(sbmlloclist)):
            sbml = te.readFromFile(zipextloc + sbmlloclist[i])
            sbmlstrlist.append(te.sbmlToAntimony(sbml))
        for j in range(len(sedmlloclist)):
            sedmlstr = pl.convertFile(zipextloc + sedmlloclist[j])
            sedmlstr = sedmlstr.replace('"compartment"', '"compartment_"')
            sedmlstr = sedmlstr.replace("'compartment'", "'compartment_'")
            sedmlstrlist.append(sedmlstr)
        
        for k in range(len(sedmlstrlist)):
            outputstrlist.append(outputstr + "AntimonyModel = '''\n" + sbmlstrlist[0] + "'''\n\nPhrasedMLstr = '''\n" + sedmlstrlist[k] + "'''")
        
        delseq(zipextloc)
        return outputstrlist
    
    #Garbage collection
    def delseq(floc):
        try:
            os.remove(floc)
        except OSError as E1:
            try:
                shutil.rmtree(floc)
            except OSError as E2:
                if E1.errno != errno.ENOENT or E2.errno != errno.ENOENT:
                    raise
                
    fname = os.path.basename(combine)
    return translate(combine, fname)


#==============================================================================
# The following statements are required to register this 3rd party plugin:
#==============================================================================
PLUGIN_CLASS = C2PWP

