# Change Log

## v0.2.0 (2020-??-??)

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
