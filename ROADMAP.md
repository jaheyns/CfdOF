# CfdOF Development Roadmap

This is a (non-exhaustive) list of tasks which are planned or needed. If you would like to make a contribution,
please consider tackling one of these items.

## General

* Finish translation support
  * See the guide here: <https://wiki.freecad.org/Translating_an_external_workbench>
  * Forum topic: <https://forum.freecad.org/viewtopic.php?f=10&t=36413>
* Logging - some of the more technical/diagnostic output that is printed to the report view
could instead be directed to the log, so that the report view is cleaner and more readable
for the user. Generally improve the logging and messages that are printed there.
(see FreeCAD.Console.PrintLog/PrintMessage/PrintWarning/PrintError.)
* Test and provide more elegant errors or fallbacks for invalid/unexpected/unusual sequences of actions
  
## Analysis object

Add a task panel and allow editing case path

## Solver

* Add a mechanism to specify surface tension coefficients between each pair of fluids
  (with future extensibility to other pairwise interfacial properties).
* Improve organisation of source code
* Expose parallel run option in GUI

## Property page

* Split into sub-pages

## Documentation

* Formal documentation should be completed on the FreeCAD Wiki.

## Testing

* Add additional, small 'demo' cases, which are specified as macros and run during the testing runs,
  to cover all functionality
* Additional unit tests which also test the functionality of the task panels, are needed. Currently testing is only
  done based on macros. Somehow, interaction with the GUI itself needs to be simulated.
