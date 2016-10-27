"""A Hiero task and preset for sending shots to a Stone FS via Wiretap.

@author Brendan Holt
@date March 2014
@see \ref modStonify
@defgroup modFnStonify FnStonify
@{

"""
import os.path
import platform
from Queue import Queue, Empty
import re
import subprocess
import sys
from threading import Thread

import hiero.core
from hiero.core import Timecode  # only accessible when Hiero is running

from CBSD import Path
from wiretap import WireTapException
from WiretapBrowser import SplitNodePath
from WiretapTools import SplitHostname


## \c{(re.RegexObject)} A cached regular expression object for parsing the
#  progress reported in the Stonify script's standard output.
PROGRESS_REGEX = re.compile(r'^Wrote frame (\d+) of (\d+)\.$')


class StonifyTask(hiero.core.TaskBase):
    """A custom Hiero task that copies the frames from the selected shot to the
    designated Wiretap clip node.
    
    @details This task launches an external process through the Stonify script.
    
    """
    
    def __init__(self, initDict):
        """Constructs a Stonify task given an initialization dictionary.
        
        @param[in] initDict \c{(FnExporterBase.TaskData)} Task initialization
                            data.
        
        """
        super(StonifyTask, self).__init__(initDict)
        
        ## \c{(Queue)} Stores messages from the Stonify script's standard
        #  output.
        self.__stdoutQueue = Queue()
        
        ## \c{(int)} The index of the current frame being copied.
        self.__frameIndex = 0
        
        ## \c{(int)} The starting frame's file number in the output range.
        self.__start = 0
        
        ## \c{(int)} The ending frame's file number in the output range.
        self.__end = 0
        self.__start, self.__end = self.outputRange()
        
        ## \c{(int)} The total number of frames in the selected shot.
        self.__numFrames = self.__end - self.__start + 1
        
        ## \c{(hiero.core.TimeBase)} The sequence frame rate.
        self.__timeBase = self._sequence.framerate()
        
        ## \c{(bool)} Whether the sequence timecode is displayed in drop frame
        #  format.
        #
        #  @see Documentation was copied from
        #       \c{hiero.core.Sequence.dropFrame()}.
        self.__isDropFrame = self._sequence.dropFrame()
        
        ## \c{(bool)} Whether the associated media is a movie container.
        self.__isVideoFile = hiero.core.isVideoFileExtension(self.fileext())
    
    def startTask(self):
        """Analyzes the source media and collects the necessary Wiretap
        parameters in order to execute the Stonify script.
        
        @details Called when task reaches head of the export queue and begins
                 execution.
        
        @see Documentation was partially copied from
             \c{hiero.core.FnExporterBase.TaskBase.startTask()}.
        
        """
        # Don't call TaskBase.startTask() because it will try to make
        # directories.  Instead, just run the pre-sequence method.
        self.preSequence()
        
        if not self._preset.properties()['isWiretapShotProcess']:
            print("WARNING: Stonify tasks should be executed with the Wiretap "
                  "Shot Processor.")
        
        # The following checks for media presence and cut handles were borrowed
        # from hiero.exporters.FnFrameExporter
        if not self._source.isMediaPresent() and self._skipOffline:
            return
        
        if self._cutHandles is not None:
            if self._retime:
                raise NotImplementedError("Retimes are not yet supported when "
                                          "exporting via Wiretap.")
        
        scriptPath = os.path.join(os.path.dirname(__file__),
                                  '../scripts/Stonify.py')
        scriptPath = os.path.normpath(scriptPath)
        
        # Format the source and destination node paths
        hostname, dstParentNodeID, dstClipName = self.__ResolvePaths()
        
        if self.__isVideoFile:  # TO DO: only necessary if specifically ProRes
            srcHost = self._preset.propertiesValue('osxGatewayHost')
        else:
            srcHost = hostname + ':Gateway'
        dstHost = hostname + ':IFFFS'
        srcNodeID = self.FormatSourcePath()
        
        # LIBRARY/REEL/CLIP creation parameters set to '1' or str(int(True))
        useDisplayName = '1'  # TO DO: provide a toggle for this case
        createParentNodeID = '1'
        overwriteClip = '1'
        
        # Format the frame and time information
        # NOTE: Like Hiero, Wiretap interprets 23.98 FPS as 23.976 FPS; can use
        # string labels instead of float conversion
        frameRate = self.__timeBase.toString()
        dropMode = 'DF' if self.__isDropFrame else 'NDF'
        startTimecode = self.__GetStartTimecode()
        
        command = [
            GetBinaryPath('python'), scriptPath,
            srcHost, srcNodeID,
            dstHost, dstParentNodeID, dstClipName,
            useDisplayName, createParentNodeID, overwriteClip,
            frameRate, dropMode, startTimecode
        ]
        
        # Wiretap cannot reference a sub-clip of a video file with "@CLIP"
        # syntax, so pass the frame range as well
        if self.__isVideoFile:
            command.extend(map(str, [self.__start, self.__end]))
        
        ON_POSIX = 'posix' in sys.builtin_module_names
        self.process = subprocess.Popen(command, shell=False,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        bufsize=1,
                                        close_fds=ON_POSIX)
        
        # Monitor stdout in a separate thread to track upload progress
        stdoutMonitor = Thread(target=self.EnqueueOutput,
                               args=(self.process.stdout, self.__stdoutQueue))
        stdoutMonitor.daemon = True
        stdoutMonitor.start()
    
    def taskStep(self):
        """Polls the Stonify subprocess and parses its standard output to
        determine task progress.
        
        @details Called every frame until task completes.  The task may
                 continue to run in the background.
        
        @retval True Indicates that the task requires more steps.
        @retval False Indicates synchronous processing of the task is complete.
    
        @see Documentation was partially copied from
             \c{hiero.core.FnExporterBase.TaskBase.taskStep()}.
        
        """
        returncode = self.process.poll()
        if returncode:  # there are errors
            raise WireTapException(self.__CollectErrors())
        
        # Attempt to read output from the queue without blocking
        try:
            line = self.__stdoutQueue.get_nowait()
        except Empty:  # no output yet
            pass
        else:  # update the current frame index based on the subprocess output
            try:
                self.__frameIndex = self.ParseProgressOutput(line.strip())[0]
            except IndexError:  # output didn't contain frame information
                pass
        
        return self.__frameIndex < self.__numFrames
    
    def progress(self):
        """Reports a value between 0 and 1 to indicate the progress of the
        task.
        
        @details The task is considered complete once the progress equals
                 1.
        
        @return \c{(float)} The fraction of work completed.
        
        @see Documentation was partially copied from
             \c{hiero.core.FnExporterBase.TaskBase.progress()}.
        
        """
        if self._finished:
            return 1.0
        return float(self.__frameIndex)/self.__numFrames
    
    def forcedAbort(self):
        """Terminates the Stonify subprocess if it is still running.
        
        @details Called by Hiero when the user presses the Abort
                 button.
        
        @see Documentation was partially copied from \c{ITask.forcedAbort()} in
             the <em>Hiero Python Developer Guide</em>.
        
        """
        if hasattr(self, 'process') and self.process.poll() is None:
            try:
                self.process.terminate()
            except OSError as why:
                print "Failed to terminate the Wiretap process: " + str(why)
    
    def __ResolvePaths(self):
        """Extracts the Wiretap server hostname, parent node ID, and clip name
        from this task's shot path.
        
        @throws Raises a <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.ValueError" target="_blank">
                ValueError</a> if the shot path does not have the minimum
                number of segments (i.e. a path in the form of
                \c{/VOLUME/PROJECT/LIBRARY/[REEL]/CLIP}).
        
        @return \c{(tuple)} The resolved Wiretap server hostname, parent node
                ID, and clip name.
        
        """
        # Decompose the shot path into the hostname, parent node ID, and clip
        # node name.  The hostname should not contain the product name (e.g.
        # Vid_WS17:IFFFS), but just in case, remove the colon and the text
        # after it.
        parentNodePath, clipName = os.path.split(self._shotPath)
        hostname, parentNodeID = SplitNodePath(parentNodePath)
        hostname = SplitHostname(hostname)[0]  # truncate text after colon
        
        # Perform limited path validation
        # NOTE: Node paths with blank display names are not supported because
        # Hiero does not let you set blank folder names in the export structure
        # viewer.
        segments = [seg for seg in parentNodeID.split('/') if seg]
        if len(segments) < 3:
            raise ValueError("Shots/clips sent to a Stone FS require a "
                             "volume, project, library, and optionally a reel "
                             "node in the parent node path: "
                             "/VOLUME/PROJECT/LIBRARY/[REEL]/CLIP")
        
        # Resolve tokens
        return tuple(map(self.resolvePath, [hostname, parentNodeID, clipName]))
        
    def EnqueueOutput(self, fileHandle, queue):
        """Enqueues each line of the standard output from an external process.
        
        @param[in] fileHandle \c{(file)} The standard output stream from the
                              external process.
        
        @param[in] queue \c{(Queue.Queue)} The object for holding the queued
                         output lines.
        
        @see <a href="http://stackoverflow.com/a/4896288" target="_blank">
             Non-blocking read on a subprocess.PIPE</a>
        
        """
        for line in iter(fileHandle.readline, b''):
            queue.put(line)
        fileHandle.close()

    def ParseProgressOutput(self, text):
        """Parses the Stonify subprocess output to determine the index of the
        frame that was copied.
        
        @param[in] text \c{(str)} An output line in the form "Wrote frame
                        [index] of [total]."
        
        @return \c{(tuple)} The current integer frame index and total number of
                frames.
        
        @see \ref FnStonify.PROGRESS_REGEX() "FnStonify.PROGRESS_REGEX"
        
        """
        print text
        matchObj = PROGRESS_REGEX.match(text)
        if matchObj:
            return tuple([int(ii) for ii in matchObj.groups()])
        return ()
    
    def __CollectErrors(self):
        """Collects the exception(s) from the Stonify subprocess' standard
        error stream.
        
        @details \c{stderr} is only read if the Stonify subprocess has
                 ended.
        
        @return \c{(str)} The exception trace and message, if any.
        
        """
        # It is unknown if reading from stderr blocks execution, so only read
        # if the subprocess is not running.  If the return code is 0, there
        # probably won't be errors anyway.  In either case, this function will
        # return an empty string.
        if self.process.poll() is not None:
            return '\n'.join(self.process.stderr.readlines())
        return ''
    
    def FormatSourcePath(self):
        """Formats the path to the media source for Wiretap Gateway server
        access.
        
        @details If the source is an image sequence, the frame index is removed
                 and substituted with a frame range denoted by square brackets
                 before the file extension.  For both images and video files,
                 "@CLIP" is appended after the file extension.
        
        @return \c{(str)} The formatted path to the media source.
        
        """
        fileInfo = self._source.fileinfos()[0]
        
        # Format a single frame or a movie file.
        # Note: This check doesn't work on filenames ending in a number.
        if self._source.singleFile():
            
            # NOTE: Movie files do not support specific frame ranges, so the
            # start and end frames must be forwarded to the subprocess in
            # startTask().
            sourcePath = Path.Normalize(fileInfo.filename() + '@CLIP')
        
        # Format an image sequence
        else:
            # Hiero identifies a standalone frame ending in a number as part of
            # a sequence, so do not use a bracketed range in this case
            if self.__start == self.__end:
                frameRange = str(self.__start)
            else:  # only add range brackets if there is more than one frame
                frameRange = '[{0}-{1}]'.format(
                    self.filepadding() %self.__start,
                    self.filepadding() %self.__end)
            
            parentPath = os.path.dirname(fileInfo.filename())
            clipName = (self.filehead() + frameRange +
                        '.' + self.fileext() + '@CLIP')
            sourcePath = Path.Normalize(parentPath, clipName)
        
        # Replace leading double slash with single slash, if necessary
        if sourcePath[0:2] == '//':
            sourcePath = sourcePath[1:]
        
        return sourcePath
    
    def __GetStartTimecode(self):
        """Retrieves the starting timecode for the shot, accounting for the
        sequence timecode offset, the shot's position on the timeline, and the
        cut handles.
        
        @details Although semicolons indicate drop frame mode, the Wiretap
                 server will ignore that syntax unless the XML \c{DropMode}
                 element is set to \c{DF}.
        
        @return \c{(str)} The shot's starting timecode in the form of
                \c{hh:mm:ss:ff}.
        
        @warning Shot retimes are not yet supported.
        
        """
        if self.__isDropFrame:
            displayType = Timecode.kDisplayDropFrameTimecode
        else:
            displayType = Timecode.kDisplayTimecode
        
        time = (self._sequence.timecodeStart() + self._item.timelineIn() +
                self.outputHandles()[0])  # time is in units of frames
        tc = Timecode.timeToString(time, self.__timeBase,
                                   displayType, False, 0)
        return tc


