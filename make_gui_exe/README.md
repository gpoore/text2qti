# Create Standalone GUI Executable for Windows

This directory contains scripts for creating a standalone GUI executable under
Windows with PyInstaller.



## Requirements

* Windows
* [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)



## Directions

If you do not already have a local copy of the text2qti source, download
`make_tk_exe.bat` and `text2qti_tk.pyw`, and place them in the same directory.
Double-click on `make_tk_exe.bat` to run it.  Or open a command prompt,
navigate to `make_gui_exe/` (or wherever the batch file is located), and run
the batch file.  Under PowerShell, run something like
`cmd /c make_gui_exe.bat`.

The batch file performs these steps:
* Create a new conda environment for building the executable.
* Activate the conda environment.
* Install needed Python packages in the environment:  bespon, markdown,
  pyinstaller, and text2qti.  If the batch file detects that it is part of a
  local copy of the text2qti source, then this local version of text2qti will
  be used.  Otherwise, text2qti will be installed from PyPI via pip.
* Build executable `text2qti_tk_VERSION.exe` using PyInstaller.
* Deactivate the conda environment.
* Remove the conda environment.
* Move the executable to the working directory.
* Remove all temp files and build files.
