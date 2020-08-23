# Change Log


## v0.5.0 (dev)

* Fixed bug caused by swapped identifiers in QTI XML (#18, #19).  Now quiz
  descriptions work with Canvas and question titles appear in Canvas in the
  quiz editor (but not in the student view).   The following options now work
  with Canvas:  `Shuffle answers`, `Show correct answers`,
  `One question at a time`, and `Can't go back`.



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
