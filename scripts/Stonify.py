"""Command-line script for copying frames to a Wiretap clip node, similar in
functionality to the \c{wiretap_client_tool} CLI.

@todo Move some of the more useful module-level methods to WiretapTools.py.
@author Brendan Holt
@date March 2014
@defgroup modStonify Stonify
@{

"""
try:
    from wiretap import *
except ImportError as why:
    msg = ('The CBSD "PythonModules" directory must be added to PYTHONPATH.  '
           "Also verify that the Wiretap Python API has been compiled for the "
           "separate versions of Python embedded in Hiero and HieroNuke.")
    raise ImportError(str(why) + ".  " + msg)

from Locator import SCRIPT_PATH


## Absolute path to the Hiero-Wiretap modules directory.
MODULE_PATH = ''  # force Doxygen to use type "string" instead of "tuple"
MODULE_PATH = os.path.normpath(os.path.join(SCRIPT_PATH, '..'))
if MODULE_PATH not in sys.path:
    sys.path.append(MODULE_PATH)

from WiretapTools import GetChildren, GetDisplayName


class FrameCopier(object):
    """Manages video frame ingestion from one Wiretap server to another.
    
    @note Be sure to save references to key Wiretap objects (Boost.Python), or
          they may go out of scope, causing Python to crash.
    
    """
    def __init__(self, sourceHost, sourceNodeID,
                 destinationHost, destinationParentNodeID, destinationClipName,
                 useDisplayName, createParentNodeID, overwriteClip,
                 frameRate, dropMode, startTimecode,
                 startFrame=None, endFrame=None):
        """Constructs a frame copier object using source/destination paths,
        frame rate, starting timecode, and other clip parameters.
        
        @param[in] sourceHost \c{(str)} The source hostname, including the
                              colon-separated product type, usually a Wiretap
                              Gateway server (e.g. "Vid_WS17:Gateway").
        
        @param[in] sourceNodeID \c{(str)} The source clip's node ID.
        
        @param[in] destinationHost \c{(str)} The destination hostname,
                                   including the colon-separated product type,
                                   usually a Wiretap IFFFS server (e.g.
                                   "Vid_WS17:IFFFS").
        
        @param[in] destinationParentNodeID \c{(str)} The parent node ID for the
                                           destination clip.
                                           
        @param[in] destinationClipName \c{(str)} The display name of the
                                       destination clip.
        
        @param[in] useDisplayName \c{(bool)} Whether to select the destination
                                  parent node ID using display names rather
                                  than a node ID.
        
        @param[in] createParentNodeID \c{(bool)} Whether to create the parent
                                      node if the specified parenet node ID
                                      doesn't exist.
        
        @param[in] overwriteClip \c{(bool)} Whether to first delete existing
                                 clips with the same display name as the
                                 destination clip to be written.
        
        @param[in] frameRate \c{(float)} The frame rate of the destination
                             clip.
        
        @param[in] dropMode \c{(str)} Whether to use drop frame ("DF") or
                            non-drop frame ("NDF") timecode.
        
        @param[in] startTimecode \c{(str)} The starting timecode for the clip
                                 node in the form of \c{hh:mm:ss:ff}
                                 (semicolons instead of colon separators
                                 indicate drop frame timecode).
        
        @param[in] startFrame \c{(int)} The zero-based starting frame number.
                              Not required for image sequences.
        
        @param[in] endFrame \c{(int)} The zero-based ending frame number.  Not
                            required for image sequences.
        
        @throws Raises a \c{WireTapException} if the Wiretap client could not
                be initialized.
        
        """
        if not WireTapClientInit():
            raise WireTapException("Unable to initialize the Wiretap client "
                                   "API.")
        
        # Set up source/destination clip nodes/formats
        
        ## \c{(WireTapServerHandle)} A handle to the source Wiretap Gateway
        #  server.
        self.sourceServer = WireTapServerHandle(sourceHost)
        
        ## \c{(WireTapNodeHandle)} A handle to the source clip node.
        self.sourceClip = WireTapNodeHandle(self.sourceServer, sourceNodeID)
        
        ## \c{(WireTapClipFormat)} The format of the source clip.
        self.sourceClipFormat = GetClipFormat(self.sourceClip)
        
        ## \c{(int)} The zero-based starting frame number.
        self.startFrame = 0
        
        ## \c{(int)} The zero-based ending frame number.
        self.endFrame = 0
        
        ## \c{(int)} The total number of frames to be copied.
        self.numFrames = 0
        
        # NOTE: ParseArguments() deals with bad input (e.g. if startFrame was
        # specified without an accompanying endFrame)
        if startFrame is not None and endFrame is not None:
            self.startFrame = startFrame
            self.endFrame = endFrame
            self.numFrames = self.endFrame - self.startFrame + 1
        else:  # frame range is implicit if the source is an image sequence
            self.numFrames = GetClipFrameCount(self.sourceClip)
            self.endFrame = self.numFrames - 1
        
        ## \c{(WireTapServerHandle)} A handle to the destination Wiretap IFFFS
        #  server.
        self.destinationServer = WireTapServerHandle(destinationHost)
        
        # Convert user-friendly display paths to internal node IDs, and create
        # any missing library/reel if requested.
        if useDisplayName:  # destinationParentNodeID isn't actually a node ID
            destinationParentNodeID = ResolveDisplayPath(
                self.destinationServer, destinationParentNodeID,
                createParentNodeID)
        
        # Delete the existing destination clip if the overwrite flag is
        # enabled.  Otherwise, a clip with the same display name (but different
        # node ID will be created.
        #
        # NOTE: The parent node ID was already converted from display names, if
        # necessary.
        if overwriteClip:
            destinationParentNode = WireTapNodeHandle(self.destinationServer,
                                                      destinationParentNodeID)
            DeleteDuplicateClips(destinationParentNode, destinationClipName)
            
        ## \c{(WireTapNodeHandle)} A handle to the destination clip node.
        self.destinationClip = self.__CreateDestinationClip(
            destinationParentNodeID, destinationClipName,
            frameRate, dropMode, startTimecode)
        
        ## \c{(WireTapClipFormat)} The format of the destination clip.
        # 
        # @see Autodesk's \c{createClip.py} sample
        self.destinationClipFormat = GetClipFormat(self.destinationClip)
        
        
    def __CreateDestinationClip(self, parentNodeID, clipName,
                                frameRate, dropMode, startTimecode):
        """Creates the destination clip node with the appropriate format and
        metadata.
        
        @param[in] parentNodeID \c{(str)} The parent node ID for the
                                destination clip.
        
        @param[in] clipName \c{(str)} The display name of the destination
                            clip.
        
        @param[in] frameRate \c{(float)} The frame rate of the destination
                             clip.
        
        @param[in] dropMode \c{(str)} Whether to use drop frame ("DF") or
                            non-drop frame ("NDF") timecode.
        
        @param[in] startTimecode \c{(str)} The starting timecode for the clip
                                 node in the form of hh:mm:ss:ff.
        
        @throws Raises a \c{WireTapException} if this method failed to create
                the clip node or set the number of frames.
        
        @return \c{(WireTapNodeHandle)} The destination clip node that was
                created.
        
        @note You must query the server for an updated \c{WireTapClipFormat}
              after successfully creating the clip node, because the server
              adds other metadata to the format.
        
        """
        clipFormat = CopyClipFormat(self.sourceClipFormat)
        clipFormat.setFrameRate(frameRate)  # allow Hiero to override
        
        # NOTE: Other metadata like timestamp and duration will be added
        # automatically when the clip is created and the frames preallocated.
        clipFormat.setMetaData('<XML Version="1.0">'
                               '<ClipData>'
                               '<DropMode>{0}</DropMode>'
                               '<SrcTimecode>{1}</SrcTimecode>'
                               '</ClipData>'
                               '</XML>'.format(dropMode, startTimecode))
        
        parentNode = WireTapNodeHandle(self.destinationServer, parentNodeID)
        clip = WireTapNodeHandle()
        if not parentNode.createClipNode(clipName, clipFormat, "CLIP", clip):
            raise WireTapException("Unable to create clip node: {0}".format(
                parentNode.lastError()))
        
        # Results in the <Duration> element being added to the clip format
        if not clip.setNumFrames(self.numFrames):
            raise WireTapException(
                "Unable to set the number of frames: {0}".format(
                    parentNode.lastError()))
        return clip
    
    def __CopyFrame(self, sourceIndex, destinationIndex):
        """Copies a single frame from the source to the destination clip node.
        
        @param[in] sourceIndex \c{(int)} The frame index of the source clip to
                               be copied.
        
        @param[in] destinationIndex \c{(int)} The destination frame index.
        
        @throws Raises a \c{WireTapException} if this method failed to read or
                write the frame.
        
        @note The Wiretap SDK guide states that since "each thread is
              contending for the same network pipe, there is not much benefit
              in performing multi-threaded I/O.  It would be better to
              serialize the requests from each thread." (Appendix A, p. 104)
        
        """
        # Read frame from the source clip.  Note that Boost magically stores
        # the results in the output parameter framebuffer (Python strings are
        # usually immutable).
        frameBuffer = '0'*self.sourceClipFormat.frameBufferSize()
        if not self.sourceClip.readFrame(sourceIndex, frameBuffer,
                self.sourceClipFormat.frameBufferSize()):
            raise WireTapException("Unable to read frame {0}: {1}.".format(
                sourceIndex, self.sourceClip.lastError()))
        
        # Write frame to the destination clip
        if not self.destinationClip.writeFrame(destinationIndex, frameBuffer,
                self.destinationClipFormat.frameBufferSize()):
            raise WireTapException("Unable to write frame {0}: {1}.".format(
                destinationIndex, self.destinationClip.lastError()))
    
    def CopyFrames(self):
        """Copies frames from the source to the destination Wiretap server
        using the node IDs and frame ranges specified during object
        construction.
        
        """
        for ii in xrange(self.numFrames):
            self.__CopyFrame(self.startFrame + ii, ii)
             
            # Print progress and flush to allow the host application to parse
            # the output immediately.
            print "Wrote frame {0} of {1}.".format(ii + 1, self.numFrames)
            sys.stdout.flush()


