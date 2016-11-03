"""Enforces POSIX-style path joining and normalization regardless of OS.

@details Python 3 overcomes some of the limitations of Python 2 path
         manipulation.

@author Brendan Holt
@date October 2016
@defgroup modPath Path
@{

"""
import ntpath
import os
import posixpath
import re


def Join(pathSegment, *pathSegments):
    """Joins paths with forward slashes.

    @details posixpath.join() fails to replace backslashes in existing path
             chunks.

    @param[in] pathSegment \c{(str)} The first path segment that will be joined
                           to any additional path segments.

    @param[in] pathSegments \c{(tuple)} Optional path segments that will be
                            joined to the first given path.  Note that each
                            path segment may contain path separators.

    @return \c{(str)} The joined path.

    @see Use Normalize() to format network paths in a more OS-independent way.

    """
    outputPath = posixpath.join(pathSegment, *pathSegments)
    outputPath = outputPath.replace('\\ ', ' ').replace('\\', '/')
    return outputPath


def Normalize(fpath, mountMap=None):
    """Converts OS-specific path variations to a generalized style that uses
    forward slash path separators and UNC server shares instead of drive
    letters, if applicable.

    @details This function does not check for output path existence since the
             current Python environment might not have access to the server
             share as formatted.

    @param[in] fpath \c{(str)} The OS-specific file or folder path to be
                     normalized.

    @param[in] mountMap \c{(dict)} Maps Windows drive letters (uppercase letter
                        and colon) or UNIX mount points (/mnt/share) to either
                        a pseudo UNC-style path (//server/share) compatible
                        with UNIX, or another UNIX-style mount point.

    @return \c{(str)} The normalized path.

    @todo Remove illegal file characters?

    @todo Move some of this code into Segment() to keep //server/share a single
          unit.

    """
    if not mountMap:
        mountMap = {}

    # For easier analysis, segment and rejoin
    fpath = Join(fpath)  # convert to forward slashes
    root = fpath[:2].upper()  # will later analyze the first two characters
    segments = Segment(fpath)
    outputPath = Join(*segments)  # lacks leading slashes

    # Convert Windows drive letters to UNC paths, if possible
    # NOTE: ntpath.splitdrive() matches ANY character followed by a colon, not
    # just a letter.
    if re.match('[A-Z]:', root):

        # Fix for when user forgets slash separator after drive (e.g. "C:TEMP")
        # Does not correct multiple colons or other errors (e.g. C::TEMP)
        drive, pathSeg = ntpath.splitdrive(segments[0])
        if drive and pathSeg:
            segments.insert(0, root)  # insert drive letter in path segments
            segments[1] = segments[1][2:]  # remove drive letter from 2nd chunk

        # Reconstruct path with a UNC prefix or a capitalized drive letter
        try:
            segments[0] = mountMap[root]
        except KeyError:
            pass
        outputPath = Join(*segments)

    # Convert OS X and Linux mounts
    elif re.match('/[^/]', root):
        if len(segments) > 1:  # can potentially replace with a UNC path
            mount = '/{0}/{1}'.format(*segments[0:2])
            try:
                mount = mountMap[mount]
            except KeyError:
                pass
            outputPath = Join(mount, *segments[2:])
        else:
            outputPath = '/' + Join(*segments)

    # Already a UNC path
    elif root == '//':
        outputPath = Join(root, *segments)
        if len(segments) == 0:  # reduce a bunch of slashes to root symbol
            outputPath = '/'

    return outputPath


def Segment(fpath):
    """Splits a file or folder path into its constituent path segments
    regardless of whether the path contains forward slashes, backslashes, or
    both.

    @param[in] fpath \c{(str)} The OS-specific file or folder path to be split
                     by any path separator.

    @return \c{(list)} The resulting path segments.

    @todo Do not split network mount, if possible.

    """
    fpath = os.path.normpath(fpath)
    fpath = fpath.strip().replace('\\ ', ' ').replace('\\', '/')
    return [i for i in fpath.split('/') if i]


## @}
