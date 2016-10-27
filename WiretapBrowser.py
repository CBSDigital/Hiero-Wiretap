"""Provides a Qt-based GUI for browsing Wiretap servers and nodes.

@author Brendan Holt
@date May 2014
@todo Implement node creation, deletion, and display filters.
@defgroup modWiretapBrowser WiretapBrowser
@{

"""
import sys

from PySide import QtGui
from wiretap import WireTapClientInit, WireTapClientUninit, WireTapException

import WiretapBrowserUI
from WiretapView import NodeItem


class BrowserDialog(QtGui.QDialog, WiretapBrowserUI.Ui_browserDialog):
    """A dialog window for browsing to a Wiretap \c{CLIP} container node
    (either a \c{LIBRARY} or a \c{REEL}) using a tree view of the node
    hierarchy.
    
    @details Content such as clip and setup nodes are not shown (disabled in
             NodeSelected() and \ref modWiretapView).
    
    """
    def __init__(self, parent=None):
        """Initializes a Wiretap browser dialog.
        
        @param[in] parent \c{(QtGui.QWidget)} The parent widget for this
                          dialog.
        
        """
        super(BrowserDialog, self).__init__(parent)
        self.setupUi(self)
        self.nodeTreeView.Populate()
        
        self.nodeItem = None
        
        self.openButton = self.confirmButtonBox.button(
            QtGui.QDialogButtonBox.Open)
        self.openButton.setEnabled(False)
        
        # Node selection signal-slot
        self.__InitTreeSelectionModel()
        
        # Refresh buttons
        self.refreshButton.clicked.connect(self.Refresh)
        self.refreshAllButton.clicked.connect(self.RefreshAll)
        
        self.pathEdit.textEdited.connect(self.CheckPathFormat)
        self.idButton.toggled.connect(self.ToggleNodeID)
        
        #self.pathEdit.setReadOnly(True)  # prevent users from wrecking format
    
    def __InitTreeSelectionModel(self):
        """Initializes the item selection model for the tree view and connects
        the \c{currentRowChanged} signal to a node selection slot.
        
        """
        selectionModel = QtGui.QItemSelectionModel(self.nodeTreeView.model())
        selectionModel.currentRowChanged.connect(self.NodeSelected)
        self.nodeTreeView.setSelectionModel(selectionModel)
    
    def IsValidPathFormat(self, text):
        """Checks whether the node path is of the appropriate depth for a
        library or reel node and corrects matching hostnames with improper
        case.
        
        @param[in] text \c{(str)} The node path from the browser's text box.
        
        @return \c{(bool)} Whether the node path has a valid format.
        
        @todo Implement browsing to the node as you type.  However, there can
              be significant delays depending on the server selected.
        
        """
        minSegments = 4  # at least HOST/VOLUME/PROJECT/LIBRARY
        maxSegments = 5  # at most HOST/VOLUME/PROJECT/LIBRARY/REEL
        segments = [seg for seg in text.split('/') if seg]
        
        # Get the hostname from the first segment
        try:
            hostname = segments[0]
        except IndexError:
            return False
        
        # Hostname must be in the current list of detected servers and is case-
        # sensitive.
        try:
            fixedHostname = self.FixHostnameCase(hostname)
        except ValueError:
            return False
        
        # Fix the case of the hostname
        if hostname != fixedHostname:
            cursorPos = self.pathEdit.cursorPosition()
            self.pathEdit.setText(text.replace(hostname, fixedHostname, 1))
            self.pathEdit.setCursorPosition(cursorPos)
        
        # TO DO: Browse to node as you type.
        #self.nodeTreeView.GoTo(...)
        
        # Too few or too many path segments
        if len(segments) < minSegments or len(segments) > maxSegments:
            return False
        
        return True
    
    def FixHostnameCase(self, hostname):
        """Fixes a Wiretap hostname that was spelled correctly but may have
        improper case.
        
        @details Wiretap hostnames are case-sensitive for initiating server
                 connections.
        
        @param[in] hostname \c{(str)} The hostname whose case may need fixing.
        
        @throws Raises a <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.ValueError" target="_blank">
                ValueError</a> if the hostname is misspelled.
        
        @return \c{(str)} The corrected hostname.
        
        """
        for hn in self.nodeTreeView.manager.hostnames:
            if hostname.lower() == hn.lower():
                return hn
        raise ValueError("Invalid hostname: " + hostname)
    
    #--------------------------------------------------------------------------
    #    SLOTS
    #--------------------------------------------------------------------------
    def NodeSelected(self, current, previous):
        """Updates the node path text box and determines if the current node
        is a container type that can be returned.
        
        @details This method is a Qt slot for when a new Wiretap node is
                 selected in the tree view.
        
        @param[in] current \c{(QtCore.QmodelIndex)} The current row's model
                           index.
        
        @param[in] previous \c{(QtCore.QmodelIndex)} The previous row's model
                            index.
        
        """
        model = current.model()
        self.nodeItem = model.itemFromIndex(current)
        try:  # attempt access on NodeItem attributes
            if self.idButton.isChecked():
                self.pathEdit.setText(self.nodeItem.nodePath)
            else:
                self.pathEdit.setText(self.nodeItem.displayPath)
            
            if self.nodeItem.nodeType in NodeItem.CLIP_CONTAINERS:
                self.openButton.setEnabled(True)
            else:
                self.openButton.setEnabled(False)
        except AttributeError:  # may occasionally select dummy item
            pass
    
    def Refresh(self):
        """Refreshes the children of the currently selected node.
        
        @details The collapsed/expanded states of the child nodes will not be
                 retained.  This method is a Qt slot for when the "Refresh"
                 button is clicked.
        
        """
        if self.nodeItem:
            index = self.nodeItem.index()
            isExpanded = self.nodeTreeView.isExpanded(index)
            
            try:
                self.nodeItem.ResetChildren()
            except AttributeError:  # probably not a NodeItem
                pass
            
            self.nodeTreeView.collapse(index)  # hide dummy node
            self.nodeTreeView.expand(index)  # forces reloading of children
            self.nodeTreeView.setExpanded(index, isExpanded)  # original state
    
    def RefreshAll(self):
        """Collapses all node trees and refreshes the Wiretap server list.
        
        @details This method is a Qt slot for when the "Refresh All" button is
                 clicked.
        
        """
        self.nodeTreeView.Reset()
        self.__InitTreeSelectionModel()
    
    def CheckPathFormat(self, text):
        """Enables/disables the dialog-accepted ("Open") button depending on
        whether the node path has the correct format.
        
        @details This method is a Qt slot for when text is manually edited in
                 the text box.
        
        @param[in] text \c{(str)} The edited text to be checked.
        
        """
        if self.IsValidPathFormat(text):
            self.openButton.setEnabled(True)
        else:
            self.openButton.setEnabled(False)
    
    def ToggleNodeID(self, checked):
        """Converts a node ID to a display path in the path text box, and vice
        versa.
        
        @details If a reel or clip has a blank display name, then consecutive
                 slashes may appear in portions of the path.  When node ID mode
                 is activated, reels and clips will show up as hash IDs instead
                 of display names.  This method is a Qt slot for when the ID
                 button is clicked.
        
        @param[in] checked \c{(bool)} Whether the node ID toggle button is in
                           an activated state.
        
        """
        # Navigate to the current path using the previous node/display path
        # style (opposite of checked)
        self.nodeTreeView.GoTo(self.pathEdit.text(), not checked)
        
        # When the ID toggle button is activated, make the text bold
        if checked:
            font = self.idButton.font()
            font.setBold(True)
        else:
            font = self.idButton.font()
            font.setBold(False)
        self.idButton.setFont(font)