def ResolveDisplayPath(server, displayPath, create):
    """Resolves a Wiretap display path into the first node handle with a
    matching display name.
    
    @details Currently, only libraries and reels can be created if not found on
             the display path.
    
    @param[in] server \c{(WireTapServerHandle)} The Wiretap server associated
                      with the display path.
    
    @param[in] displayPath \c{(str)} The pseudo node ID to the library or reel
                           consisting of node display names joined by forward
                           slashes.
    
    @param[in] create \c{(bool)} Whether to create the missing library and reel
                      if the specified display path doesn't exist.
    
    @throws Raises a \c{WireTapException} if no matching node was found.
    
    @return \c{(WireTapNodeHandle)} The Wiretap node that was created or found
            to match the given display path.
    
    """
    node = WireTapNodeHandle()
    if WireTapResolveDisplayPath(server, displayPath, node):
        return node.getNodeId().id()
    elif create:
        node = CreateNodeContainers(server, displayPath)
        return node.getNodeId().id()
    raise WireTapException("There is no existing node ID that matches the "
                           "given display path: " + displayPath)
    

def CreateNodeContainers(server, displayPath):
    """Creates libraries and/or reels along the given display path if they do
    not already exist.
    
    @details Reels and clips have display names that differ from their internal
             node IDs.  For safety and technical reasons, this function does
             not create volumes or projects.
    
    @param[in] server \c{(WireTapServerHandle)} The Wiretap server associated
                      with the display path.
    
    @param[in] displayPath \c{(str)} The pseudo node ID to the library or reel
                           consisting of node display names joined by forward
                           slashes.
    
    @throws Raises a <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.ValueError" target="_blank">
            ValueError</a> if the \pn{displayName} includes a clip name.
    
    @throws Raises a \c{WireTapException} if node creation fails.
    
    @return \c{(WireTapNodeHandle)} The Wiretap node that was created or found
            to match the given display path.
    
    """
    minSegments = 3  # at least /VOLUME/PROJECT/LIBRARY
    maxSegments = 4  # at most /VOLUME/PROJECT/LIBRARY/REEL
    segments = [seg for seg in displayPath.split('/') if seg]
    if len(segments) < minSegments or len(segments) > maxSegments:
        raise ValueError("The display path must include at least a library "
                         "and/or a reel, but should not include a clip name.")
    
    # Although only libraries and reels need to be created for now, the loop
    # below allows for extension to other node types.
    node = None
    NODE_TYPES = ('VOLUME', 'PROJECT', 'LIBRARY', 'REEL', 'CLIP')
    parentNodeID = '/' + '/'.join(segments[0:2])  # start with PROJECT node
    for ii in xrange(minSegments - 1, len(segments)):
        
        # Get handle to parent node and create child node if non-existent
        parentNode = WireTapNodeHandle(server, parentNodeID)
        node = WireTapNodeHandle()
        if not WireTapFindChild(parentNode, segments[ii], node):
            
            node = WireTapNodeHandle()  # re-initialize
            if not parentNode.createNode(segments[ii], NODE_TYPES[ii], node):
                raise WireTapException("Unable to create {0} node: {1}".format(
                    NODE_TYPES[ii], '/' + '/'.join(segments[0:ii])))
            
            print('Created a {0} node "{1}" at {2}:IFFFS{3}').format(
                NODE_TYPES[ii], segments[ii], server.getHostName(),
                parentNodeID)
        
        parentNodeID = node.getNodeId().id()  # refresh parent node ID
    
    return node


