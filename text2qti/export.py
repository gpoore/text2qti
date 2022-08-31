# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import random
import re
import textwrap

from .quiz import Quiz, Question, GroupStart, GroupEnd, TextRegion
from .markdown import Markdown


markdown = Markdown()


# https://daringfireball.net/projects/markdown/syntax
_md_escape_chars_re = re.compile(r'[\\`*_{}\[\]()#+\-.!]')

def _md_escape_chars_repl_func(match: re.Match) -> str:
    return '\\' + match.group()

def md_escape(raw_text: str) -> str:
    '''
    Escape raw text so that it is suitable for inclusion in Markdown.
    '''
    return _md_escape_chars_re.sub(_md_escape_chars_repl_func, raw_text)


def indent(text: str, n_spaces: int, first_line: bool=True):
    '''
    Indent a string by a specified number of spaces, optionally leaving the
    first line unchanged.
    '''
    if n_spaces < 0:
        raise ValueError
    if n_spaces == 0 or not text:
        return text
    indent_spaces = ' '*n_spaces
    indented_text = text.replace('\n', '\n' + indent_spaces)
    indented_text = indented_text.replace('\n' + indent_spaces + '\n', '\n\n')
    if text[-1] == '\n':
        indented_text = indented_text.rstrip(' ')
    if first_line and text[0] != '\n':
        indented_text = indent_spaces + indented_text
    return indented_text


_latex_templates = {
    'header': textwrap.dedent(
        r'''
        %%%% Begin text2qti custom preamble
        % Page layout
        \usepackage[margin=1in]{geometry}
        % Graphics
        \usepackage{graphicx}
        % Math/science
        \usepackage{amsmath, amssymb}
        \usepackage{siunitx}
        % Symbols for solutions
        \usepackage{fontawesome}
        % Answers and solutions use itemize with custom item symbols
        \def\texttoqtimctfchoicesymb{%
            \resizebox{2ex}{!}{\faCircleO}}
        \def\texttoqtimctfcorrectchoicesymb{%
            \resizebox{2ex}{!}{\faDotCircleO}}
        \def\texttoqtimultanschoicesymb{%
            \resizebox{2ex}{!}{\faSquareO}}
        \def\texttoqtimultanscorrectchoicesymb{%
            \resizebox{2ex}{!}{\faCheckSquare}}
        \def\texttoqtigeneralcorrectanssymb{%
            \resizebox{2ex}{!}{\faArrowRight}}
        \def\texttoqtisolutionsymb{%
            \resizebox{2ex}{!}{\faFileTextO}}
        \def\texttoqtishortansbox{%
            \framebox[0.25\linewidth]{\strut}}
        \def\texttoqtiessayansbox{%
            \framebox{\begin{minipage}\vspace{4\baselineskip}\end{minipage}}}
        %%%% End text2qti custom preamble
        '''[1:]
    ),
    'mctf_choice_start': r'\item[\texttoqtimctfchoicesymb]',
    'mctf_choice_end': r'',
    'mctf_correct_choice_start': r'\item[\texttoqtimctfcorrectchoicesymb]',
    'mctf_correct_choice_end': r'',
    'multans_choice_start': r'\item[\texttoqtimultanschoicesymb]',
    'multans_choice_end': r'',
    'multans_correct_choice_start': r'\item[\texttoqtimultanscorrectchoicesymb]',
    'multans_correct_choice_end': r'',
    'generic_correct_choice_start': r'\item[\texttoqtigeneralcorrectanssymb]',
    'generic_correct_choice_end': r'',
    'choices_start': r'\begin{itemize}',
    'choices_end': r'\end{itemize}',
    'solution_start': r'\begin{itemize}' +'\n' + r'\item[\texttoqtisolutionsymb]',
    'solution_end': r'\end{itemize}',
    'shortans_placeholder': r'\texttoqtishortansbox',
    'essay_placeholder': r'\texttoqtiessayansbox',
    'file_upload_placeholder': r'\framebox{\texttt{<file upload>}}',
    'random_questions_start': r'\begingroup\renewcommand{\labelitemi}{[?]}',
    'random_questions_end': r'\endgroup',
}