def ChooseContainerNode(parent=None):
    """Launches a Wiretap browser and returns the selected node path.
    
    @param[in] parent \c{(QtGui.QWidget)} The parent widget for this dialog.
    
    @throws Raises a \c{WireTapException} if the Wiretap client failed to
            initialize.
    
    @return \c{(str)} The Wiretap server concatenated with the selected node ID
            or display path.  The result is an empty string if the dialog was
            canceled.
    
    """
    if not WireTapClientInit():
        raise WireTapException("Unable to initialize the Wiretap client API.")
    
    browser = BrowserDialog(parent)
    status = browser.exec_()
    
    WireTapClientUninit()
    
    if status == QtGui.QDialog.Accepted:
        return browser.pathEdit.text()
    return ''


def SplitNodePath(nodePath):
    """Splits a Wiretap Browser node path into a Wiretap server name and node
    ID.
    
    @details A "node path" combines a Wiretap server name and a node ID,
             yielding a single string.  When splitting a node path, this
             function assumes that the text before the first slash is the
             server name.
    
    @param[in] nodePath \c{(str)} A non-standard conjunction of the Wiretap
                        server name and node ID in the form of
                        \c{HOST:PRODUCT/VOLUME/PROJECT/LIBRARY/[REEL]/CLIP}.
    
    @return \c{(tuple)} The hostname and node ID (the latter always has a
            leading slash).
    
    """
    try:  # split server from the node ID
        hostname, nodeID = nodePath.split('/', 1)
    except ValueError:  # only the server present
        hostname = nodePath
        nodeID = ''
    return hostname, '/' + nodeID


## @cond TEST
def main():
    """A test harness for launching the Wiretap browser in standalone mode."""
    if not WireTapClientInit():
        raise WireTapException("Unable to initialize the Wiretap client API.")
     
    app = QtGui.QApplication(sys.argv)
     
    browser = BrowserDialog()
    browser.show()
 
    # Cleanup
    appStatus = app.exec_()
    WireTapClientUninit()
    sys.exit(appStatus)
## @endcond

if __name__ == '__main__':
    main()


## @}
