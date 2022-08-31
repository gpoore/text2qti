# Change Log


## v0.6.0 (dev)

* Added `amsmath`, `amssymb`, and `siunitx` to template for LaTeX solutions
  export.

* Fixed a bug with error handling when Pandoc fails to export solutions (#47).

* For question groups, the value of `pick` is now allowed to equal the total
  number of questions (#44).

* Added support for Pandoc-style attributes on images:
  `![alt_text](image_file){#id .class1 .class2 width=10em height=5em}` (#41).

* Executable code blocks now use PATH to locate executables under Windows, and
  thus now work with Python environments.  Previously PATH was ignored under
  Windows due to the implementation details of Python's `subprocess.Popen()`
  (#34, #42).

* Added command-line options `--solutions` and `--only-solutions` to
  command-line application.  These generate solutions in Pandoc Markdown,
  PDF, and HTML formats.  Pandoc Markdown solutions are only suitable for
  use with LaTeX and HTML (#35).

* Added quiz-level options `feedback is solution`, `solutions sample groups`,
  and `solutions randomize groups` for customizing solutions.  Added
  group-level option `solutions pick` for customizing solutions.  Added
  question-level syntax involving `!` for providing solutions.

* In quiz parsing, simplified question type handling and error checking.

* Fixed bug in calculation of total points possible per quiz.



## v0.5.0 (2020-09-28)

* Added `text2qti_tk` executable, which provides a basic graphical user
  interface (GUI) via `tkinter`.  Added build scripts in `make_gui_exe/` for
  creating a standalone GUI executable under Windows with PyInstaller (#27).
* In executable code blocks, `.python` now invokes `python3` on systems where
  `python` is equivalent to `python2` as well as on systems that lack a
  `python` executable.  The README now suggests using `.python3` and
  `.python2` to be more explicit (#22).
* Added a new keyword argument `executable` for executable code blocks, which
  allows a custom executable (including path) to be specified for running
  code.  Added support for periods in code block language attributes, so that
  things like `.python3.8` are now possible.
* Fixed bug caused by swapped identifiers in QTI XML (#18, #19).  Now quiz
  descriptions work with Canvas and question titles appear in Canvas in the
  quiz editor (but not in the student view).   The following options now work
  with Canvas:  `Shuffle answers`, `Show correct answers`,
  `One question at a time`, and `Can't go back`.
* Installation (`setup.py`) now requires `markdown` >= 3.2 to ensure
  compatibility and avoid Markdown parsing bugs fixed in 3.2 (#31).
* Fixed bug that produced incorrect QTI output paths when using quiz files
  outside the current working directory (#28, #29).
* README now covers more options for installing the development version (#20).



## v0.4.0 (2020-07-17)

* Improved preprocessing for siunitx notation, LaTeX math, and HTML comments.
  Fixed catastrophic backtracking in LaTeX math regex (#11).  Added support
  for newlines in HTML comments.  The preprocessor now skips backslash
  escapes, inline code containing newlines, and fenced code blocks (as long as
  they do not start on the same line as a list marker).  The preprocessor now
  handles the escape `\$` itself, since Python-Markdown ignores it (#14).
* Python-Markdown's Markdown-in-HTML extension is now enabled (#13).
* Added quiz options `Shuffle answers`, `Show correct answers`,
  `One question at a time`, and `Can't go back` (#10).  These options are
  apparently ignored by Canvas, but may work with some other systems.
* Revised README to clarify that some features are apparently not supported
  by Canvas (#16).



## v0.3.0 (2020-05-26)

* Added support for multiple-answers questions.
* Added support for short-answer (fill-in-the-blank) questions.
* Added support for file-upload questions.
* Added support for setting question titles and point values (#9).
* Added support for text regions outside questions.
* Added `--pandoc-mathml` command-line option.  This converts LaTeX to MathML
  via Pandoc, rather than using a Canvas LaTeX rendering URL (#4).
* Added support for comments at the top level of quiz files (outside Markdown
  content like questions, choices, or feedback).  HTML comments within
  Markdown are now stripped and no longer appear in the final QTI file (#2).
* For numerical questions, exact answers with allowed margin are now treated
  as exact answers, rather than being converted into ranges of values.  This
  primarily affects how feedback for incorrect answers is worded (#7).
* Essay questions now support general feedback.
* Fixed a bug that prevented incorrect question feedback from working.
* Relaxed indentation requirements for quiz titles spanning multiple lines.
  Indentation for wrapped lines must now be at least 2 spaces or 1 tab, rather
  than being equivalent to that of the first character in the title.
* Fixed a bug that allowed trailing whitespace to cause incorrect indentation
  calculations, resulting in indentation errors in valid quizzes.



## v0.2.0 (2020-04-23)

* Added support for images, using standard Markdown syntax.
* Added support for multi-paragraph descriptions, questions, choices, and
  feedback.
* Added support for essay questions.
* Added support for numerical questions.
* Added support for question groups.  A subset of the questions in a group is
  chosen at random when a quiz is taken.
* Added support for executable code blocks.  These can be used to generate
  questions automatically.  This feature requires the command-line flag
  `--run-code-blocks` or setting `run_code_blocks = true` in the config
  file.
* Quiz titles are now processed as plain text, rather than as Markdown,
  because QTI does not support HTML titles.
* Fixed a bug that prevented source file names from appearing in error
  messages.  Fixed misspelling of "imsmanifest.xml" in QTI output.



## v0.1.0 (2020-04-01)

* Initial release.
