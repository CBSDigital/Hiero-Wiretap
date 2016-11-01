# Hiero<>Wiretap
A custom Hiero shot processor and task for sending shots to an Autodesk Stone FS via Wiretap.

Developed by Brendan A. Holt and Andrew D. Britton  
Software Development Department  
CBS Digital

## Overview
Hiero<>Wiretap is a plugin for The Foundry’s HIERO that allows the user to export selected shots in the timeline to a library or reel on an Autodesk IFFFS server (Stone FS). Many standard VFX formats are supported via Wiretap Gateway, including Apple ProRes and DPX/EXR image sequences.

Using the Wiretap SDK, we can directly create/copy projects, libraries, reels, clips, etc. on a Stone FS, which could be useful for future integration with other 3D/2D applications that need to publish to Flame framestores.

Hiero<>Wiretap consists of three main components and is tightly integrated with Hiero’s export system:

### Stonify Task
An export routine that copies frames from the selected Hiero shot to the designated Wiretap clip node. Stonify tasks are assigned to leaf elements in the export structure viewer.

### Wiretap Shot Processor
A custom shot processor that works in tandem with the Stonify task and provides a streamlined interface for translating Wiretap node paths into appropriate export structures. Regular exports (Transcode Images, Copy Exporter, etc.) to the local/network file system are also supported.

### Wiretap Browser
A window for browsing Wiretap server trees and selecting a destination library or reel for the new clip.

## Dependencies
Hiero<>Wiretap was originally created for Hiero 1.8 and Flame 2012&mdash;it will probably need some work to get the Wiretap Shot Processor up and running in Hiero/Nuke Studio 10.x. Also, the Wiretap 2017 Python bindings may need to be recompiled (with Boost) if for some reason the binaries aren't compatible with either Nuke 10.x or the system's Python.

## Future Development
Due to other priorities, CBS Digital has ceased development on Hiero<>Wiretap. Autodesk has since improved their documentation on Open Clip files and introduced new Python hooks with the advent of Shotgun/Flame integration. These technologies provide other avenues for accessing conformed shots in Flame. Regardless, the visual effects community may find aspects of this project useful. If so, we hope that those parties will share their findings.

## Legal Information
HIERO is a registered trademark of The Foundry Visionmongers, Ltd.  
Wiretap is a registered trademark of Autodesk, Inc.

CBS Digital has developed this tool independently of The Foundry and Autodesk and released the source code under a permissive license. The software is provided as-is with no warranty of any kind. See the license file for more details.