_html_templates = {
    'header': textwrap.dedent(
        '''
        <style type="text/css">
        html {
            line-height: 1.2;
        }
        div.text2qti-randomized > ul {
            list-style-position: outside;
            margin-left: -0.5em;
        }
        div.text2qti-randomized > ul > li {
            list-style-type: "[?]";
            padding-left: 0.5em;
        }
        ul.text2qti {
            list-style-position: outside;
            /* margin-left: -0.5em; */
        }
        ul > li.text2qti-mctf-choice::marker, ul > li.text2qti-mctf-correct-choice::marker {
            font-size: 1.5em;
        }
        ul > li.text2qti-mctf-choice, ul > li.text2qti-mctf-correct-choice {
            margin-top: -0.5em;
        }
        li.text2qti-mctf-choice {
            list-style-type: "○";
            padding-left: 0.5em;
        }
        li.text2qti-mctf-correct-choice {
            list-style-type: "●";
            padding-left: 0.5em;
        }
        li.text2qti-multans-choice {
            list-style-type: "☐";
            padding-left: 0.5em;
        }
        li.text2qti-multans-correct-choice {
            list-style-type: "☑";
            padding-left: 0.5em;
        }
        li.text2qti-generic-correct {
            list-style-type: "🡆";
            padding-left: 0.5em;
        }
        ul > li.text2qti-solution::marker {
            font-size: 1.75em;
        }
        ul > li.text2qti-solution {
            margin-top: -0.25em;
        }
        li.text2qti-solution {
            list-style-type: "🗈";
            padding-left: 0.5em;
        }
        </style>
        '''[1:]
    ),
    'mctf_choice_start': '<li class="text2qti-mctf-choice">',
    'mctf_choice_end': '</li>',
    'mctf_correct_choice_start': '<li class="text2qti-mctf-correct-choice">',
    'mctf_correct_choice_end': '</li>',
    'multans_choice_start': '<li class="text2qti-multans-choice">',
    'multans_choice_end': '</li>',
    'multans_correct_choice_start': '<li class="text2qti-multans-correct-choice">',
    'multans_correct_choice_end': '</li>',
    'generic_correct_choice_start': '<li class="text2qti-generic-correct">',
    'generic_correct_choice_end': '</li>',
    'choices_start': '<ul class="text2qti">',
    'choices_end': '</ul>',
    'solution_start': '<ul class="text2qti"><li class="text2qti-solution">',
    'solution_end': '</ul></li>',
    'shortans_placeholder': '<div style="width:20em; height:1.5em; border:1px solid black;"></div>',
    'essay_placeholder': '<div style="width:100%; height:6em; border:1px solid black;"></div>',
    'file_upload_placeholder': '<pre style="border:1px solid black;"><file upload></pre>',
    'random_questions_start': '<div class="text2qti-randomized">',
    'random_questions_end': '</div>',
}

_templates = {}
template = textwrap.dedent(
    r'''
    ```{=latex}
    !{latex}
    ```

    ```{=html}
    !{html}
    ```

    '''[1:]
)
for key in _latex_templates:
    _templates[key] = template.replace('!{latex}', _latex_templates[key]).replace('!{html}', _html_templates[key])
del template
_templates['divider'] = '{0}\n\n'.format('-'*78)


