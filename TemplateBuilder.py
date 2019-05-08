# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

from __future__ import print_function
import re
import os


class BracketError(ValueError):
    pass


class TemplateBuilder(object):
    """ Build a case directory from a template directory by substituting
     values in a python settings dictionary """
    def __init__(self,
                 case_path,
                 template_path,
                 settings):
        if case_path[0] == "~":
            case_path = os.path.expanduser(case_path)
        self.case_path = os.path.abspath(case_path)
        self.settings = settings
        self.template_path = template_path

        self.buildDir('.')

    def buildDir(self, rel_dir):
        """ Recursively build files in dir (relative to case base) """
        full_dir = os.path.join(self.template_path, rel_dir)
        for f in os.listdir(full_dir):
            rel_file = os.path.join(rel_dir, f)
            # Ignore files beginning with underscore so they can be used as includes
            if os.path.basename(rel_file)[0] != '_':
                if os.path.isdir(os.path.join(self.template_path, rel_dir, f)):
                    self.buildDir(rel_file)
                else:
                    contents = self.buildFile(rel_file, [])
                    # Do not write a blank file - provides a way for optional creation of files
                    if len(contents):
                        self.writeToFile(rel_file, contents)

    def writeToFile(self, rel_file, contents):
        # Make sure directory tree exists
        path = os.path.join(self.case_path, os.path.dirname(rel_file))
        try:
            os.makedirs(path)
        except OSError as exc:
            import errno
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
        # Write file
        with open(os.path.join(self.case_path, rel_file), 'w') as ofid:
            ofid.write(contents)

    def buildFile(self, rel_file, params):
        """ Open the specified template file, make replacements, and return as a string """
        try:
            fid = open(os.path.join(self.template_path, rel_file))
        except IOError:
            # Special cases:
            # 1. Don't worry if files that end with "None" do not exist
            if rel_file.endswith("None"):
                return ""
            # 2. If a file is not found, try the same file with 'default' after the last underscore
            rel_file_default = rel_file.rsplit("_", 1)[0] + "_default"
            try:
                fid = open(os.path.join(self.template_path, rel_file_default))
            except IOError:
                raise IOError("Error reading file {} in template path {}".format(rel_file, self.template_path))
            finally:
                rel_file = rel_file_default
        contents = fid.read()
        fid.close()
        try:
            contents = self.process(contents, rel_file, params)
        except BracketError as err:
            raise ValueError("Bracket matching error in {}: {}".format(rel_file, str(err)))
        except ValueError as err:
            raise ValueError("Error in {}: {}".format(rel_file, str(err)))
        except Exception as err:
            print("Unexpected error building file {}: {}".format(rel_file, str(err)))
            raise
        return contents

    def findAtCurrentLevel(self, string, find_string, start):
        """ Find the specified string, ignoring anything inside brackets """
        brackets = {'%(': '%)', '%[': '%]', '%{': '%}'}
        while True:
            n = string.find(find_string, start)
            if n < 0:
                return None
            next_bra = [string.find(b, start) for b in brackets.keys()]
            next_ket = [string.find(b, start) for b in brackets.values()]
            for i in range(len(next_bra)):
                if next_bra[i] < 0:
                    next_bra[i] = len(string)
            for i in range(len(next_ket)):
                if next_ket[i] < 0:
                    next_ket[i] = len(string)
            if min(next_ket) < min(next_bra):
                if n <= min(next_ket):
                    return n
                else:
                    return None
            else:
                if n <= min(next_bra):
                    return n
                else:
                    end = self.findClosingBracket(string, min(next_bra))
                    start = end+2

    def findClosingBracket(self, string, start):
        """ Find the closing bracket corresponding to the one at the start """
        brackets = {'%(': '%)', '%[': '%]', '%{': '%}'}
        bra = string[start:start+2]
        ket = brackets[bra]
        found = self.findAtCurrentLevel(string, ket, start+2)
        if found is None:
            raise BracketError("Error matching {} ...".format(string[start:start+40]))
        else:
            return found

    def process(self, contents, curr_file, params):
        """ Processes the contents string at the current level (does not go inside brackets - this is done
        recursively inside the functions """
        # print("Before processConditionals {} {}:\n".format(curr_file, params), contents)
        contents = self.processConditionals(contents, curr_file, params)
        # print("Before processBraces {} {}:\n".format(curr_file, params), contents)
        contents = self.processBraces(contents, curr_file, params)
        # print("Before makeVarSubstitutions {} {}:\n".format(curr_file, params), contents)
        contents = self.makeVarSubstitutions(contents, curr_file, params)
        # print("Before makeFileSubstitutions {} {}:\n".format(curr_file, params), contents)
        contents = self.makeFileSubstitutions(contents, curr_file, params)
        # print("Final:\n", contents)
        return contents

    def processConditionals(self, contents, curr_file, params):
        """ Select the relevant conditional block introduced by %:key1 key2 ... by matching the first parameter on 
        the stack, and process the block with that parameter removed """
        # Find first conditional
        start = self.findAtCurrentLevel(contents, "%:", 0)
        if start is None:
            return contents
        pos = start
        # Loop tags
        while pos < len(contents):
            end = self.findAtCurrentLevel(contents, "%:", pos+2)
            if end is None:
                end = len(contents)
            block = contents[pos:end]
            endOfKey = self.findAtCurrentLevel(block, "\n", 0)
            matchKeys = block[2:endOfKey]
            block = block[endOfKey+1:]
            # Process matchKeys
            matchKeys = self.process(matchKeys, curr_file, params)
            matchKeys = matchKeys.split()
            if params[0] in matchKeys or "default" in matchKeys:
                block = self.process(block, curr_file, params[1:])  # Remove first (matching) param inside block
                return contents[:start]+block
            pos = end
        return contents[:start]

    def processBraces(self, contents, curr_file, params):
        """ Process brace substitutions. Format:
        %{val1 [val2]\n
        content
        %} [output-file]\n
        pushes values onto the parameter stack, one by one and repeats content for each """
        while True:
            start = contents.find("%{")
            if start < 0:
                break
            end = self.findClosingBracket(contents, start)
            replace = contents[start+2:end]
            # Split into keys and contents
            delim = self.findAtCurrentLevel(replace, '\n', 0)
            if delim is None:
                delim = len(replace)
            keys = replace[:delim]
            # Make any replacements in keys
            keys = self.process(keys, curr_file, params)
            keys = keys.split(' ')
            replace = replace[delim+1:]
            # Extract trailing filename parameter if any
            trailing_nl = self.findAtCurrentLevel(contents, '\n', end+2)
            filename_param = None
            if trailing_nl is not None:
                filename_param = contents[end+2:trailing_nl].strip()
            # Loop the content passing values
            replacement = ""
            for v in keys:
                filename = None
                if filename_param:
                    # Process filename with parameter
                    filename = self.process(filename_param, curr_file, [v] + params)
                    if not filename:
                        raise ValueError("File name parameter " + filename_param + "evaluates to nothing")
                processed = self.process(replace, filename if filename else curr_file, [v] + params)
                if filename:
                    self.writeToFile(filename, processed)
                else:
                    replacement += processed
            replace = replacement
            afterEnd = (trailing_nl+1 if trailing_nl else end+2)
            contents = contents[:start] + replace + contents[afterEnd:]
        return contents

    def makeVarSubstitutions(self, contents, curr_file, params):
        """ Perform variable substitutions. Format:
        %(key/in/settings/dict%) key/in/settings/dict is the name of a variable 
        in the settings dict, with subdicts separated by backslashes, or a numeric value on the
        parameter stack. If 
        key/in/settings/dict specifies a dictionary or a list, its keys/values 
        are outputted separated by white space """
        while True:
            start = contents.find("%(")
            if start < 0:
                break
            end = self.findClosingBracket(contents, start)
            key = contents[start+2:end]
            # Make any replacements
            key = self.process(key, curr_file, params)
            # Special case - if key is a number, treat as positional parameter
            match = re.match("[0-9]+", key)
            if match and match.span() == (0, len(key)):
                try:
                    replace = str(params[int(key)])
                except IndexError:
                    raise ValueError("Index " + key + " of stack variables is out of range")
            # Otherwise, navigate the settings dict for the key
            else:
                keys = key.split('/')
                dic = self.settings
                for k in keys:
                    # Special key to list contents
                    if k == "LIST":
                        print("Contents:")
                        print(dic)
                    if isinstance(dic, dict) and (k in dic):
                        dic = dic[k]
                    elif isinstance(dic, list):
                        # Lists must be indexed with an integer
                        match = re.match("[0-9]+", k)
                        if match and match.span() == (0, len(k)):
                            dic = dic[int(k)]
                        else:
                            dic = "None"
                    else:
                        # Not found. Replace with "None"
                        dic = "None"
                if isinstance(dic, dict) or isinstance(dic, tuple):
                    # Dictionary type - print keys
                    # Tuple type - print values
                    replacement = ""
                    for k in dic:
                        replacement += str(k) + " "
                    replace = replacement[:-1]  # Trim trailing space
                elif isinstance(dic, list):
                    # List type - print indices
                    replacement = ""
                    for i in range(len(dic)):
                        replacement += str(i) + " "
                    replace = replacement[:-1]  # Trim trailing space
                else:
                    replace = str(dic)
            contents = contents[:start] + replace + contents[end+2:]
        return contents

    def makeFileSubstitutions(self, contents, cur_file, params):
        # Perform file substitutions
        while True:
            start = contents.find("%[")
            if start < 0:
                break
            end = self.findClosingBracket(contents, start)
            new_file = contents[start+2:end]
            if cur_file == new_file:
                ValueError("File cannot include itself: " + cur_file)
            replacement = self.buildFile(new_file, params)
            afterEnd = (end+3 if contents[end+2:end+3] == '\n' else end+2)
            contents = contents[:start] + replacement + contents[afterEnd:]
        return contents
