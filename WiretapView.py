"""Extended Qt widgets and methods for displaying hierarchical Wiretap nodes.

@author Brendan Holt
@date May 2014
@defgroup modWiretapView WiretapView
@{

"""
import sys

from PySide import QtCore, QtGui
from wiretap import WireTapException

from WiretapTools import WiretapManager


class NodeTreeView(QtGui.QTreeView):
    """A tree view tailored for displaying Wiretap nodes.
    
    @todo Some of the methods in this class pertain more to the model than
          the view.  Implement a \c{QAbstractItemModel} and move those methods
          there.
    
    """
    def __init__(self, parent=None):
        """Initializes a node tree view for displaying NodeItem%s.
        
        @param[in] parent \c{(QtGui.QWidget)} The parent widget for this
                          dialog.
        
        """
        super(NodeTreeView, self).__init__(parent)
        
        ## \c{(bool)} Whether this tree view should exclude Wiretap clip,
        #  setup, and other content-related nodes.
        self.excludeContent = True
        
        ## \c{(\ref WiretapTools.WiretapManager "WiretapManager")} The Wiretap
        #  server manager for keeping track of connections.
        self.manager = WiretapManager(WiretapManager.PRODUCT_IFFFS)
        
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        
        # Signal-slot pairs
        self.expanded.connect(self.LoadChildren)
        
        # Use Refresh buttons to update children instead
        #self.collapsed.connect(self.ResetChildren)
        
        # Auto-resizing of columns (may be visually annoying)
        #self.expanded.connect(lambda index: self.FitColumnToContents(0))
        #self.collapsed.connect(lambda index: self.FitColumnToContents(0))
    
    def Populate(self):
        """Populates the tree model with NodeItem%s for each Wiretap server
        discovered.
        
        """
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels(['Name', 'Type'])
        self.setModel(model)
        
        self.setUniformRowHeights(True)  # enable view optimizations
        self.setColumnWidth(0, 300)  # works only after view initialized
        self.setColumnWidth(1, 100)
        
        # Populate the view with a list of servers
        for hn in self.manager.hostnames:
            item = NodeItem(self.manager, hn)
            NestItem(self.model(), item)
    
    def GoTo(self, path, useNodeID):
        """Navigates to the specified Wiretap node in the tree view and
        selects it.
        
        @param[in] path \c{(str)} The Wiretap server hostname concatenated with
                        the node ID or node display path.
        
        @param[in] useNodeID \c{(bool)} Whether to interpret the path as a
                             Wiretap node ID or a series of slash-separated
                             node display names (reels and clips have display
                             names that differ from their node IDs).
        
        """
        HOST = 0
        depth = 0
        item = None
        segments = [seg for seg in path.split('/') if seg]
        
        # Account for unnamed REELs and CLIPs (displayed as "Unnamed" but are
        # actually an empty string)
        if len(segments) > 1 and path[-1] == '/': 
            segments.append('')  # unnamed REEL/CLIP
        
        # Open each node item and search for a match
        for depth, segment in enumerate(segments):
            # Match top-level item's hostname
            if depth == HOST:
                items = Query(self.model(), 'hostname', segment)
            
            # Match item with same node ID up to the current depth
            elif useNodeID:
                nodeID = '/' + '/'.join(segments[1:depth+1])
                items = Query(item, 'nodeID', nodeID)
            
            # Match first item with the same displayName
            else:
                items = Query(item, 'displayName', segment)
            
            # Expand the first matched item's parent and select item in view
            if items:
                item = items[0]
                if depth > HOST:
                    self.setExpanded(item.parent().index(), True)
                self.setCurrentIndex(item.index())
    
    #--------------------------------------------------------------------------
    #    SLOTS
    #--------------------------------------------------------------------------
    def Reset(self):
        """Resets the Wiretap connection manager and clears the item model."""
        self.manager = WiretapManager(WiretapManager.PRODUCT_IFFFS)
        self.model().clear()
        self.expanded.connect(self.LoadChildren)
        self.Populate()
    
    def ResetChildren(self, index):
        """Removes the children of the NodeItem associated with the given
        index.
        
        @details The children may be reloaded by closing and reopening the item
                 in the tree view.
        
        @param[in] index \c{(QtCore.QModelIndex)} The index of the parent item
                         whose children will be reset.
        
        """
        model = index.model()
        item = model.itemFromIndex(index)
        try:
            item.ResetChildren()
        except:
            item.removeRows(0, item.rowCount())
    
    def LoadChildren(self, index):
        """Loads the children of the NodeItem associated with the given index.
        
        @param[in] index \c{(QtCore.QModelIndex)} The index of the parent item
                         whose children will be loaded.
        
        """
        model = index.model()
        item = model.itemFromIndex(index)
        try:
            item.LoadChildren(self.excludeContent)
        except WireTapException as why:
            print why
            self.clearSelection()
    
    def FitColumnToContents(self, column, margin=10):
        """Resizes the specified column to fit its contents with a margin.
        
        @param[in] column \c{(int)} The zero-based column index to fit.
        
        @param[in] margin \c{(int)} Additional buffer added to the column
                           width.
        
        """
        self.resizeColumnToContents(column)
        self.setColumnWidth(column, self.columnWidth(column) + margin)