class StonifyPreset(hiero.core.TaskPresetBase):
    """Stores settings for use with the Stonify task and task UI classes that
    may be configured in the Hiero export dialog.
    
    """
    def __init__(self, name, properties):
        """Sets up the Stonify task preset with default properties.
        
        @param[in] name \c{(str)} The preset name, usually handled
                        automatically by Hiero.
        
        @param[in] properties \c{(dict)} Preset properties to be updated.
        
        """
        super(StonifyPreset, self).__init__(StonifyTask, name)
        
        # NOTES:
        #
        # - Flame 2014 and newer natively support importing ProRes movies,
        #   so Mac Wiretap Gateways should not be necessary in the future.
        defaults = {
            'isWiretapShotProcess': False,  # Wiretap processor will enable
            'sourceHost': '',  # TO DO: allow overrides for source (read) host
            'osxGatewayHost': 'io-server:Gateway',  # N/A for Flame 2014+
        }
        self.properties().update(defaults)
        
        # Update preset with loaded data
        self.properties().update(properties)
    
    ## @cond NOT_IMPLEMENTED
    def addCustomResolveEntries(self, resolver):
        """Add resolvers for Wiretap servers, volumes, projects, and libraries.
        
        """
        pass
    ## @endcond
    
    def supportedItems(self):
        """Establishes that the associated task supports shots (track items).
        
        @return \c{(core.Hiero.Python.ITaskPreset.ItemTypes)} or \c{(long)} The
                supported item types which may be combined with bitwise \c{OR}
                operators.
        
        @todo Add support for \c{TaskPresetBase.kSequence}.
        
        """
        return hiero.core.TaskPresetBase.kTrackItem