def question_to_markdown(question: Question, *,
                         solutions: bool, unordered: bool,
                         show_points: bool=False) -> str:
    '''
    Convert a question to Markdown
    '''
    if not solutions:
        raise NotImplementedError

    quiz_md = []

    # List marker and point value
    if solutions and unordered:
        quiz_md.append('*   ')
    else:
        quiz_md.append('@.  ')
    if show_points:
        quiz_md.append('**[{0}]** '.format(question.points_possible))
    quiz_md.append(indent(markdown.md_to_pandoc(question.question_raw), 4, first_line=False))
    quiz_md.append('\n\n')

    if question.type in ('true_false_question', 'multiple_choice_question'):
        quiz_md.append(indent(_templates['choices_start'], 4))
        for choice in question.choices:
            if solutions and choice.correct:
                quiz_md.append(indent(_templates['mctf_correct_choice_start'], 4))
            else:
                quiz_md.append(indent(_templates['mctf_choice_start'], 4))
            quiz_md.append(indent(markdown.md_to_pandoc(choice.choice_raw), 4))
            quiz_md.append('\n\n')
            if solutions and choice.correct:
                quiz_md.append(indent(_templates['mctf_correct_choice_end'], 4))
            else:
                quiz_md.append(indent(_templates['mctf_choice_end'], 4))
        quiz_md.append(indent(_templates['choices_end'], 4))
    elif question.type == 'multiple_answers_question':
        quiz_md.append(indent(_templates['choices_start'], 4))
        for choice in question.choices:
            if solutions and choice.correct:
                quiz_md.append(indent(_templates['multans_correct_choice_start'], 4))
            else:
                quiz_md.append(indent(_templates['multans_choice_start'], 4))
            quiz_md.append(indent(markdown.md_to_pandoc(choice.choice_raw), 4))
            quiz_md.append('\n\n')
            if solutions and choice.correct:
                quiz_md.append(indent(_templates['multans_correct_choice_end'], 4))
            else:
                quiz_md.append(indent(_templates['multans_choice_end'], 4))
        quiz_md.append(indent(_templates['choices_end'], 4))
    elif question.type == 'short_answer_question':
        if solutions:
            quiz_md.append(indent(_templates['choices_start'], 4))
            quiz_md.append(indent(_templates['generic_correct_choice_start'], 4))
            quiz_md.append(indent(' | '.join(markdown.md_to_pandoc(choice.choice_raw) for choice in question.choices), 4))
            quiz_md.append('\n\n')
            quiz_md.append(indent(_templates['generic_correct_choice_end'], 4))
            quiz_md.append(indent(_templates['choices_end'], 4))
        else:
            quiz_md.append(indent(_templates['shortans_placeholder'], 4))
    elif question.type == 'numerical_question':
        if solutions:
            quiz_md.append(indent(_templates['choices_start'], 4))
            quiz_md.append(indent(_templates['generic_correct_choice_start'], 4))
            ans = question.numerical_raw
            if '+-' in ans:
                while '+- ' in ans:
                    ans = ans.replace('+- ', '+-')
                if ans.endswith('+-0'):
                    ans = ans[:-3]
                else:
                    ans = ans.replace('+-', r'\pm ')
                ans = ans.replace('%', r'\%')
            quiz_md.append(indent('$', 4))
            quiz_md.append(ans)
            if question.numerical_min is not None and question.numerical_max is not None:
                if '+-' in question.numerical_raw:
                    if isinstance(question.numerical_min, int) and isinstance(question.numerical_max, int):
                        quiz_md.append(rf' \quad \Rightarrow \quad [{question.numerical_min}, {question.numerical_max}]')
                    else:
                        quiz_md.append(rf' \quad \Rightarrow \quad [{question.numerical_min:.4f}, {question.numerical_max:.4f}]')
            quiz_md.append('$')
            quiz_md.append('\n\n')
            quiz_md.append(indent(_templates['generic_correct_choice_end'], 4))
            quiz_md.append(indent(_templates['choices_end'], 4))
    elif question.type == 'essay_question':
        if not solutions:
            quiz_md.append(indent(_templates['essay_placeholder'], 4))
    elif question.type == 'file_upload_question':
        if not solutions:
            quiz_md.append(indent(_templates['file_upload_placeholder'], 4))
    else:
        raise ValueError

    if solutions and question.solution is not None:
        quiz_md.append(indent(_templates['solution_start'], 4))
        quiz_md.append(indent(markdown.md_to_pandoc(question.solution), 4))
        quiz_md.append('\n\n')
        quiz_md.append(indent(_templates['solution_end'], 4))

    return ''.join(quiz_md)


