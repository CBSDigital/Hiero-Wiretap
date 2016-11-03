"""A processor for sending shots to an Autodesk IFFFS server (Stone FS) via
Wiretap.

@author Brendan Holt
@date May 2014
@defgroup modFnWiretapShotProcessor FnWiretapShotProcessor
@{

"""
import os.path

import hiero.core
from hiero.exporters.FnShotProcessor import ShotProcessor, ShotProcessorPreset
import hiero.ui
from PySide import QtCore, QtGui

import Path
import FnStonify
import FnWiretapShotProcessorUI
from WiretapBrowser import ChooseContainerNode
from WiretapTools import SplitHostname


class WiretapShotProcessor(ShotProcessor):
    """A custom Hiero shot processor that works in tandem with the Stonify task
    and provides a streamlined interface for translating Wiretap node paths
    into appropriate export structures.
    
    """
    def __init__(self, preset, submission=None, synchronous=False):
        """Initializes the Wiretap shot processor given a preset and submission
        information.
        
        @param[in] preset \c{(WiretapShotProcessorPreset)} The preset
                          associated with this shot processor.
        
        @param[in] submission \c{(hiero.exporters.FnSubmission.Submission)} The
                              submission task group used for spawning tasks.
        
        @param[in] synchronous \c{(bool)} Whether spawned tasks should be
                               processed synchronously.
        
        """
        super(WiretapShotProcessor, self).__init__(preset, submission,
                                                   synchronous)
    
    def displayName(self):
        """The label for this shot processor as it should appear in the export
        dialog.
        
        @return \c{(str)} The display name for this shot processor.
        
        """
        return "Wiretap Shot Processor"
    
    def toolTip(self):
        """A pop-up summary of this feature when the mouse hovers over the
        processor selection in the export dialog.
        
        @return \c{(str)} The tooltip for this shot processor.
        
        """
        return ("The Wiretap Shot Processor sends supported video/frame "
                "formats to a Stone FS.")
    
    def populateUI(self, widget, exportItems, editMode=None):
        """Inserts custom Qt widgets above the export structure viewer for
        selecting a Wiretap destination node.
        
        @param[in] widget \c{(QtGui.QWidget)} The parent widget that will
                          contain GUI controls exposed for this processor.
        
        @param[in] exportItems \c{(list)} The media selected in the Hiero
                               interface to be exported.  Each item is wrapped
                               as a \c{hiero.core.ItemWrapper} instance.
        
        @param[in] editMode \c{(hiero.ui.IProcessorUI.EditMode)} Whether to
                            expose the full UI (Hiero) or a limited subset
                            (HieroPlayer).
        
        """
        layout = QtGui.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        header = ProcessorHeader()
        defaultForm = QtGui.QWidget()
        layout.addWidget(header)
        layout.addWidget(defaultForm)
        
        super(WiretapShotProcessor, self).populateUI(defaultForm, exportItems,
                                                     editMode)
        
        header.exportTemplate = self._exportTemplate
        header.exportStructureViewer = self._exportStructureViewer
    
    def startProcessing(self, exportItems):
        """Adds an entry to the CBSD usage log before processing the selected
        export items.
        
        @param[in] exportItems \c{(list)} The media selected in the Hiero
                               interface to be exported.  Each item is wrapped
                               as a \c{hiero.core.ItemWrapper} instance.
        
        """
        super(WiretapShotProcessor, self).startProcessing(exportItems)
    
    def validate(self, exportItems):
        """Modified version of Hiero's validation routine that does not enforce
        the requirement of an existing project root on a standard file system
        if there are only Stonify tasks in the export structure.
        
        @param[in] exportItems \c{(list)} The media selected in the Hiero
                               interface to be exported.  Each item is wrapped
                               as a \c{hiero.core.ItemWrapper} instance.
        
        @see \c{hiero.exporters.FnShotProcessor.ShotProcessor.validate()}
        @see \c{hiero.ui.FnProcessorUI.ProcessorUIBase.validate()}
        
        """
        # Do the standard validation if any non-Stonify tasks are present
        doStandardValidation = False
        for exportPath, preset in self._exportTemplate.flatten():
            # NOTE: isinstance() sometimes fails to match a valid object type
            # (maybe because FnStonify.py is loaded as a plugin?)
            if type(preset) is not FnStonify.StonifyPreset:
                doStandardValidation = True
            else:
                # Set a flag on Stonify presets to let the task know that it is
                # being executed by the Wiretap Shot Processor
                preset.setPropertiesValue('isWiretapShotProcess', True)
            
        if doStandardValidation:
            return super(WiretapShotProcessor, self).validate(exportItems)
        
        # Since only Stonify tasks are present, perform almost the same
        # validation as the standard shot processor, except do not check
        # whether the project root has been set.
        # Copied from FnShotProcessor.py
        invalidItems = []
        # Look for selected items which aren't of the correct type
        for item in exportItems:
            if not item.sequence() and not item.trackItem():
                invalidItems.append(item.item().name() +
                                    " <span style='color: #CC0000'>"
                                    "(Not a Sequence)</span>")
        # Found invalid items
        if invalidItems:
            # Show warning
            msgBox = QtGui.QMessageBox()
            msgBox.setTextFormat(QtCore.Qt.RichText)
            result = msgBox.information(
                None, "Export",
                "The following items will be ignored by this export:<br/>%s"
                % str("<br/>".join(invalidItems)),
                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            # Continue if user clicks OK
            return result == QtGui.QMessageBox.Ok
 
        # Copied from FnProcessorUI.py
        # Check for offline track items
        if not self.checkOfflineMedia(exportItems):
            return False
        
        # Do any ShotProcessor-specific validation here...
        return True


class ProcessorHeader(QtGui.QWidget, FnWiretapShotProcessorUI.Ui_Form):
    """A custom header for the Wiretap shot processor that is inserted above
    the export structure viewer.
    
    """
    def __init__(self):
        """Initializes the header UI for the Wiretap shot processor section of
        the export dialog.
        
        """
        super(ProcessorHeader, self).__init__()
        self.setupUi(self)
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        # Override path to CBSD logo
        logoPath = os.path.join(os.path.dirname(__file__),
                                '../resources/images/cbsd_logo.png')
        logoPath = os.path.normpath(logoPath)
        
        self.logoLabel.setPixmap(QtGui.QPixmap(logoPath))
        
        self.notesLabel.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Ignored)
        
        ## \c{(bool)} Whether additional instructions related to the shot
        #  processor configuration are visible.
        self.notesVisible = False
        
        ## \c{(hiero.core.FnExportStructure.ExportStructure2)} A reference to
        #  the current preset's export template.
        #
        #  @details Set externally by WiretapShotProcessor.populateUI().
        self.exportTemplate = None
        
        ## \c{(hiero.ui.ExportStructureViewer)} A reference to the Wiretap shot
        #  processor's export structure viewer.
        #
        #  @details Set externally by WiretapShotProcessor.populateUI().
        self.exportStructureViewer = None
        
        # Signal-slot pairs
        self.notesButton.clicked.connect(self.ToggleNotes)
        self.chooseButton.clicked.connect(self.ChooseNodePath)
        self.clipNameEdit.textEdited.connect(self.__FixClipName)
        self.addElementButton.clicked.connect(self.AddElement)
    
    #--------------------------------------------------------------------------
    #    SLOTS
    #--------------------------------------------------------------------------
    def ToggleNotes(self):
        """Toggles the visibility of additional usage notes displayed in the
        processor header.
        
        @details This method is a Qt slot for when the expand/collapse notes
                 button is clicked.
        
        """
        if self.notesVisible:
            self.notesButton.setText('Notes  [+]')
            self.notesLabel.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Ignored)
            self.notesVisible = False
        else:
            self.notesButton.setText(u'Notes  [\u2212]')  # minus (not hyphen)
            self.notesLabel.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Preferred)
            self.notesVisible = True
    
    def ChooseNodePath(self):
        """Launches a Wiretap browser and displays the selected node path upon
        return.
        
        @details This method is a Qt slot for when the "Choose..." (Wiretap
                 library or reel) button is clicked.
        
        """
        nodePath = ChooseContainerNode()
        if nodePath:
            self.nodePathEdit.setText(nodePath)
    
    def __FixClipName(self, text):
        """Provides dynamic text substitutions and constraints when editing the
        clip name.
        
        @details This method is a Qt slot for when the contents of the clip
                 name text box are manually edited.
        
        """
        substitutions = {
            '/': '',
            '\\': ''
        }
        cursorPos = self.clipNameEdit.cursorPosition()
        for char in substitutions:
            text = text.replace(char, substitutions[char])
        self.clipNameEdit.setText(text)
        self.clipNameEdit.setCursorPosition(cursorPos)
    
    def AddElement(self):
        """Converts a Wiretap node path into an export structure and updates
        the export structure viewer with the new hierarchy.
        
        @details There is minimal path syntax checking in this method.  The
                 Wiretap Browser will usually fix most typos.
        
        @throws Raises a <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.TypeError" target="_blank">
                TypeError</a> if the export structure viewer was not properly
                set by WiretapShotProcessor.populateUI().
        
        """
        if not self.exportStructureViewer:
            raise TypeError("Please connect the shot processor's export "
                            "structure viewer to this header instance.")
        
        # Don't discard double slashes at end to allow for unnamed nodes.
        segments = [seg for seg in self.nodePathEdit.text().split('/')]
        hostname = SplitHostname(segments[0])[0]  # drop "IFFFS"
        
        # Require a clip name
        # NOTE: The actual path requirements for uploading to a Wiretap IFFFS
        # server are more strict, but path validation happens elsewhere.
        clipName = self.clipNameEdit.text().strip()
        if clipName:
            segments.append(clipName)
        elementPath = Path.Join(hostname, *segments[1:])
        
        # Populate export structure
        root = self.exportTemplate.rootElement()
        if clipName:
            root.createChild(elementPath, True)
            leaf = root[elementPath]
        
            # Add preset to leaf element
            # NOTE: Be sure to update the string representation of the Stonify
            # task if the module or class name changes.
            preset = FnStonify.StonifyPreset(name='FnStonify.StonifyTask',
                                             properties={})
            if leaf is not None:
                leaf.setPreset(preset)
            else:
                print("WARNING: Unable to set Stonify content on element " +
                      elementPath)
        elif elementPath:
            root.createChild(elementPath, False)

        self.exportStructureViewer.refresh()
        

class WiretapShotProcessorPreset(ShotProcessorPreset):
    """Stores settings for use with the Wiretap shot processor and its
    corresponding UI class that augments the export dialog interface.
    
    """
    def __init__(self, name, properties):
        """Sets up the Wiretap shot processor preset with default properties.
        
        @param[in] name \c{(str)} The preset name, usually handled
                        automatically by Hiero.
        
        @param[in] properties \c{(dict)} Preset properties to be updated.
        
        """
        super(WiretapShotProcessorPreset, self).__init__(name, properties)
        
        # Necessary in order for Hiero to view this plugin as different from
        # the default shot processor
        self._parentType = WiretapShotProcessor


hiero.core.taskRegistry.registerProcessor(WiretapShotProcessorPreset,
                                          WiretapShotProcessor)
hiero.ui.taskUIRegistry.registerProcessorUI(WiretapShotProcessorPreset,
                                            WiretapShotProcessor)

## @}
