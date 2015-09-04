# Author: J Kyle Medley
# Date: 09/04/2015

import os.path
from os.path import exists, isfile, basename
from zipfile import ZipFile
import phrasedml

class CombineAsset(object):
    # Get the URI for sbml, sedml, etc.
    def getCOMBINEResourceURI(x):
        types = {
            'sbml': 'http://identifiers.org/combine.specifications/sbml',
            'sed-ml': 'http://identifiers.org/combine.specifications/sed-ml'
        }

    def isPhraSEDML():
        return False

# Raw/file assets:
# File assets specify a file path in the OS filesystem
# Raw assets contain the raw string of the entire asset

class CombineRawAsset(CombineAsset):
    def __init__(self, raw, archname):
        self.raw = raw
        self.archname = archname

    def getArchName(self):
        return self.archname

    def getRawStr(self):
        with open(self.getFileName()) as f:
            return f.read()

    # return a form suitable for exporting to COMBINE (uses dynamic binding)
    def getExportedStr(self):
        return self.getRawStr()

class CombineFileAsset(CombineAsset):
    def __init__(self, filename):
        self.filename = filename

    def getFileName(self):
        return self.filename

    def getArchName(self):
        return self.getbasename(f)

    def getRawStr(self):
        with open(self.getFileName()) as f:
            return f.read()

    def getExportedStr(self):
        return self.getRawStr()

# Asset types: SBML, SEDML, etc.

class CombineSBMLAsset(CombineAsset):
    def getResourceURI(self):
        return CombineAsset.getCOMBINEResourceURI('sbml')

class CombineSEDMLAsset(CombineAsset):
    def getResourceURI(self):
        return CombineAsset.getCOMBINEResourceURI('sed-ml')

class CombinePhraSEDMLAsset(CombineAsset):
    def isPhraSEDML():
        return True

    def getSEDMLStr(self):
        return phrasedml.convertString(self.getRawStr())

    def getResourceURI(self):
        return CombineAsset.getCOMBINEResourceURI('sed-ml')

# SBML:

class CombineSBMLRawAsset(CombineRawAsset, CombineSBMLAsset):
    pass

class CombineSBMLFileAsset(CombineFileAsset, CombineSBMLAsset):
    pass

# SEDML:

class CombineSEDMLRawAsset(CombineRawAsset,   CombineSEDMLAsset):
    pass

class CombineSEDMLFileAsset(CombineFileAsset, CombineSEDMLAsset):
    pass

# PhraSEDML:

class CombinePhraSEDMLRawAsset(CombineRawAsset,   CombinePhraSEDMLAsset):
    # return SEDML, since COMBINE doesn't support PhraSEDML
    def getExportedStr(self):
        return self.getSEDMLStr()

class CombinePhraSEDMLFileAsset(CombineFileAsset, CombinePhraSEDMLAsset):
    # converts a phrasedml extension to a sedml extension
    def replace_pml_ext(self, filename):
        r = re.compile(r'.*\.([^.]*)')
        m = r.match(filename)
        if m is None:
            raise RuntimeError('Unrecognized file name: {}'.format(filename))
        return filename.replace(m.groups()[0], 'xml')

    def getArchName(self):
        return self.replace_pml_ext(self.getbasename(f))

    # return SEDML, since COMBINE doesn't support PhraSEDML
    def getExportedStr(self):
        return self.getSEDMLStr()

class MakeCombine:
    def __init__(self):
        self.sbmlfiles = []
        self.sedmlfiles = []
        self.phrasedmlfiles = []

    def checkfile(self, filename):
        if not exists(filename) or not isfile(filename):
            raise RuntimeError('No such file: {}'.format(filename))

    def addSBMLFile(self, sbmlfile):
        self.checkfile(sbmlfile)
        self.assets.append(CombineFileAsset(sbmlfile))

    def addSEDMLFile(self, sedmlfile):
        self.checkfile(sedmlfile)
        self.assets.append(CombineFileAsset(sedmlfile))

    def addPhrasedmlFile(self, phrasedmlfile):
        self.checkfile(phrasedmlfile)
        self.assets.append(CombinePhraSEDMLFileAsset(phrasedmlfile))

    def writeAsset(self, zipfile, asset):
        if asset.isFile():
            zipfile.write(asset.getFileName(), asset.getArchName())
        else:
            zipfile.writestr(asset.getExportedStr(), asset.getArchName())

        manifest += '    <content location="./{}" master="true" format="{}"/>'.format(
            asset.getArchName(),
            asset.getResourceURI()
            )

    def write(self, outfile):
        manifest = ''
        with ZipFile(outfile, 'w') as z:
            manifest += '<?xml version="1.0"  encoding="utf-8"?>\n<omexManifest  xmlns="http://identifiers.org/combine.specifications/omex-manifest">\n'
            manifest += '    <content location="./manifest.xml" format="http://identifiers.org/combine.specifications/omex-manifest"/>'

            for a in self.assets:
                self.writeAsset(z, a)

            for f in self.sedmlfiles:
                z.write(f, self.getbasename(f))
                manifest += '    <content location="./{}" master="true" format=""/>'.format(
                    self.getbasename(f))

            for f in self.phrasedmlfiles:
                sedml = phrasedml.convertString(self.readfile(f))
                z.writestr(self.replace_pml_ext(self.getbasename(f)), sedml)
                manifest += '    <content location="./{}" master="true" format="http://identifiers.org/combine.specifications/sed-ml"/>'.format(
                    self.replace_pml_ext(self.getbasename(f)))

            manifest += '</omexManifest>\n'

            z.writestr('manifest.xml', manifest)