def GetClipFormat(clip):
    """Retrieves the clip format from the given clip node.
    
    @details Wraps \c{WireTapNodeHandle.getClipFormat()} and converts a failed
             return state to an exception.
    
    @param[in] clip \c{(WireTapNodeHandle)} The clip node whose format is to be
                    queried.
    
    @throws Raises a \c{WireTapException} if unable to retrieve the clip
            format.
            
    @return \c{(WireTapClipFormat)} The clip format associated with the clip
            node.
    
    """
    clipFormat = WireTapClipFormat()
    if not clip.getClipFormat(clipFormat):
        raise WireTapException("Unable to obtain clip format: {0}.".format(
            clip.lastError()))
    return clipFormat


def CopyClipFormat(clipFormat):
    """Uses properties from the source clip format to generate a duplicate.
    
    @details Unlike the \c{WireTapClipFormat} copy constructor, this method
             purposely ignores the clip format's framebuffer size and metadata.
    
    @param[in] clipFormat \c{(WireTapClipFormat)} The source clip format from
                          which key parameters will be copied (excluding
                          metadata like drop mode, duration, and timestamp).
    
    @return \c{(WireTapClipFormat)} The duplicated clip format object.
     
    """
    # NOTE: Could actually just concatenate "_le" to the format, but use the
    # constants anyway in case Autodesk changes the strings in the future.
    rgbFormatMap = {
        WireTapClipFormat.FORMAT_RGB():
            WireTapClipFormat.FORMAT_RGB_LE(),
        WireTapClipFormat.FORMAT_RGB_FLOAT():
            WireTapClipFormat.FORMAT_RGB_FLOAT_LE(),
        WireTapClipFormat.FORMAT_RGBA():
            WireTapClipFormat.FORMAT_RGBA_LE(),
        WireTapClipFormat.FORMAT_RGBA_FLOAT():
            WireTapClipFormat.FORMAT_RGBA_FLOAT_LE()
    }
    
    # Map all big endian RGB formats to their little endian counterparts
    try:
        formatTag = rgbFormatMap[clipFormat.formatTag()]
    except KeyError:  # not an RGB format
        formatTag = clipFormat.formatTag()
    
    return WireTapClipFormat(
        clipFormat.width(),
        clipFormat.height(),
        clipFormat.bitsPerPixel(),
        clipFormat.numChannels(),
        clipFormat.frameRate(),
        clipFormat.pixelRatio(),
        clipFormat.scanFormat(),
        formatTag)