def quiz_to_pandoc(quiz: Quiz, *, solutions=False) -> str:
    '''
    Generate a Pandoc Markdown version of assessment that optionally includes
    solutions.
    '''
    if not solutions:
        raise NotImplementedError

    quiz_md = []

    title = md_escape(quiz.title_raw or 'Quiz')
    title += r'`\\ \textsc{solutions}`{=latex}'
    title += r'`<br><span style="font-variant: small-caps;">solutions</span>`{=html}'
    title = title.replace('\\', '\\\\').replace(r'"', r'\"')
    meta = textwrap.dedent(
        r'''
        ---
        title: "{title}"
        header-includes: |
            {header}
        ...

        '''[1:]
    )
    meta = meta.format(title=title, header=indent(_templates['header'], 4, first_line=False))
    quiz_md.append(meta)

    if quiz.description_raw:
        quiz_md.append(markdown.md_to_pandoc(quiz.description_raw))
        quiz_md.append('\n\n')
        quiz_md.append(_templates['divider'])

    len_quiz_md_before_questions = len(quiz_md)
    in_group = False
    group_needs_divider = False
    for question_or_delim in quiz.questions_and_delims:
        if isinstance(question_or_delim, TextRegion):
            if question_or_delim.title_raw:
                if len(quiz_md) > len_quiz_md_before_questions and quiz_md[-1] != _templates['divider']:
                    quiz_md.append(_templates['divider'])
                quiz_md.append('## {0}\n\n'.format(md_escape(question_or_delim.title_raw.replace('\n', ' '))))
            if question_or_delim.text_raw:
                quiz_md.append(markdown.md_to_pandoc(question_or_delim.text_raw))
                quiz_md.append('\n\n')
            quiz_md.append(_templates['divider'])
            continue
        if isinstance(question_or_delim, GroupStart):
            in_group = True
            group = question_or_delim.group
            if solutions:
                if group.solutions_pick is not None:
                    num_questions_displayed = group.solutions_pick
                elif quiz.solutions_sample_groups:
                    num_questions_displayed = group.pick
                else:
                    num_questions_displayed = len(group.questions)
                if num_questions_displayed > 1:
                    if len(quiz_md) > len_quiz_md_before_questions and quiz_md[-1] != _templates['divider']:
                        quiz_md.append(_templates['divider'])
                    group_needs_divider = True
                if group.pick == 1:
                    if num_questions_displayed == 1:
                        quiz_md.append(f'### Randomized question: representative example is shown\n\n')
                    elif num_questions_displayed < len(group.questions):
                        quiz_md.append(f'### Randomized question: randomly select {group.pick} from representative examples shown\n\n')
                    else:
                        quiz_md.append(f'### Randomized question: randomly select {group.pick}\n\n')
                else:
                    if num_questions_displayed == group.pick:
                        quiz_md.append(f'### Randomized questions: representative examples are shown\n\n')
                    elif num_questions_displayed < len(group.questions):
                        quiz_md.append(f'### Randomized questions: randomly select {group.pick} from representative examples shown\n\n')
                    else:
                        quiz_md.append(f'### Randomized questions: randomly select {group.pick}\n\n')
                if num_questions_displayed != group.pick:
                    for _ in range(group.pick):
                        quiz_md.append('@.  `<randomly selected>`\n\n')
                unordered = num_questions_displayed != group.pick
                if unordered:
                    quiz_md.append(_templates['random_questions_start'])
                if quiz.solutions_randomize_groups:
                    for question in random.choices(question_or_delim.group.questions, num_questions_displayed):
                        quiz_md.append(question_to_markdown(question, solutions=solutions, unordered=unordered))
                else:
                    for question in question_or_delim.group.questions[:num_questions_displayed]:
                        quiz_md.append(question_to_markdown(question, solutions=solutions, unordered=unordered))
                if unordered:
                    quiz_md.append(_templates['random_questions_end'])
                if group_needs_divider:
                    quiz_md.append(_templates['divider'])
                    group_needs_divider = False
            continue
        if isinstance(question_or_delim, GroupEnd):
            in_group = False
            continue
        if isinstance(question_or_delim, Question):
            if in_group:
                continue
            quiz_md.append(question_to_markdown(question_or_delim, solutions=solutions, unordered=in_group))
            continue
        raise TypeError

    if quiz_md and quiz_md[-1] is _templates['divider']:
        quiz_md.pop()
    return ''.join(quiz_md)