def GetBinaryPath(executable):
    """Retrieves the absolute path to the platform-appropriate Hiero executable
    contained within the application folder.

    @details The three possible executables are \c{hiero}, \c{HieroNuke}, and
             \c{python}.  The Python interpreter returned belongs to the
             embedded copy of Nuke, not Hiero.

    @param[in] executable \c{(str)} The name of the Hiero command-line program
                          without the extension.

    @throws Raises a <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.ValueError" target="_blank">
            ValueError</a> if given an invalid executable name.
    
    @throws Raises an <a href="http://docs.python.org/2.6/library/exceptions.html#exceptions.OSError" target="_blank">
            OSError</a> if running an unsupported OS.

    @return \c{(str)} The absolute path to a Hiero executable.

    @see \c{hiero.core.hieroNukePath()}
    
    """
    HIERO_EXECUTABLES = ['hiero']
    HIERO_NUKE_EXECUTABLES = ['HieroNuke', 'python']
    EXECUTABLES = set(HIERO_EXECUTABLES) | set(HIERO_NUKE_EXECUTABLES)
    if executable not in EXECUTABLES:
        valid = ', '.join(EXECUTABLES)
        raise ValueError(
            'The executable name "{0}" is unsupported.  Valid Hiero binaries '
            "include: {1}".format(executable, valid))
    
    HIERO_PATH = os.path.dirname(sys.executable)
    binaryExt = ''
    
    systemOS = platform.system()
    if systemOS == 'Windows':
        binaryExt = '.exe'
        if executable in HIERO_EXECUTABLES:
            return os.path.join(HIERO_PATH, executable) + binaryExt
        else:
            return (os.path.join(HIERO_PATH, 'HieroNuke', executable) +
                    binaryExt)
    else:
        raise OSError("UNIX path information is not available at this time.")


hiero.core.taskRegistry.registerTask(StonifyPreset, StonifyTask)


## @}