def GetClipFrameCount(clip):
    """Retrieves the number of frames from the given clip node.
    
    @details Wraps \c{WireTapNodeHandle.getNumFrames()}, converts a failed
             return state to an exception, and handles the conversion from
             \c{WireTapInt} to \c{int}.
    
    @param[in] clip \c{(WireTapNodeHandle)} The clip node whose frame count is
                    to be queried.
    
    @throws Raises a \c{WireTapException} if unable to retrieve the clip's
            frame count.
            
    @return \c{(int)} The number of frames in the given clip node.
    
    """
    numFrames = WireTapInt()
    if not clip.getNumFrames(numFrames):
        raise WireTapException(
            "Unable to obtain number of frames: {0}.".format(clip.lastError()))
    return int(numFrames)


def DeleteDuplicateClips(parentNode, displayName):
    """Deletes first-level child clips of \pn{parentNode} that have the same
    display name.
    
    @param[in] parentNode \c{(WireTapNodeHandle)} The handle to the parent
                          library or reel containing the duplicate clips.
    
    @param[in] displayName \c{(str)} The non-unique display name of the clips
                           that should be deleted.
    
    @return \c{(tuple)} The node IDs that could not be deleted.
    
    """
    notDeleted = []
    children = GetChildren(parentNode)
    for child in children:
        isClipNode = WireTapInt(0)
        if child.getIsClipNode(isClipNode):  # whether the query succeeded
            if int(isClipNode) and GetDisplayName(child) == displayName:
                nodeID = child.getNodeId().id()
                if child.destroyNode():
                    print('Deleted duplicate clip node "{0}": {1}'
                          .format(displayName, nodeID))
                else:
                    notDeleted.append(nodeID)
                    print('Unable to delete duplicate clip node "{0}": {1}'
                          .format(displayName, nodeID))
    return tuple(notDeleted)


