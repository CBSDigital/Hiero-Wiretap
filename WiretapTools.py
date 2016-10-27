"""Tracks Wiretap server connections and wraps various node querying functions.

@author Brendan Holt
@date May 2014
@defgroup modWiretapTools WiretapTools
@{

"""
from wiretap import *


class WiretapManager(object):
    """A Wiretap connection manager that also provides an easy interface for
    querying nodes.
    
    """
    
    ## Bit flag for the Wiretap IFFFS (Stone FS) server type.
    PRODUCT_IFFFS = 0b1
    
    ## Bit flag for the Wiretap Gateway (standard file system) server type.
    PRODUCT_GATEWAY = 0b10
    
    ## Bit flag for the Wiretap Backburner (render queue) server type.
    PRODUCT_BACKBURNER = 0b100
    
    ## Relates bit flag constants to their Wiretap server product names.
    PRODUCT_FLAG_MAP = {
        PRODUCT_IFFFS: 'IFFFS',
        PRODUCT_GATEWAY: 'Wiretap Gateway Server',
        PRODUCT_BACKBURNER: 'Backburner'
    }
    
    @staticmethod
    def __ListProducts(flags):
        """Converts bit flags to a list of Wiretap server product names,
        filtered by product type.
        
        @param[in] flags \c{(int)} The product flags (see \c{PRODUCT_MAP} for
                         valid entries) joined with a bitwise \c{OR}.
        
        @throws Raises a <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.ValueError" target="_blank">
                ValueError</a> if an invalid flag was submitted.
        
        @return \c{(list)} The names of the Wiretap server products that
                correspond to the given bit flags.
        
        """
        products = []
        shiftCount = 0
        while flags > 0:
            flag = (flags - (flags >> 1 << 1)) << shiftCount
            if flag:
                try:
                    products.append(WiretapManager.PRODUCT_FLAG_MAP[flag])
                except KeyError:
                    raise ValueError("Invalid Wiretap server product flag: {0}"
                                     .format(flag))
            flags = flags >> 1
            shiftCount += 1
        return products
    
    @staticmethod
    def GetServerListInfo(productFlags=None):
        """Retrieves information for each server that passed the product type
        filter.
        
        @param[in] productFlags \c{(int)} The product flags (see
                                \c{PRODUCT_MAP} for valid entries) joined with
                                a bitwise \c{OR}.
        
        @throws Raises a \c{WireTapException} if unable to access the server
                list or a particular Wiretap server.
        
        @return \c{(list)} A series of \c{WiretapServerInfo} objects
                corresponding to the filtered Wiretap hosts.
        
        @see Borrows from the Wiretap Python API \c{listAllServers.py} example.
        
        """
        products = WiretapManager.__ListProducts(productFlags)
        servers = WireTapServerList()
        count = WireTapInt()
        if not servers.getNumNodes(count):
            raise WireTapException("Error acquiring server list: {0}".format(
                servers.lastError()))
        
        serverListInfo = []
        for ii in xrange(count):
            info = WireTapServerInfo()
            if not servers.getNode(ii, info):
                raise WireTapException("Error accessing server {0}: {1}"
                                       .format(ii, servers.lastError()))
            
            if products:
                if info.getProduct().lower() in [p.lower() for p in products]:
                    serverListInfo.append(info)
            else:
                serverListInfo.append(info)
        return serverListInfo
    
    def __init__(self, productFlags):
        """Initializes a Wiretap connection manager.
        
        @param[in] productFlags \c{(int)} The product flags (see
                                \c{PRODUCT_MAP} for valid entries) joined with
                                a bitwise \c{OR}.
        
        """
        ## \c{(list)} A series of \c{WiretapServerInfo} objects for the
        #  relevant server types (IFFFS, Gateway, and/or Backburner) currently
        #  detected on the network.
        self.__serverListInfo = WiretapManager.GetServerListInfo(productFlags)
        
        ## \c{(dict)} The currently connected Wiretap servers
        #  \c{(WireTapServerHandle)} with hostnames \c{(str)} for keys.
        self.__connected = {}
    
    def Connect(self, hostname):
        """Connects to a Wiretap server and saves the connection in this
        manager's server dictionary.
        
        @param[in] hostname \c{(str)} The name of the Wiretap server to connect
                            to.
        
        @return \c{(WireTapServerHandle)} A handle to the connected Wiretap
                server.
        
        """
        server = WireTapServerHandle(hostname)
        self.__connected[hostname] = server
        return server
    
    def Disconnect(self, hostname):
        """Attempts to disconnect from a Wiretap server by removing the entry
        from this manager's server dictionary.
        
        @param[in] hostname \c{(str)} The name of the Wiretap server to
                            disconnect from.
        
        @warning The Wiretap Python API does not expose a disconnect method.
                 If other objects have saved a reference to the server handle,
                 it might not be truly destroyed.
        
        """
        try:
            del self.__connected[hostname]
        except KeyError:
            pass
    
    def GetServer(self, hostname):
        """Retrieves a Wiretap server handle by hostname.
        
        @param[in] hostname \c{(str)} The name of the Wiretap server to
                            retrieve.
        
        @throws Raises a <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.ValueError" target="_blank">
                ValueError</a> if the hostname is invalid or not connected.
        
        @return \c{(WireTapServerHandle)} A handle to the requested Wiretap
                server.
        
        """
        if hostname in self.hostnames:
            try:
                return self.__connected[hostname]
            except KeyError:
                return self.Connect(hostname)
        else:
            raise ValueError("The hostname and/or its product port alias is "
                             "invalid: " + hostname)
    
    def GetRoot(self, hostname):
        """Wraps the module-level function \ref WiretapTools.GetRoot()
        "GetRoot()" by using string parameters instead of Wiretap object
        handles.
        
        @param[in] hostname \c{(str)} The name of the Wiretap server being
                            queried.
        
        @return \c{(WireTapNodeHandle)} A Wiretap node handle that gives access
                to the root node of the Wiretap server.
        
        """
        server = self.GetServer(hostname)
        return GetRoot(server)
    
    def GetNode(self, hostname, nodeID):
        """Gets a Wiretap node handle by node ID from the specified server.
        
        @param[in] hostname \c{(str)} The name of the Wiretap server being
                            queried.
        
        @param[in] nodeID \c{(str)} The unique Wiretap node ID of the requested
                          node.
                          
        @return \c{(WireTapNodeHandle)} A handle to the requested Wiretap node.
        
        """
        server = self.GetServer(hostname)
        return WireTapNodeHandle(server, nodeID)
    
    def GetChildren(self, hostname, nodeID):
        """Wraps the module-level function \ref WiretapTools.GetChildren()
        "GetChildren()" by using string parameters instead of Wiretap object
        handles.
        
        @param[in] hostname \c{(str)} The name of the Wiretap server being
                            queried.
        
        @param[in] nodeID \c{(str)} The unique Wiretap node ID of the requested
                          node.
        
        @return \c{(list)} The immediate children under the Wiretap node
                corresponding to the given node ID.
        
        """
        node = self.GetNode(hostname, nodeID)
        return GetChildren(node)

    def GetNodeTypeStr(self, hostname, nodeID):
        """Wraps the module-level function \ref WiretapTools.GetNodeTypeStr()
        "GetNodeTypeStr()" by using string parameters instead of Wiretap object
        handles.
        
        @param[in] hostname \c{(str)} The name of the Wiretap server being
                            queried.
        
        @param[in] nodeID \c{(str)} The unique Wiretap node ID of the requested
                          node.
                          
        @return \c{(str)} A string representation of the node type.
        
        """
        if nodeID == '/':  # a shortcut
            return 'HOST'
        node = self.GetNode(hostname, nodeID)
        return GetNodeTypeStr(node)
    
    def GetDisplayName(self, hostname, nodeID):
        """Wraps the module-level function \ref WiretapTools.GetDisplayName()
        "GetDisplayName()" by using string parameters instead of Wiretap object
        handles.
        
        @param[in] hostname \c{(str)} The name of the Wiretap server being
                            queried.
        
        @param[in] nodeID \c{(str)} The unique Wiretap node ID of the requested
                          node.
        
        @return \c{(str)} The display name for the node.
        
        """
        if nodeID == '/':  # a shortcut
            return SplitHostname(hostname)[0]
        node = self.GetNode(hostname, nodeID)
        return GetDisplayName(node)
    
    #--------------------------------------------------------------------------
    #    PROPERTIES
    #--------------------------------------------------------------------------
    def __GetHostnames(self):
        """Getter for #hostnames.
        
        @return \c{(list)} The filtered Wiretap hostnames associated with this
                connection manager.
        
        """
        hostnames = []
        for info in self.__serverListInfo:
            product = info.getProduct()
            # Convert "Wiretap Gateway Server" to just "Gateway"
            if 'gateway' in product.lower():
                product = 'Gateway'
            hostnames.append('{0}:{1}'.format(info.getDisplayName(), product))
        return hostnames
    
    ## \c{(list)} The Wiretap hostnames, filtered by server type, that are
    #  associated with this connection manager.
    #
    #  @details Implemented by __GetHostnames().
    hostnames = property(fget=__GetHostnames)