class NodeItem(QtGui.QStandardItem):
    """Represents a Wiretap server or node handle in a tree view."""
    
    ## \c{(tuple)} The names of the Wiretap container node types (hosts,
    #  volumes, projects, libraries, and reels).
    CONTAINERS = ('HOST', 'VOLUME', 'PROJECT', 'LIBRARY', 'REEL')
    
    ## \c{(tuple)} The names of the Wiretap container types that can store
    #  clip nodes (libraries and reels).
    CLIP_CONTAINERS = ('LIBRARY', 'REEL')
    
    def __init__(self, manager, hostname, nodeID='/'):
        """Initializes a Wiretap node item for use with a
        \c{QStandardItemModel}.
        
        @param[in] manager \c{(\ref WiretapTools.WiretapManager
                           "WiretapManager")} A reference to the Wiretap
                           connection manager providing data for the tree view.
        
        @param[in] hostname \c{(str)} The Wiretap server hostname associated
                            with this NodeItem.  The hostname includes the
                            colon-separated product type (usually "IFFFS").
        
        @param[in] nodeID \c{(str)} The Wiretap node ID that this item will
                          represent.
        
        """
        
        ## \c{(\ref WiretapTools.WiretapManager "WiretapManager")} A reference
        #  to the Wiretap connection manager providing data for the tree view.
        self.manager = manager
        
        ## \c{(str)} The Wiretap server hostname associated with this node
        #  item.
        #
        #  @details The hostname includes the colon-separated product type
        #           (usually "IFFFS").
        self.hostname = hostname
        
        ## \c{(str)} The Wiretap node ID that this item will represent.
        self.nodeID = nodeID
        
        ## \c{(str)} The Wiretap node type.
        self.nodeType = manager.GetNodeTypeStr(hostname, nodeID)
        
        ## \c{(bool)} Whether the children of this node have been listed (the
        #  node was expanded in the tree view).
        self.__hasCachedChildren = False
        
        ## \c{(function)} Nests other NodeItem%s under this node.
        self.NestItem = lambda item: NestItem(self, item)
        
        ## \c{(str)} The Wiretap node display name (usually).
        #
        # @details The text property is not necessarily the same as the display
        #          name, especially with server items, which may append the
        #          artists' names.
        self.displayName = manager.GetDisplayName(hostname, nodeID)
        super(NodeItem, self).__init__(self.displayName)
        self.setEditable(False)
        
        if not self.text():
            self.setText('Unnamed')
            font = self.font()
            font.setItalic(True)
            self.setFont(font)
        
        if self.nodeType in NodeItem.CONTAINERS:
            self.appendRow(CreateDummyItem())
    
    def LoadChildren(self, excludeContent):
        """Creates a NodeItem for every immediate child of the associated
        Wiretap node.
        
        @param[in] excludeContent \c{(bool)} Whether or not clips, setups, and
                                  other non-container nodes should be excluded
                                  from the hierarchy.
        
        """
        if not self.__hasCachedChildren:
            try:
                children = self.manager.GetChildren(self.hostname, self.nodeID)
            except WireTapException:
                self.RemoveChildren()
                self.DisableRow()
                raise WireTapException("Failed to load children from node "
                                       "path: " + self.nodePath)
            
            self.removeRows(0, self.rowCount())
            for node in children:
                nodeID = node.getNodeId().id()
                nodeType = self.manager.GetNodeTypeStr(self.hostname, nodeID)
                # Exclude SETUP and CLIP nodes
                if excludeContent and nodeType not in NodeItem.CONTAINERS:
                    continue
                self.NestItem(NodeItem(self.manager, self.hostname, nodeID))
            self.__hasCachedChildren = True
    
    def ResetChildren(self):
        """Replaces this item's children with a placeholder item."""
        self.RemoveChildren()
        self.appendRow(CreateDummyItem())
    
    def RemoveChildren(self):
        """Resets this item to an uncached state by removing all child rows."""
        self.removeRows(0, self.rowCount())
        self.__hasCachedChildren = False
    
    def DisableRow(self):
        """Disable all columns in this item's row.
        
        @note Each item can manipulate the states of its child columns.  In
              order to disable the current item's row, you must access its
              parent and then the correct row beneath it.
        
        """
        parent = self.parent()
        if not parent:  # top-level item has null parent
            parent = self.model()
        
        # Disable every column in this item's row (w.r.t. the parent)
        for ii in xrange(parent.columnCount()):
            try:  # parent = QStandardItem
                column = parent.child(self.row(), ii)
            except AttributeError:  # parent type is QStandardItemModel
                column = parent.item(self.row(), ii)
            if column:
                column.setEnabled(False)
    
    #--------------------------------------------------------------------------
    #    PROPERTIES
    #--------------------------------------------------------------------------
    def __GetDisplayPath(self):
        """Getter for #displayPath.
        
        @return \c{(str)} The Wiretap hostname concatenated with the node
                display path.
        
        """
        MAX_DEPTH = 10  # IFFFS hierarchies typically less than 7 nodes deep
        depth = 0  # safety feature in case top-level node is not of type HOST
        displayNames = []
        nodeItem = self
        while nodeItem.nodeType != 'HOST' and depth < MAX_DEPTH:
            displayNames.insert(0, nodeItem.displayName)
            nodeItem = nodeItem.parent()
            depth += 1
        return self.hostname + '/' + '/'.join(displayNames)
    
    def __GetNodePath(self):
        """Getter for #nodePath.
        
        @return \c{(str)} The Wiretap hostname concatenated with the node ID.
        
        """
        return self.hostname + self.nodeID
    
    ## \c{(str)} Gets the Wiretap hostname concatenated with the node display
    #  path.
    #
    #  @details Implemented by __GetDisplayPath().
    displayPath = property(fget=__GetDisplayPath)
    
    ## \c{(str)} Gets the Wiretap hostname concatenated with the node ID.
    #
    #  @details Implemented by __GetNodePath().
    nodePath = property(fget=__GetNodePath)


