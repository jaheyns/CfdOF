# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License as        *
# *   published by the Free Software Foundation, either version 3 of the    *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this program.  If not,                             *
# *   see <https://www.gnu.org/licenses/>.                                  *
# *                                                                         *
# ***************************************************************************

# Versions required

FC_MAJOR_VER_REQUIRED = 0
FC_MINOR_VER_REQUIRED = 20
FC_PATCH_VER_REQUIRED = 0
FC_COMMIT_REQUIRED = 29177

CF_MAJOR_VER_REQUIRED = 1
CF_MINOR_VER_REQUIRED = 30

HISA_MAJOR_VER_REQUIRED = 1
HISA_MINOR_VER_REQUIRED = 13
HISA_PATCH_VER_REQUIRED = 2

MIN_FOUNDATION_VERSION = 9
MIN_OCFD_VERSION = 2206
MIN_MINGW_VERSION = 2212

MAX_FOUNDATION_VERSION = 13
MAX_OCFD_VERSION = 2506
MAX_MINGW_VERSION = 2212


# Default download locations

OPENFOAM_URL = \
    "https://github.com/blueCFD/Core/releases/download/blueCFD-Core-2024-1/blueCFD-Core-2024-1-win64-setup.exe"
OPENFOAM_FILE_EXT = ".exe"
PARAVIEW_URL = \
    "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.10&type=binary&os=Windows&downloadFile=ParaView-5.10.1-Windows-Python3.9-msvc2017-AMD64.exe"
PARAVIEW_FILE_EXT = ".exe"
CFMESH_URL = \
    "https://sourceforge.net/projects/cfmesh-cfdof/files/cfmesh-cfdof.zip/download"
CFMESH_URL_MINGW = \
    "https://sourceforge.net/projects/cfmesh-cfdof/files/cfmesh-cfdof-binaries-{}.zip/download"
CFMESH_FILE_BASE = "cfmesh-cfdof"
CFMESH_FILE_EXT = ".zip"
HISA_URL = \
    "https://sourceforge.net/projects/hisa/files/hisa-master.zip/download"
HISA_URL_MINGW = \
    "https://sourceforge.net/projects/hisa/files/hisa-master-binaries-{}.zip/download"
HISA_FILE_BASE = "hisa-master"
HISA_FILE_EXT = ".zip"
DOCKER_URL = \
    "docker.io/mmcker/cfdof-openfoam"


# Some standard install locations that are searched if an install directory is not specified
# Supports variable expansion and Unix-style globs (in which case the last lexically-sorted match will be used)
FOAM_DIR_DEFAULTS = {'Windows': ['C:\\blueCFD-Core-*',
                                 'C:\\Program Files\\blueCFD-Core-*\\OpenFOAM-*'
                                 'C:\\Program Files\\ESI-OpenCFD\\OpenFOAM\\v*',
                                 '~\\AppData\\Roaming\\ESI-OpenCFD\\OpenFOAM\\v*'],
                     'Linux': ['/opt/openfoam*', '/opt/openfoam-dev',  # Foundation official packages
                               '/usr/lib/openfoam/openfoam*',  # ESI official packages
                               '~/openfoam/OpenFOAM-v*',
                               '~/OpenFOAM/OpenFOAM-*.*', '~/OpenFOAM/OpenFOAM-dev'],  # Typical self-built locations
                     "Darwin": ['~/OpenFOAM/OpenFOAM-*.*', '~/OpenFOAM/OpenFOAM-dev']
                     }

PARAVIEW_PATH_DEFAULTS = {
                    "Windows": ["C:\\Program Files\\ParaView *\\bin\\paraview.exe"],
                    "Linux": ["/usr/bin/paraview", "/usr/local/bin/paraview"],
                    "Darwin": ["/Applications/ParaView-*.app/Contents/MacOS/paraview"]
                    }