def SplitHostname(hostname):
    """Splits a Wiretap hostname into the server name and its colon-separated
    product type (IFFFS, Gateway, or Backburner).
    
    @param[in] hostname \c{(str)} The Wiretap server's hostname in the form of
                        \c{name:type}.
    
    @return \c{(tuple)} The Wiretap server name followed by the product type,
            if any.
    
    """
    splitHostname = hostname.split(':')
    if len(splitHostname) != 2:
        print("A Wiretap hostname should contain exactly one colon between "
              "the server name and product type.")
    if len(splitHostname) == 1:
        splitHostname.append('')
    return tuple(splitHostname)


def GetRoot(server):
    """Gets the root node of the Wiretap server (usually "/").
    
    @param[in] server \c{(WireTapServerHandle)} The Wiretap server to be
                      queried.
    
    @throws Raises a \c{WireTapException} if unable to retrieve the root node.
    
    @return \c{(WireTapNodeHandle)} A Wiretap node handle that gives access to
            the root node of the Wiretap server.
    
    @see Documentation was partially copied from
         \c{WireTapServerHandle.getRootNode()} in the <em>Autodesk Wiretap
         Client C++ API Reference</em>.
    
    """
    rootNode = WireTapNodeHandle()
    if not server.getRootNode(rootNode):
        msg = "Unable to get the root node from {0}: {1}".format(
            server.getHostName(), server.lastError())
        raise WireTapException(msg)
    return rootNode


