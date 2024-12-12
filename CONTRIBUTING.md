# CfdOF Contribution Guidelines

We welcome contributions to CfdOF. In order to make contributions cohesive with the existing code, as well as
administration of the project manageable, when contributing please follow the following contribution guidelines. We
have also included some suggestions to make contributing easier, such as development environment setup etc.

## Ethos

Please note the overarching goal of CfdOF is to build simplified and steamlined access to the OpenFOAM® CFD library,
as opposed to simply exposing every available function in a GUI environment. So, although contributions are welcomed,
we favour usability improvements over rapid expansion of the feature set.

This does not mean that advanced features will not be included - however, some thought and potentially discussion
should be applied to your contributions to ensure that ease of use is not compromised, and they may only be accepted
once they have been well honed.

## Source code contributions

It is asked that developers only add functionality or code that is working and can be tested. Dead code, even
portions included for possible future functionality, reduces function clarity and increases the maintenance overhead.
Our philosophy is 'Do the basics well' and therefore robust operation takes precedence over extended functionality.

### Source code management

The easiest way to develop for CfdOF is to work directly in the FreeCAD module installation directory for CfdOF
(`$HOME/.FreeCAD/Mod/CfdOF` or `$HOME/.local/share/FreeCAD/Mod/CfdOF` on Linux and `%APPDATA%\FreeCAD\Mod\CfdOF` on
Windows) as the workbench will be loaded from this location. After installing the workbench via the
Addon Manager, you should be able to use Git for source code management directly from this directory.
A symlink can be used in Linux if you wish to work in a more convenient location.

To contribute code, we suggest forking the CfdOF repository via the Github GUI, and issuing a Merge Request with your
bug fix and/or new feature. The repository workflow we use is based on the [Github-flow] philosophy.
Essentially, we ask all developers to submit merge requests for self-contained, tested and working features.
Although the process can be frustrating at times, the long-term health of the project depends on being strict on the
quality and completeness of code coming in, as well as harmonising it with the existing design philosophy. Please
remember that all developers are volunteers with their own interests, and allowing code that is not entirely fit for
purpose would place an unfair obligation on others to bring it up to scratch.

That said, there is generally no objection to submission of an _incomplete_ feature in order to expand on it later,
as long as it is functional, tested and of good quality as it stands, even if its capabilities are limited.

If you wish to get a first impression or some guidance on a feature you are developing, please feel free to submit a
'Draft' merge request which can be updated later. Alternatively, open an issue for a proposed change to initiate a
discussion.

### Version numbering

