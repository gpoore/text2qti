# Change Log


## v0.3.0 (2020-??-??)

* Added support for multiple-answers questions.
* Added `--pandoc-mathml` command-line option.  This converts LaTeX to MathML
  via Pandoc, rather than using a Canvas LaTeX rendering URL (#4).
* Added support for comments at the top level of quiz files (outside Markdown
  content like questions, choices, or feedback).  HTML comments within
  Markdown are now stripped and no longer appear in the final QTI file (#2).
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
