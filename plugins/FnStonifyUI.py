"""Contains the user interface template for the Stonify task created in the
Hiero export dialog.

@author Brendan Holt
@date March 2014
@see \ref modFnStonify
@defgroup modFnStonifyUI FnStonifyUI
@{

"""


import hiero.ui
from PySide import QtGui

from FnStonify import StonifyTask, StonifyPreset


class StonifyTaskUI(hiero.ui.TaskUIBase):
    """An interface for setting the Stonify task parameters.
    
    @details UI controls will appear when a leaf element is selected in the
             Hiero export structure viewer.  Currently, this object definition
             is just a placeholder that displays usage instructions but no
             settings.
    
    """
    def __init__(self, preset):
        """Initializes the Stonify task interface.
        
        @param[in] preset \c{(\ref FnStonify.StonifyPreset "StonifyPreset")}
                          The preset containing user controlled settings that
                          will be exposed in the task UI.
        
        """
        super(StonifyTaskUI, self).__init__(StonifyTask, preset, "Stonify")
    
    def populateUI(self, widget, exportTemplate):
        """Populates the task's user interface with Qt widgets.
        
        @param[in] widget \c{(QtGui.QWidget)} The parent widget that will
                          contain GUI controls exposed for this task.
        
        @param[in] exportTemplate
                   \c{(hiero.core.FnExportStructure.ExportStructure2)} The
                   export structure associated with the task preset.
        
        """
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(9, 0, 9, 0)
        widget.setLayout(layout)
        label = QtGui.QLabel(
            "<p>This file is a placeholder for the clip node to be generated "
            "on an Autodesk Stone FS.  The destination Wiretap server is "
            "given by the name of the top-level export structure folder, "
            "while the parent node display path (a library or reel) is "
            "represented by the intermediate folder hierarchy.</p>"
            
            "<p><i>Please note that Stonify tasks are intended for use with "
            "the Wiretap Shot Processor.</i></p>")
        label.setWordWrap(True)
        layout.addWidget(label)


hiero.ui.taskUIRegistry.registerTaskUI(StonifyPreset, StonifyTaskUI)


## @}