The version number loosely follows [Semantic versioning](https://semver.org) approach in the form MAJOR.MINOR.PATCH.
The major version number is incremented when there is a change which breaks backward compatibility with the file format
(`FCStd` files). This is avoided wherever possible, and phased conversion periods where an old format is accepted and the
new format written out, are preferred. The minor version number is incremented when there is a new feature in a release,
or a significant enhancement to existing functionality. The patch version is updated when a release contains only
a minor bug fix or fixes. Please increment the version number in ```package.xml``` when
submitting a merge request.

### Style guide

For consistency please follow [PEP8](https://www.python.org/dev/peps/pep-0008/)

1. Use 4 spaces per indentation level (spaces are preferred over tabs).
   - An exception is the `.ui` files describing the GUI templates. For convenience these are indented with 1 space in order
     to follow the behaviour of the QtDesigner software (see below).
   - OpenFOAM template files in the 'Templates' directories should be indented with 4 spaces, and not tabs.
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
    - `ClassNames` (Camel)
    - `variable_names_without_capitals` (Underscore)
    - `CONSTANTS_USE_CAPITALS` (Uppercase)
    - `functionsWithCapitals` (Although not following PEP8, Camel-case instead of underscore is preferred as it is widely
      used within FreeCAD)
    - `__class_attribute` (Double leading underscore)
9. Python allows both single quotes ('...') and double quotes ("...") for strings. As a convention, please use single
   quotes for internal string constants and double quotes for user-facing communication. The rule of thumb is that
   if a string should be translated, use double quotes. However, this is not a hard-and-fast rule and can be broken
   for convenience e.g. when quotes are contained in a string.

In the root of the repository we have included a `.ruff.toml` file which contains some settings for [ruff] linter
and formatter tool, this configuration file is used when:

- your editor uses ruff to format code
- your pre-commit hooks use ruff formatter
- your CI/CD pipeline uses an action to enforce formatting

#### Setting up pre-commit hooks

To ensure code quality and maintain consistency across the project, we use pre-commit hooks with
`ruff` as the linter and formatter. These hooks automatically check and format your code before you
commit changes, saving time and avoiding manual errors.

1. **Install `pre-commit`**: pre-commit is a Python-based tool, so ensure you have Python installed.
   Then, install pre-commit globally or within a virtual environment:

   ```bash
   sudo apt install pre-commit # On Debian/Ubuntu-based systems
   sudo dnf install pre-commit # On Fedora-based systems
   sudo pacman -S pre-commit # On Arch Linux-based systems
   ```

2. **Set up `pre-commit` hooks**: pre-commit takes care of installing the hooks dependencies, it usually uses
   the `$HOME/.cache/pre-commit` directory to clone the needed repositories. In the project directory,
   run the following command to install the pre-commit hooks, this will set up the hooks to run automatically
   before each commit:

   ```bash
   pre-commit install
   ```

3. **Run hooks manually (optional)**: You can test the hooks on all files at any time by running:

   ```bash
   pre-commit run --all-files
   ```

4. **Skip hooks**: If you want to force a commit despite a failing hook you can use:

   ```bash
   git commit --no-verify -m "WIP: My commit message"
   ```

5. **Updating hooks**: To update the pre-commit hooks to their latest versions use:

   ```bash
   pre-commit autoupdate
   ```

### Testing

Unit and regression testing is supported. Where possible, it is asked that new functionality be included
in the unit test framework.

In order to run the tests, the following command can be used from the terminal:

```bash
FreeCAD -t TestCfdOF
```

Alternatively, from FreeCAD, select the 'Testing framework' workbench, choose the 'Self-test' button,
select the 'TestCfdOF' test name and click 'Start'.

## Documentation

At present, there is not much documentation available for CfdOF users. As such, for those contributors who would prefer
to help in non-code based ways, we would welcome contributions in terms of video and/or written user guides or
tutorials.

## Roadmap

For a list of suggested tasks that need attention, please see the [Roadmap](ROADMAP.md).

## Recommended Tools

### IDE's and GUI editors

These are simply some suggestions which might help you set up an easy-to-use development environment.

We suggest you use **Qt Designer** and not **Qt Creator** - this is a cut down version of Qt Creator, which is the full
Qt IDE intended primarily for C++ development. Qt Designer on the other hand is a lightweight GUI design tool, which
will write the required XML only which can then be integrated with the Python PySide (PyQT) library used by FreeCAD

- Please ensure that your indent spacing for your GUI template (XML) editing software is set to **x1 spaces** and not
  \tab or other indenting, to be consistent with the indenting produced by Qt designer.
- Please note that in some places in the CfdOF GUI, we use a custom input field, GUI::InputField which will need to be
  included in your set up as a [custom widget].
- You should be able to get a pre-built version of [Qt Designer here](https://build-system.fman.io/qt-designer-download)
  for Mac and Windows otherwise you can also download a copy using PIP (Package name: pyqt5-tools)

We have found **VS Code** and **PyCharm** quick and easy to set up as Python IDEs.

- Whatever IDE you use, the most important consideration is to ensure that your Python interpreter includes the FreeCAD
  **bin** and **lib** paths so that you will have access to the bundled Python libraries distributed (and required) by
  FreeCAD workbenches
- Please note that at this stage, 3rd party code (i.e. libraries) which can be used by FreeCAD workbenches, are
  restricted to those distributed with the main FreeCAD installation itself - we cannot at this stage include additional
  Python libraries with Workbenches.

Another proven alternative is to use **Neovim** with the **[LazyVim]** setup along the [Python extra] configuration which
already uses ruff to format the Python files.

[Github-flow]: <https://docs.github.com/en/get-started/using-github/github-flow>
[ruff]: <https://docs.astral.sh/ruff>
[custom widget]: <https://wiki.freecad.org/Compile_on_Linux#Qt_designer_plugin>
[LazyVim]: <https://www.lazyvim.org>
[Python extra]: <https://www.lazyvim.org/extras/lang/python>
