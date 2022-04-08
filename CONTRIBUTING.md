# CfdOF: A Computational fluid dynamics (CFD) workbench for FreeCAD

The workbench serves as a front-end (GUI) for the popular OpenFOAM® CFD toolkit (www.openfoam.org, www.openfoam.com).

Disclaimer:
This offering is not approved or endorsed by OpenCFD Limited, producer and distributor of the OpenFOAM software via www.openfoam.com, and owner of the OPENFOAM® and OpenCFD® trade marks

## Contributing
![screenshot](website\resources\drone.png)

We welcome contributions to CfdOF from all sources: users (bug reports and feature suggestions / improvements) and developers (bug fixes, merge requests). 

In order to make contributions cohesive with the existing code, as well as admin of the project manageable, when contributing please follow the following contribution guidelines. We have also included some suggestions to make contributing easier if you are considering contributing code, such as dev environment setup etc. 

## Ethos
As indicated, the core developers welcome contributions to CfdOF and we want to build a great tool. However, please note the overarching ethos of CfdOF is to build simplified access to the OpenFOAM® CFD library. 

Therefore, our aim is to include as many useful features as possible, without introducing too many fiddle-factors or tweak parameters to the GUI. In short, CfdOF should make OpenFOAM®  accessible to entry level users, while advanced users can still access the core OpenFOAM configuration files via the "Edit" functionality included wherever needed. 

This does not mean that advanced features will not be included - however, some thought and potentially discussion should be applied to your contributions to ensure we continue to build an easy to use tool. 

## Recommended Tools
### IDE's and GUI editors

These are simply some suggestions which might help you set up a easy-to-use development environment. 

We suggest you use **Qt Designer** and not **Qt Creator** - this is a cut down version of Qt Creator, which is the full Qt IDE intended primarily for C++ development. Qt Designer on the other hand is a lightweight GUI design tool, which will write the required XML only which can then be integrated with the Python PySide (PyQT) library used by FreeCAD
* Please ensure that your indent spacing for your GUI template (XML) editing software is set to **x4 spaces** and not \tab or other indenting, to be consistent with the indenting used in the Python src files
* Please note that in some places in the CfdOF GUI, we use a custom input field, GUI::InputField which will need to be included in your set up as a custom widget. 
* You should be able to get a prebuilt version of [Qt Designer here](https://build-system.fman.io/qt-designer-download) for Mac and Windows otherwise you can also download a copy using PIP (Package name: pyqt5-tools)

Choice of Python IDE's is whatever you feel most comfortable with, although we have found **VS Code** and **PyCharm** quick and easy to set up. 
* Whatever IDE you use, the most important consideration is to ensure that your Python interpreter includes the FreeCAD **bin** and **lib** paths so that you will have access to the bundled Python libs distributed (and required) by FreeCAD workbenches
* Please note that at this stage, 3rd party code (ie libraries) which can be used by FreeCAD workbenches, are restricted to those distributed with the main FreeCAD installation itself - we cannot at this stage include additional Python libraries with Workbenches. 

## Source code contributions
[![Total alerts](https://img.shields.io/lgtm/alerts/g/jaheyns/CfdOF.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/jaheyns/CfdOF/alerts/)[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/jaheyns/CfdOF.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/jaheyns/CfdOF/context:python)

It is asked that developers should only add functionality or code that is working and can be tested. Dead code, even
portions included for possible future functionality, reduces function clarity and increases the maintenance overhead. 
Our philosophy is 'Do the basics well' and therefore robust operation takes precedence over extended functionality.

### Source code management

We have found the easist way to develop for CfdOF is to work directly in the FreeCAD module installation directory for CfdOF as the FreeCAD AddOn Manager simply clones the latest commits from the main Workbench repo to this directory. Therefore, you should be able to access Git and switch branches as required directly from this directory. 

* In terms of managing your own repo, for occaisional developers, we suggest cloning the CfdOF repo, and issuing Pull Requests to the main CfdOF repo with your bug fix and / or new feature. 
    - When developing, please use the **Gitflow** approach - we welcome _feature/new-feature-branch_ or _bugfix/my-bug-fix_ PR's into **develop** only, as the **master** branch is mirrored and pulled immediately into the FreeCAD Workbench distribution system, so any code added to master will effectively go live as soon as it is committed. 
    -  Hotfixes to released versions (ie **master**, _hotfix/my-hotfix_) will be accepted but only if determined to be essential by the core developers, otherwise it may be requested that your fix be included in the **develop** trunk and released with the next pull to master. 
* Regular contributors may be granted _developer_ access to the repo, in which case contributions can be pushed directly to the main CfdOF repository
    - Developer access is still restricted to the _develop_ and your own _feature_ / _bugfix_ branches. 

### Style guide

For consistency please follow [PEP8](https://www.python.org/dev/peps/pep-0008/)
1. Use 4 spaces per indentation level (spaces are preferred over tabs).
2. Limit all lines to a maximum of 120 characters.
3. Break lines before binary operators.
4. Blank lines 
    
    - Surround top-level function and class definitions with two lines.
    - Definitions inside a class are surrounded by a single line.
    
5. Imports should usually be on separate lines.
6. Comments
    - Docstrings always use """ triple double-quotes """
    - Block comment starts with a # and a single space and are indented to the same level as that code
    - Use inline comments sparingly. They are on the same line as a statement and should be separated by at least two
 spaces from the statement. 

7. Avoid trailing whitespaces
8. Naming convention

    - ClassNames (Camel)
    - variable_names_without_capitals (Underscore)
    - CONSTANTS_USE_CAPITALS (Uppercase)
    - functionsWithCapitals (Although not following PEP8, Camel-case instead of underscore is preferred as it is widely used within FreeCAD)
    - __class_attribute (Double leading underscore)
9. Python allows both single quotes ('...') and double quotes ("...") for strings. As a convention, please use single quotes for internal string constants and double quotes for 
   user-facing communication. The rule of thumb is that if it should be translated, use double quotes.
   This is not a hard-and-fast rule and can be broken for convenience e.g. when quotes are contained in a string.
   
### Testing

Unit and regression testing is supported. Where possible, it is asked that new functionality be included
in the unit test framework.

In order to run the tests, the following command can be used from the terminal:
```
FreeCAD -t TestCfdOF
```
Alternatively, from FreeCAD, select the 'Testing framework' workbench, choose the 'Self-test' button,
select the 'TestCfdOF' test name and click 'Start'. Remember to switch to your development / feature branch before testing.

In order to make sure that tests have been run before you issue your PR's, please include in your PR description a comment to show you have run the FreeCAD CfdOF unit tests above and that they have passed. 

## Documentation
At present, there is not much documentation available for CfdOF users. As such, for those contributors who would prefer to help in non-code based ways, we would welcome contributions in terms of video and or written user guides or tutorials. 

_Last updated 07/04/2022_