This directory contains a generic OpenFOAM case template 
from which the case is built. The case builder cycles through the
files and directories recursively, but ignoring
any files beginning with '_'.

The case builder replaces special markup in these
files. All markup relevant to the case builder is prefixed 
with '%'. Other content is included verbatim and
does not need to be escaped/quoted.

Replacements are made based on the following rules:

1. File inclusion
   
   Files can be included with:
   
        %[filename%]
   
   where filename is a path relative to 
   the 'defaults' folder.
   - As a convenience to ignore nonexistant variables (see below),
   if filename ends with `_None`, nothing will be included
   - As a convenient catch-all, if `filename` is not found,
   the same file name with the text after the last underscore
   (if any) replaced with `default` is tried. 

2. Dictionary substitutions
 
    A python dictionary, which may contain sub-dictionaries and 
    sub-lists is used by the case builder to substitute values 
    into the case files. This is achieved with:
    
        %(key/and/optional/subkeys%)
    
    where the bracketed value is replaced with the string
    representation of the variable, and slashes allow nested
    sub-dictionaries to be referenced.
    - If the key is itself a dictionary, it evaluates
    to a space-separated sequence of the dictionary's keys.
    - If the key is a list, it evaluates to a space-separated
    sequence of the list indices, `0 1 2 ...`.
    - If the key is a tuple, it evaluates to a space-separated
    sequence of the tuple's values.
    - Any variable not found in the dictionary will be replaced 
    with `None`

3. Parameter stack

    A list of parameters (strings) is 
    maintained as a stack,
    and these are referenced as 
    
        %(N%)
    
    where N is a number
    with 0 representing the top of the stack, 1 the previous top
    of stack, etc.

4. Blocks
   
   The markup

        %{value
        block of
        text
        %} [output-file]

    pushes the word 'value' onto the stack for the duration of
    'block of text' and removes it at the end.
    - If 'value' is a space-separated sequence of multiple 
    words, 'block of text' is included repeatedly, once with 
    each item at the top of the stack.
    - If an optional file name `output-file` is given, the contents
    of the bracketed block are written to that file instead of the
    current parent file. The `output-file` parameter is evaluated
    with `value` at the top of the stack, the same as the contents
    of the block.

5. Switch statement

        %:word1 word2 ...
    
    (ended with a new line) causes the current value at
    the top of the parameter stack [i.e., '%(0%)'] to be compared 
    against 'word1', 'word2', etc, and only if it matches any of 
    them, it is removed from the stack and the following block of 
    text is included up until the next 
    '%:' or the end of the current block ('%}'). 
    If a match was found, no further text in 
    subsequent '%:' clauses in the current block (until 
    the next '%}') is included.
    - The special clause 

            %:default 

        matches anything and can be
        used at the end as an 'else' block.

General notes:

* Anything can be embedded in anything else.
* If a file ends up empty, it is not created.
