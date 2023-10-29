# text2qti – Create quizzes in QTI format from Markdown-based plain text

text2qti converts
[Markdown](https://daringfireball.net/projects/markdown/)-based plain text
files into quizzes in QTI format (version 1.2), which can be imported by
[Canvas](https://www.instructure.com/canvas/) and other educational software.
It supports multiple-choice, true/false, multiple-answers, numerical,
short-answer (fill-in-the-blank), essay, and file-upload questions.  It
includes basic support for LaTeX math within Markdown, and allows a limited
subset of [siunitx](https://ctan.org/pkg/siunitx) notation for units and for
numbers in scientific notation.



## Examples

text2qti allows quick and efficient quiz creation.  Example
**multiple-choice** plain-text quiz question that can be converted to QTI and
then imported by Canvas:

```
1.  What is 2+3?
a)  6
b)  1
*c) 5
```

A **question** is created by a line that starts with a number followed by a
period and one or more spaces or tabs ("`1. `").  Possible **choices** are
created by lines that start with a letter followed by a closing parenthesis
and one or more spaces or tabs ("`a) `").  Numbers and letters do not have to
be ordered or unique.  The **correct** choice is designated with an asterisk
("`*c) `").  All question and choice text is processed as
[Markdown](https://daringfireball.net/projects/markdown/).

There is also support for a quiz title and description, as well as question
titles, point values, and feedback.  Note that unlike most other text, titles
like quiz and question titles are treated as plain text, not Markdown, due to
the QTI format.  **Also note that Canvas correctly shows question titles
within its quiz editor for instructors, but always replaces them with titles
like "Question 1" in the student view.**  Question point values must be
positive integers or half-integers.

```
Quiz title: Addition
Quiz description: Checking addition.

Title: An addition question
Points: 2
1.  What is 2+3?
... General question feedback.
+   Feedback for correct answer.
-   Feedback for incorrect answer.
a)  6
... Feedback for this particular answer.
b)  1
... Feedback for this particular answer.
*c) 5
... Feedback for this particular answer.
```

**Multiple-answers questions** use `[]` or `[ ]` for incorrect answers and
`[*]` for correct answers.

```
1.  Which of the following are dinosaurs?
[ ] Woolly mammoth
[*] Tyrannosaurus rex
[*] Triceratops
[ ] Smilodon fatalis
```

**Numerical questions** use an equals sign followed by one or
more spaces or tabs followed by the numerical answer.  Acceptable answers can
be designated as a range of the form `[<min>, <max>]` or as a correct answer
with a specified acceptable margin of error `<ans> +- <margin>`.  When the
latter form is used, `<margin>` can be either a number or a percentage.
`<margin>` can be omitted when the answer is an integer and an exact answer is
required.  In this case, scientific notation is not permitted, but the
underscore can be used as a digit separator; for example, `1000` and `1_000`
are both valid, but `1e3` is not.  An exact answer can be required for
floating-point numbers, but this requires an explicit `+- 0`, since a range is
typically more appropriate for floating-point values.  Numerical questions
have the limitation that the absolute value of the smallest acceptable answer
must be greater than or equal to 0.0001 (1e-4).

```
1.  What is the square root of 2?
=   1.4142 +- 0.0001

2.  What is the cube root of 2?
=   [1.2598, 1.2600]

3.  What is 2+3?
=   5
```

**Short-answer (fill-in-the-blank) questions** use an asterisk followed by one
or more spaces or tabs followed by an answer.  Multiple acceptable answers can
be given.  Answers are restricted to a single line each and are treated as
plain text, not Markdown.
```
1.  Who lives at the North Pole?
*   Santa
*   Santa Claus
*   Father Christmas
*   Saint Nicholas
*   Saint Nick
```

**Essay questions** are indicated by a sequence of three or more underscores.
They only support general question feedback.

```
1.  Write an essay.
... General question feedback.
____
```

**File-upload questions** are indicated by a sequence of three or more
circumflex accents.  They only support general question feedback.
```
1.  Upload a file.
... General question feedback.
^^^^
```

**Text regions** outside of questions are supported.  Note that unlike most
other text, titles like text region titles are treated as plain text, not
Markdown, due to the QTI format.  Also note that Canvas apparently ignores the
text region title and only displays the text itself.  Text regions are not
required to have both a title and text; either may be used alone, but the
title must come first when both are present.
```
Text title:  Instructions about the next questions
Text:  General comments about the next questions.
```


## File format

The text2qti file format is a plain-text file format that serves as a wrapper
around Markdown.  Each individual chunk of text (question, answer, feedback,
etc.) is Markdown. But the outermost level of text (no indentation) is the
text2qti plain-text quiz format.  The fact that the Markdown is indented
within the text2qti format is only really visible when multiple lines of
Markdown are involved. The indentation for each chunk of Markdown text doesn't
have to be 4 spaces; it just has to be the same for the whole chunk of text
that makes up each element of a question.

```
**No indentation: text2qti wrapper syntax for Markdown**
|
|   **Indentation: Now using Markdown**
|   **Everything below this must have at least this indentation**
|   |
1.  Question.
|   |
|   Question continued, so indentation.
|   |
*a) Correct answer.
|   |
|   Correct answer continued, so indentation.
|   |
b)  Another answer.
|   |
```


## Installation

Install **Python 3.8+** if it is not already available on your machine.  See
https://www.python.org/, or use the package manager or app store for your
operating system.  Depending on your use case, you may want to consider a
Python distribution like [Anaconda](https://www.anaconda.com/distribution/)
instead.

Install
[setuptools](https://packaging.python.org/tutorials/installing-packages/)
for Python if it is not already installed.  This can be accomplished by
running
```
python -m pip install setuptools
```
on the command line.  Depending on your system, you may need to use `python3`
instead of `python`.  This will often be the case for Linux and OS X.

Install text2qti by running this on the command line:
```
python -m pip install text2qti
```
Depending on your system, you may need to use `python3` instead of `python`.
This will often be the case for Linux and OS X.


### Upgrading

```
python -m pip install text2qti --upgrade
```
Depending on your system, you may need to use `python3` instead of `python`.
This will often be the case for Linux and OS X.


### Installing the development version

If you want to install the development version to use the latest features,
download `text2qti` from [GitHub](https://github.com/gpoore/text2qti) and
extract the files.  A few different ways to install the development version
are listed below.  Depending on your system, you may need to use `python3`
instead of `python` in the commands below.  This will often be the case for
Linux and OS X.

* You can install using the included `setup.py` by running
  ```
  python setup.py install
  ```
  Depending on your system configuration, especially if you do not have root
  or administrator privileges, you may want to
  [customize the installation location](https://docs.python.org/3.8/install/#alternate-installation-the-user-scheme).
  For example, you can add `--user` to install under `%APPDATA%\Python` (Windows), `~/.local` (UNIX, and Mac OS X non-framework builds), or
  `~/Library/Python/<VERSION>` (Mac framework builds):
  ```
  python setup.py install --user
  ```
* You can install using `pip`.  For example, in the directory with `setup.py`,
  run this:
  ```
  python -m pip install .
  ```




## Usage

text2qti has been designed to create QTI files for use with
[Canvas](https://www.instructure.com/canvas/).  Some features may not be
supported by other educational software.  You should **always preview**
quizzes or assessments after converting them to QTI and importing them.

Write your quiz or assessment in a plain text file.  You can use a basic
editor like Notepad or gedit, or a code editor like
[VS Code](https://code.visualstudio.com/).  You can even use Microsoft Word,
as long as you save your file as plain text (*.txt).

text2qti includes a graphical application and a command-line application.

* To use the graphical application, open a command line and run `text2qti_tk`.

* To use the command-line application, open a command line in the same folder
  or directory as your quiz file.  Under Windows, you can hold the SHIFT
  button down on the keyboard, then right click next to your file, and select
  "Open PowerShell window here" or "Open command window here".  You can also
  launch "Command Prompt" or "PowerShell" through the Start menu, and then
  navigate to your file using `cd`.

  Run the `text2qti` application using a command like this:
  ```
  text2qti quiz.txt
  ```
  Replace "quiz.txt" with the name of your file.  This will create a file like
  `quiz.zip` (with "quiz" replaced by the name of your file) which is the
  converted quiz in QTI format.

Instructions for using the QTI file with Canvas:
  * Go to the course in which you want to use the quiz.
  * Go to Settings, click on "Import Course Content", select "QTI .zip file",
    choose your file, and click "Import".  Typically you should not need to
    select a question bank; that should be managed automatically.
  * While the quiz upload will often be very fast, there is an additional
    processing step that can take up to several minutes.  The status will
    probably appear under "Current Jobs" after upload.
  * Once the quiz import is marked as "Completed", the imported quiz should be
    available under Quizzes.  If the imported quiz does not appear after
    several minutes, there may be an error in your quiz file or a bug in
    `text2qti`.  When Canvas encounters an invalid quiz file, it tends to fail
    silently; instead of reporting an error in the quiz file, it just never
    creates a quiz based on the invalid file.
  * You should **always preview the quiz before use**.  text2qti can detect a
    number of potential issues, but not everything.

Typically, you should start your quizzes with a title, like this:
```
Quiz title: Title here
```
Otherwise, all quizzes will have the default title "Quiz", so it will be
difficult to tell them apart.  Another option is to rename quizzes after
importing them.  Note that unlike most other text, the title is treated as
plain text, not Markdown, due to the QTI format.

When you run `text2qti` for the first time, it will attempt to create a
configuration file called `.text2qti.bespon` in your home or user directory.
It will also ask for an institutional LaTeX rendering URL.  This is only
needed if you plan to use LaTeX math and if the default URL
`/equation_images/` will not work with your system.  In typical cases, you can
simply press ENTER to continue with the default value.
 * If you use Canvas, log into your account and look in the browser address
   bar.  You will typically see an address that starts with something like
   `institution.instructure.com/` or `canvas.institution.edu/`, with
   `institution` replaced by the name of your school or an abbreviation for
   it.  The LateX rendering URL that you want to use will then be something
   like `https://institution.instructure.com/equation_images/` or
   `https://canvas.institution.edu/equation_images/`, with `institution`
   replaced by the appropriate value for your school.  If the URL is like the
   second form, you may need to replace the `.edu` domain with the appropriate
   value for your institution.
 * If you use other educational software that handles LaTeX in a manner
   compatible with Canvas, consult the documentation for your software.  Or
   perhaps create a simple quiz within the software using its built-in tools,
   then export the quiz to QTI and look through the resulting output to find
   the URL.
 * If you are using educational software that does not handle LaTeX in a
   manner compatible with Canvas, try the `--pandoc-mathml` command-line
   option when creating QTI files (note that this requires that
   [Pandoc](https://pandoc.org/) be installed).  If that does not work, please
   open an issue requesting support for that software, and include as much
   information as possible about how that software processes LaTeX.



## Additional features

### Question groups

A question group contains multiple questions, and only a specified number of
these are randomly selected and used each time a quiz is taken.

```
GROUP
pick: 1
points per question: 1

1.  A question.
*a) true
b)  false

2.  Another question.
*a) true
b)  false

END_GROUP
```

The number of questions from the group that are used is specified with
"`pick:`".  If this is omitted, it defaults to `1`.  The points assigned per
question is specified with "`points per question:`".  If this is omitted, it
defaults to `1`.  All questions within a group must be worth the same number
of points.


### Executable code blocks

text2qti can execute the code in Markdown-style fenced code blocks.  Code can
be used to generate questions within a quiz.  Everything written to stdout by
the executed code is included in the quiz file; the code block is replaced by
stdout.

``````
```{.python .run}
import textwrap
for x in [2, 3]:
    print(textwrap.dedent(rf"""
        1.  What is ${x}\times 5$?
        *a) ${x*5}$
        b)  ${x+1}$
        """))
```
``````


For code to be executed, there are a few requirements:

* The code block fences (` ``` `) must not be indented; the code block must be
  at the top level of the document, not part of a question, choice, or
  feedback.  In contrast, a regular code block that is part of a question,
  choice, or feedback must be indented as part of that quiz element.

* As a security measure, code execution is disabled by default, so executable
  code blocks will trigger an error.  Run `text2qti` with the option
  `--run-code-blocks` to enable code execution, or set `run_code_blocks =
  true` in the text2qti config file in your user or home directory.

* The text immediately after the opening fence must have the form
  `{.lang .run}` or `{.lang .run executable=<executable>}`.  This is inspired
  by the code-block attributes in
  [Pandoc Markdown](https://pandoc.org/MANUAL.html).

  If the keyword argument `executable` is not provided, then `lang` must
  designate an executable that can run the code once the code has been saved
  to a file.  In the example above, `python` is extracted from the first line
  (` ```{.python .run}`),  code is saved in a temporary file, and then the
  file is executed via `python <file>`.

  If `executable` is used to specify an executable, then `lang` is ignored by
  `text2qti`, but it is still useful since some editors will use it to provide
  syntax highlighting.

  When `executable` is specified, the executable path must be quoted with
  double quotes `"` if it contains anything other than the tilde, Unicode word
  characters, numbers, forward slashes, periods, hyphens, and underscores.
  When the executable path is quoted, backslashes and quotation marks are
  still prohibited; forward slashes should be used under all operating systems
  including Windows.  A leading `~` in the executable path is expanded to the
  user's home directory under all operating systems including Windows.

* **Special Python note**:  When `.python` is used with an executable code
  block without specifying an `executable`, code will run with `python3` if
  either of these conditions is met:

    - `python3` exists on the system and `python` is equivalent to `python2`.

    - `python` does not exist on the system, but `python3` does exist.

  To avoid ambiguity, you may want to use `.python3` and `.python2` rather
  than `.python` when working with operating systems other than Windows, or
  when working with a Windows installation that includes a `python3`
  executable or symlink.  It is also possible to be even more specific by
  using something like `.python3.8`.

Each code block is executed in its own process, so data and variables are not
shared between code blocks.

If an executable code block generates multiple questions that are identical,
or multiple choices for a single question that are identical, this will be
detected by `text2qti` and an error will be reported.  Questions or choices
that may be equivalent, but are not represented by exactly the same text,
cannot be detected (for example, things like `100` versus `1e2`, or `answer`
versus `Answer`).


### Additional quiz options

There are additional quiz options that can be set immediately after the quiz
title and quiz description.  These all take values `true` or `false`.  For
example, `shuffle answers: true` could be on the line right after the quiz
description.

* `shuffle answers` — Shuffle answer order for questions.
* `show correct answers` — Show correct answers after submission.
* `one question at a time` — Only show one question at a time.
* `can't go back` — Don't allow going back to the previous question when in
  `one question at a time` mode.




## Details for writing quiz text

text2qti processes almost all text as
[Markdown](https://daringfireball.net/projects/markdown/), using
[Python-Markdown](https://python-markdown.github.io/).  (The only exceptions
are the quiz title, question titles, and text region titles, which are
processed as plain text due to the QTI format, plus the acceptable answers
for short-answer questions.)  For example, `*emphasized*` produces *emphasized*
text, which typically appears as italics.  Text can be styled using Markdown
notation, or with HTML.  Remember to preview quizzes after conversion to QTI,
especially when using any significant amount of HTML.

Python-Markdown provides several
[extensions to basic Markdown](https://python-markdown.github.io/extensions/).
Currently, the following extensions are enabled:
* `smarty`:  Automatic curly quotation marks and dashes.
* `sane_lists`:  List behavior is closer to what might be expected.
* `def_list`:  Definition lists of this form:
  ```
  term
  :   definition
* `fenced_code`:  Fenced code blocks (` ``` ` or `~~~`).
* `footnotes`:  Footnotes using this form:
  ```
  Normal text [^1].

  [^1]: Footnote text.
* `tables`:  Tables of this form:
  ```
  Header | Header
  ------ | ------
  Cell   | Cell
  Cell   | Cell
  ```
* `md_in_html`:  Text inside HTML tags is treated as Markdown.  This requires
  setting the attribute `markdown="1"` in the opening tag for block-level
  elements.  See the
  [documentation](https://python-markdown.github.io/extensions/md_in_html/)
  for more details about proper usage and potential issues.

While indented Markdown code blocks are supported, fenced code blocks should
be preferred.  Indented code can interfere with the preprocessor that strips
HTML comments and handles LaTeX math and siunitx notation.


### Titles

Quiz, question, and text region titles are limited to a single paragraph.  If
this paragraph is wrapped over multiple lines, all lines after the first must
be indented by at least two spaces or one tab, and share the same indentation.
All tabs are expanded to 4 spaces before indentation is compared, following
the typical Markdown approach.

All titles are treated as plain text, not Markdown, due to the QTI format.

Titles are always optional, but when they are used for a given element, they
are always required to be first, before any other attributes.


### Descriptions, questions, choices, feedback, and text regions

Descriptions, questions, choices, feedback, and text regions may span multiple
paragraphs and include arbitrary Markdown content like code blocks or
quotations.  Everything must be indented to at least the same level as the
start of the first paragraph on the initial line.  All tabs are expanded to 4
spaces before indentation is compared, following the typical Markdown
approach.  For example,
```
1.  A question paragraph that is long enough to wrap onto a second line.
    The second line must be indented to match up with the start of the
    paragraph text on the first line.

    Another paragraph.
```
Note that the acceptable answers for short-answer questions are treated as
plain text and limited to a single line, and numerical answers are also
processed specially and limited to a single line.


### Images

Images are included with the standard Markdown syntax:
```
![alt_text](image_file)
```
It will typically be easiest to put your image files in the same folder or
directory as the quiz file, so you can use something like `![alt](image.jpg)`.
However, file paths are supported, including `~` user expansion under all
operating systems.  All image paths not starting with `http://` or `https://`
are assumed to refer to local image files (files on your machine), and will
result in errors if these files are not found.

[Pandoc-style attributes](https://pandoc.org/MANUAL.html#images) can be used
with images:
```
![alt_text](image_file){#id .class1 .class2 width=10em height=5em}
```
This allows image id, classes, and dimensions to be specified without
resorting to HTML.


### LaTeX

By default, text2qti supports LaTeX using a Canvas LaTeX rendering URL that
defaults to `/equation_images/`.  This can be customized during installation,
or by editing the configuration file `.text2qti.bespon` in your home or user
directory.  It is possible to convert LaTeX to MathML instead with the
`--pandoc-mathml` command-line option.  This requires that
[Pandoc](https://pandoc.org/) be installed for converting LaTeX to MathML.
For example, to create a quiz you might run a command like this:
```
text2qti --pandoc-mathml quiz.txt
```
When `--pandoc-mathml` is used, a cache file `_text2qti_cache.zip` will be
created in the quiz file directory.  This is used to store Pandoc MathML
output to increase performance for long quizzes with lots of math.

text2qti supports inline LaTeX math within dollar signs `$`.  There must be a
non-space character immediately after the opening `$` and immediately before
the closing `$`.  For example, `$F = ma$`.  LaTeX math is limited to what is
supported by Canvas or whatever other educational software you are using.  It
is usually a good idea to preview imported quizzes before assigning them,
because text2qti cannot detect LaTeX incompatibilities or limitations.  There
is currently not support for block LaTeX math; only inline math is supported.

When using Canvas with LaTeX math, be aware that in some cases Canvas's
vertical alignment of math leaves much to be desired.  Sometimes this can be
improved by including `\vphantom{fg}` or `\strut` at the beginning of an
equation.  An alternative is simply to use LaTeX for all question or choice
text (via `\text`, etc.).

text2tqi supports a limited subset of LaTeX
[siunitx](https://ctan.org/pkg/siunitx) notation.  You can use notation like
`\num{1.23e5}` to enter numbers in scientific notation.  This would result in
`1.23×10⁵`.  You can use notation like `\si{m/s}` or `\si{N.m}` to enter
units.  These would result in `m/s` and `N·m`.  Unit macros currently are not
supported, with these exceptions: `\degree`, `\celsius`, `\fahrenheit`,
`\ohm`, `\micro`.  Finally, numbers and units can be combined with notation
like `\SI{1.23e5}{m/s}`.  All of these can be used inside or outside LaTeX
math.

Technical note: LaTeX and siunitx support are currently implemented as
preprocessors that are used separately from Python-Markdown.  In rare cases,
this may lead to conflicts with Markdown syntax.  These features may be
reimplemented as Python-Markdown extensions in the future.


### Comments

There are multiple ways to add comments within a quiz file.  In all cases,
comments are completely removed during quiz creation and do not appear in the
final quiz in any form.

At the top level of a quiz document (outside of questions, choices, or
feedback) there are two types of comments.  These comments cannot be indented.
* Line comments:  Any line that starts with a percent sign `%` is discarded.
* Multiline comments:  If a line starts with `COMMENT`, that line and all
  subsequent lines are discarded through a line that starts with
  `END_COMMENT`.  The `COMMENT` and `END_COMMENT` delimiters must be on lines
  by themselves; otherwise, an error is raised.

Within Markdown text, standard HTML comments of the form `<!--comment-->` may
be used.  These are stripped out during processing and do not appear in the
final QTI file.  HTML comments are not supported within LaTeX math.

Technical note:  HTML comments are currently stripped in a preprocessing step
separate from Python-Markdown.  In rare cases, this may conflict with raw HTML
embedded in Markdown.  This feature may be reimplemented as a Python-Markdown
extension in the future.



## Export solutions to PDF and HTML

There is basic support for exporting quiz solutions in Pandoc Markdown, PDF,
and HTML formats.  This is currently only available in the command-line
application.  Solutions exported as Pandoc Markdown are only suitable for use
with LaTeX and HTML.  Exporting solutions as PDF requires
[Pandoc](https://pandoc.org/) and a LaTeX installation (such as [TeX
Live](https://www.tug.org/texlive/) or [MiKTeX](https://miktex.org/)).  There
is currently no built-in support for customizing export, although you can edit
the Pandoc Markdown output before processing it via Pandoc.

To save solutions and also create a QTI file, use
`--solutions <solutions_file>`.  To save solutions without creating a QTI
file, use `--only-solutions <solutions_file>`.  `<solutions_file>` must have
an `.md` or `.markdown` extension for Pandoc Markdown export, `.pdf` for PDF
export, or `.html` for HTML export.  `--solutions` and `--only-solutions` can
be used multiple times to generate solutions in multiple formats.

When using `--only-solutions`, be aware that solutions and QTI may differ if
executable code blocks generate problems using random numbers. Consider
creating solutions and QTI at the same time (`--solutions`), or setting a seed
for the random number generator so it is reproducible.


### Customizing questions for solutions

Each question can provide a solution or other important information that is
*only* included in the solutions, *never* in the QTI.  This is particularly
useful for essay and upload questions, since they are defined without
specifying an answer and require manual grading.  For example,
```
1.  Write an essay about text2qti.

!   This is important information about what the essay should cover.

    This will only appear in the solutions, and can be as long or short as
    you wish.

____
```
The syntax for a question solution is the same as that for question feedback,
except that an exclamation point `!` is used instead of `...` or `+` or `-`.


### Quiz options

At the beginning of a quiz, there are some quiz-level options that can be set
to customize solutions.  These all take `true`/`false` values, and are `false`
by default.  For example, add `solutions sample groups: true` at the beginning
of a quiz.

* `feedback is solution` — This disables the special question solution syntax
  involving `!`, and treats general question feedback (`...`) as both feedback
  and solution.  This is useful when you want to give students solution
  information as part of the QTI feedback and also include this same
  information in solutions.

* `solutions sample groups` — By default, *all* questions in a question group
  are included in solutions, with a notice about the number that are randomly
  selected when the quiz is taken, unless the question group has `solutions
  pick` set to use a different value.

  This option causes only a sample of the questions in a group to be included
  in the solutions.  This option displays the first N questions in a group
  sequentially, where N is the group `solutions pick` value if it has been
  set, and otherwise the `pick` value if it has been set, and otherwise 1.  It
  is possible for solutions to include N random questions from a group instead
  of the first N questions; see `solutions randomize groups`.

* `solutions randomize groups` — For each question group, randomize the order
  in which questions are displayed in solutions.  If only some questions from
  a group are included in solutions (`solutions sample groups` is `true` or
  `solutions pick` is set), also randomize which questions are displayed
  instead of taking all displayed questions sequentially from the beginning of
  the group.

  Randomization is not used by default for two reasons that relate to quizzes
  using `solutions pick` or `solutions sample groups`.  First, including group
  questions sequentially allows specially chosen, representative questions to
  be placed at the beginning of the group so that they will appear in
  solutions.  If a group contains many questions that are generated by an
  executable code block, a random selection might not provide a sample that is
  representative.  Second, if a quiz is used several semesters or years in a
  row with only minor modifications, and new randomized solutions are
  distributed each time, this means that eventually all questions would be
  distributed in solutions, rather than only a fixed subset.


### Customizing groups for solutions

When a quiz is taken, the number of questions randomly selected from a
question group is the value of `pick` if `pick` is set for the group and
otherwise 1.  However, by default solutions will include *all* questions from
a group.  There are two ways to modify this.

It is possible to modify the number of questions displayed in solutions for a
specific group by setting `solutions pick` for the group.  This causes only
the specified number of questions from the group to be displayed in solutions.
The questions that are displayed are taken sequentially from the beginning of
the group by default, with no randomization.  For randomization, see the
quiz-level option `solutions randomize groups`.

It is also possible to modify the number of questions displayed in solutions
for *all* groups in a quiz by setting the quiz-level option `solutions sample
groups` to `true`.  This option displays the first N questions in a group
sequentially, where N is the group `solutions pick` value if it has been set,
and otherwise the `pick` value if it has been set, and otherwise 1.  It is
possible for solutions to include N random questions from a group instead of
the first N questions; see `solutions randomize groups`.

In the example below, the solutions would include 2 questions from the group,
even though only 1 is displayed when the quiz is taken.  The first 2 questions
would be included in solutions, unless `solutions randomize groups: true` is
included at the beginning of the quiz.

```
GROUP
pick: 1
solutions pick: 2

1.  A question.
*a) true
b)  false

2.  Another question.
*a) true
b)  false

3.  Yet another question.
*a) true
b)  false

END_GROUP
```