def ParseArguments(*args):
    """Parses command-line arguments and converts them to the proper data
    types.
    
    @param[in] args \c{(tuple)} Server information, node paths, and other
                    options for the frame copier.
    
    @throws Raises a <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.ValueError" target="_blank">
            ValueError</a> if there are missing arguments.
    
    @return \c{(tuple)} The processed command line arguments.
    
    @todo Use \c{argparse} for more flexible processing of command-line
          parameters.
    
    """
    NUM_REQ_ARGS = 11
    NUM_OPT_ARGS = 2
    MAX_ARGS = NUM_REQ_ARGS + NUM_OPT_ARGS
    
    # Required arguments that need converting
    USE_DISPLAY_NAME = 5
    CREATE_PARENT_NODE = 6
    OVERWRITE_CLIP = 7
    FRAME_RATE = 8
    
    # Optional arguments to be checked
    START_FRAME = NUM_REQ_ARGS
    END_FRAME = NUM_REQ_ARGS + 1
    
    # Check for wrong number of arguments
    if len(args) < NUM_REQ_ARGS:
        msg = (
            "Missing required arguments: {0} were entered, but at least {1} "
            "are required, and {2} more are optional."
        ).format(len(args), NUM_REQ_ARGS, NUM_OPT_ARGS)
        raise ValueError(msg)
    elif NUM_REQ_ARGS < len(args) < MAX_ARGS:
        raise ValueError("When specifying a frame range, both the starting "
                         "and ending frames of the clip are required.")
    elif len(args) > MAX_ARGS:
        msg = (
            "Too many arguments: {0} were entered, but {1} is the maximum "
            "number of arguments allowed, including optional ones."
        ).format(len(args), MAX_ARGS)
        raise ValueError(msg)
    
    # Convert certain required arguments
    parsedArgs = list(args)[0:NUM_REQ_ARGS]
    parsedArgs[USE_DISPLAY_NAME] = bool(int(args[USE_DISPLAY_NAME]))
    parsedArgs[CREATE_PARENT_NODE] = bool(int(args[CREATE_PARENT_NODE]))
    parsedArgs[OVERWRITE_CLIP] = bool(int(args[OVERWRITE_CLIP]))
    parsedArgs[FRAME_RATE] = float(args[FRAME_RATE])
    
    # Interpret optional arguments
    if len(args) == MAX_ARGS:
        startFrame = int(args[START_FRAME])
        endFrame = int(args[END_FRAME])
        parsedArgs.append(min(startFrame, endFrame))
        parsedArgs.append(max(startFrame, endFrame))
    
    return tuple(parsedArgs)


def main():
    """Parses command line arguments and creates a frame copier object to write
    ("stonify") frames on a Wiretap IFFFS server.
    
    """
    parsedArgs = ParseArguments(*sys.argv[1:])
    try:
        frameCopier = FrameCopier(*parsedArgs)
        frameCopier.CopyFrames()
    except WireTapException:
        exc_info = sys.exc_info()
        raise exc_info[0], exc_info[1], exc_info[2]  # re-raise with traceback
    finally:
        WireTapClientUninit()  # ensure cleanup

if __name__ == '__main__':
    main()


## @}