def GetChildren(node):
    """Gets all child nodes of a specified node on the server.
    
    @param[in] node \c{(WireTapNodeHandle)} The Wiretap node whose children
                    will be listed.
    
    @throws Raises a \c{WireTapException} if unable to access a child node.
    
    @return \c{(list)} The immediate children of the given Wiretap node handle.
    
    @see Borrows from the Wiretap Python API \c{listChildren.py} example.
    
    """
    children = []
    numChildren = WireTapInt(0)
    if not node.getNumChildren(numChildren):
        raise WireTapException("Unable to obtain number of children: {0}"
                               .format(node.lastError()))
    
    for ii in xrange(numChildren):
        child = WireTapNodeHandle()
        if not node.getChild(ii, child):
            raise WireTapException("Unable to retrieve child: {0}"
                                   .format(node.lastError()))
        children.append(child)
    
    return children


def GetNodeTypeStr(node):
    """Gets a string that describes the type of the current node.
    
    @details This could be the value entered when the node was created or one
             of the extended node types defined by the Wiretap server.  Each
             Wiretap server defines its own extended node types.
    
    @param[in] node \c{(WireTapNodeHandle)} The Wiretap node to be queried.
    
    @throws Raises a \c{WireTapException} if unable to obtain the node type.
    
    @return \c{(str)} A string representation of the node type.
    
    @see Documentation was partially copied from
         \c{WireTapNodeHandle.getNodeTypeStr()} in the <em>Autodesk Wiretap
         Client C++ API Reference</em>.
    
    """
    nodeType = WireTapStr()
    if not node.getNodeTypeStr(nodeType):
        raise WireTapException("Unable to obtain node type: {0}".format(
            node.lastError()))
    return str(nodeType)


def GetDisplayName(node):
    """Gets the display name of the current node.
    
    @details Display names need not be
             unique.
    
    @param[in] node \c{(WireTapNodeHandle)} The Wiretap node to be queried.
    
    @throws Raises a \c{WireTapException} if unable to obtain the node display
            name.
    
    @return \c{(str)} The display name for the node.
    
    @see Documentation was partially copied from
         \c{WireTapNodeHandle.getDisplayName()} in the <em>Autodesk Wiretap
         Client C++ API Reference</em>.
    
    """
    displayName = WireTapStr()
    if not node.getDisplayName(displayName):
        raise WireTapException("Unable to obtain node display name: {0}"
                               .format(node.lastError()))
    return str(displayName)


## @}
