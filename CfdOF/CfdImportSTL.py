# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2020 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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

import FreeCAD
import Mesh
import os
import tempfile

# This module provides tools to import multi-patch
# ascii STL files. It is an alternative to the standard Mesh STL
# importer, but supports reading multiple patches
# in a single STL file

# Python's open is masked by the function below
if open.__module__ in ['__builtin__','io']:
    pythonopen = open


def open(filename):
    """ Called to open a file """
    docname = os.path.splitext(os.path.basename(filename))[0]
    doc = FreeCAD.newDocument(docname.encode("utf8"))
    doc.Label = docname
    return insert(filename, doc.Name)


def insert(filename, doc_name):
    """ Called to import a file """
    try:
        doc = FreeCAD.getDocument(doc_name)
    except NameError:
        doc = FreeCAD.newDocument(doc_name)
    FreeCAD.ActiveDocument = doc

    with pythonopen(filename) as infile:
        while True:  # Keep reading solids
            solidline = infile.readline()
            if not solidline:
                break
            solidlinewords = solidline.strip().split(' ', 1)
            if solidlinewords[0] != 'solid' or len(solidlinewords) != 2:
                raise RuntimeError("Expected line of the form 'solid <name>'")
            solidname = solidlinewords[1]
            with tempfile.TemporaryDirectory() as tmpdirname:
                filename = os.path.normpath(os.path.join(tmpdirname, solidname+'.stl'))
                with pythonopen(filename, mode='w') as tmp_file:
                    tmp_file.write(solidline)
                    while True:  # Keep reading triangles
                        line = infile.readline()
                        if not line:
                            break
                        tmp_file.write(line)
                        if line.startswith('endsolid'):
                            break
                Mesh.insert(filename, doc_name)

    FreeCAD.Console.PrintMessage("Imported " + filename + "\n")
    return doc