def CreateDummyItem():
    """Creates a placeholder child item so that parent items may be expanded
    before checking for the existence of actual children.
    
    @return \c{(QtGui.QStandardItem)} The dummy item that was created.
    
    """
    item = QtGui.QStandardItem('Loading...')
    item.setEditable(False)
    return item


def NestItem(parent, item):
    """Adds the given item to a (multi-column) row beneath the parent model or
    item.
    
    @details Since \c{QStandardItemModel} is not supposed to be subclassed,
             this hack automatically adds a second information column (when
             appropriate) using an attribute from the item in the first column.
    
    @param[in] parent \c{(QStandardItemModel/QStandardItem/QWiretapItem)} The
                      parent model or item that will host the given item in a
                      new row.
    
    @param[in] item \c{(QStandardItem/QWiretapItem)} The item to be nested
                    under the parent.
    
    """
    try:
        nodeTypeItem = QtGui.QStandardItem(item.nodeType)
        nodeTypeItem.setEditable(False)
        parent.appendRow([item, nodeTypeItem])
    except AttributeError:  # item.nodeType doesn't exist (not a WiretapItem)
        parent.appendRow(item)


def Query(parent, attribute, value):
    """Searches the immediate children of the parent for items containing the
    attribute value that matches the given parameters.
    
    @param[in] parent \c{(QStandardItemModel/QStandardItem/QWiretapItem)} The
                      parent widget whose child items will be queried.
    
    @param[in] attribute \c{(str)} The name of the child item's attribute to be
                         checked.
    
    @param[in] value The value of the child item's attribute.
    
    @return \c{(list)} The matching items, if any, that were found.
    
    """
    matched = []
    if hasattr(parent, 'item'):  # model
        GetItem = lambda row: parent.item(row)
    elif hasattr(parent, 'child'):  # item
        GetItem = lambda row: parent.child(row)
    else:
        return matched
    
    for ii in xrange(parent.rowCount()):
        item = GetItem(ii)
        try:
            if value == getattr(item, attribute):
                matched.append(item)
        except AttributeError:
            continue
    return matched


## @}
