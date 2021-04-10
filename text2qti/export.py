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



# https://daringfireball.net/projects/markdown/syntax
_md_escape_chars_re = re.compile(r'[\\`*_{}\[\]()#+\-.!]')

def _md_escape_chars_repl_func(match: re.Match) -> str:
    return '\\' + match.group()

def md_escape(raw_text: str) -> str:
    '''
    Escape raw text so that it is suitable for inclusion in Markdown.
    '''
    return _md_escape_chars_re.sub(_md_escape_chars_repl_func, raw_text)



LATEX_MCTF_CHOICE_I = r'\renewcommand{\labelitemi}{\resizebox{2ex}{!}{\faCircleO}\texttoqtiresetlabelitemi}'
LATEX_MCTF_CHOICE_II = LATEX_MCTF_CHOICE_I.replace('itemi', 'itemii')
LATEX_MCTF_CORRECT_CHOICE_I = r'\renewcommand{\labelitemi}{\resizebox{2ex}{!}{\faDotCircleO}\texttoqtiresetlabelitemi}'
LATEX_MCTF_CORRECT_CHOICE_II = LATEX_MCTF_CORRECT_CHOICE_I.replace('itemi', 'itemii')
LATEX_MULTANS_CHOICE_I = r'\renewcommand{\labelitemi}{\resizebox{2ex}{!}{\faSquareO}\texttoqtiresetlabelitemi}'
LATEX_MULTANS_CHOICE_II = LATEX_MULTANS_CHOICE_I.replace('itemi', 'itemii')
LATEX_MULTANS_CORRECT_CHOICE_I = r'\renewcommand{\labelitemi}{\resizebox{2ex}{!}{\faCheckSquare}\texttoqtiresetlabelitemi}'
LATEX_MULTANS_CORRECT_CHOICE_II = LATEX_MULTANS_CORRECT_CHOICE_I.replace('itemi', 'itemii')
LATEX_GENERAL_CORRECT_I = r'\renewcommand{\labelitemi}{\resizebox{2ex}{!}{\faArrowRight}\texttoqtiresetlabelitemi}'
LATEX_GENERAL_CORRECT_II = LATEX_GENERAL_CORRECT_I.replace('itemi', 'itemii')
LATEX_SOLUTION_I = r'\renewcommand{\labelitemi}{\resizebox{2ex}{!}{\faFileTextO}\texttoqtiresetlabelitemi}'
LATEX_SOLUTION_II = LATEX_SOLUTION_I.replace('itemi', 'itemii')

LATEX_SHORT_ANS_BOX = r'`\framebox[0.25\linewidth]{\strut}`{=tex}'
LATEX_ESSAY_ANS_BOX = r'`\framebox{\begin{minipage}\vspace{4\baselineskip}\end{minipage}}`{=tex}'

def question_to_markdown(question: Question, *,
                         solutions: bool, group_format: bool,
                         show_points: bool=False) -> str:
    '''
    Convert a question to Markdown
    '''
    if not solutions:
        raise NotImplementedError

    md = []

    if not group_format:
        latex_mctf_choice = LATEX_MCTF_CHOICE_I
        latex_mctf_correct_choice = LATEX_MCTF_CORRECT_CHOICE_I
        latex_multans_choice = LATEX_MULTANS_CHOICE_I
        latex_multans_correct_choice = LATEX_MULTANS_CORRECT_CHOICE_I
        latex_general_correct = LATEX_GENERAL_CORRECT_I
        latex_solution = LATEX_SOLUTION_I
    else:
        latex_mctf_choice = LATEX_MCTF_CHOICE_II
        latex_mctf_correct_choice = LATEX_MCTF_CORRECT_CHOICE_II
        latex_multans_choice = LATEX_MULTANS_CHOICE_II
        latex_multans_correct_choice = LATEX_MULTANS_CORRECT_CHOICE_II
        latex_general_correct = LATEX_GENERAL_CORRECT_II
        latex_solution = LATEX_SOLUTION_II

    # List marker and point value
    if solutions and group_format:
        md.append('*   ')
    else:
        md.append('@.  ')
    if show_points:
        md.append('**[{0}]** '.format(question.points_possible))
    md.append(question.question_raw.replace('\n', '\n' + ' '*4))
    md.append('\n\n')

    if question.type in ('true_false_question', 'multiple_choice_question'):
        for choice in question.choices:
            if solutions and choice.correct:
                md.append(' '*4 + f'`{latex_mctf_correct_choice}`{{=tex}}\n\n')
            else:
                md.append(' '*4 + f'`{latex_mctf_choice}`{{=tex}}\n\n')
            md.append(' '*4 + '*   ')
            md.append(choice.choice_raw.replace('\n', '\n' + ' '*8))
            md.append('\n\n')
        if solutions and question.solution is not None:
            md.append(' '*4 + f'`{LATEX_SOLUTION}`{{=tex}}\n\n')
            md.append(' '*4 + '*   ')
            md.append(question.solution.replace('\n', '\n' + ' '*8))
            md.append('\n\n')
    elif question.type == 'multiple_answers_question':
        for choice in question.choices:
            if solutions and choice.correct:
                md.append(' '*4 + f'`{latex_multans_correct_choice}`{{=tex}}\n\n')
            else:
                md.append(' '*4 + f'`{latex_multans_choice}`{{=tex}}\n\n')
            md.append(' '*4 + '*   ')
            md.append(choice.choice_raw.replace('\n', '\n' + ' '*8))
            md.append('\n\n')
        if solutions and question.solution is not None:
            md.append(' '*4 + f'`{latex_solution}`{{=tex}}\n\n')
            md.append(' '*4 + '*   ')
            md.append(question.solution.replace('\n', '\n' + ' '*8))
            md.append('\n\n')
    elif question.type == 'short_answer_question':
        if solutions:
            md.append(' '*4 + f'`{latex_general_correct}`{{=tex}}\n\n')
            md.append(' '*4 + '*   ')
            md.append(' **|** '.join(choice.choice_raw for choice in question.choices))
            md.append('\n\n')
            if question.solution is not None:
                md.append(' '*4 + f'`{latex_solution}`{{=tex}}\n\n')
                md.append(' '*4 + '*   ')
                md.append(question.solution.replace('\n', '\n' + ' '*8))
                md.append('\n\n')
        else:
            md.append(' '*4 + LATEX_SHORT_ANS_BOX)
            md.append('\n\n')
    elif question.type == 'numerical_question':
        if solutions:
            md.append(' '*4 + f'`{latex_general_correct}`{{=tex}}\n\n')
            md.append(' '*4 + '*   ')
            ans = question.numerical_raw
            if '+-' in ans:
                while '+- ' in ans:
                    ans = ans.replace('+- ', '+-')
                if ans.endswith('+-0'):
                    ans = ans[:-3]
                else:
                    ans = ans.replace('+-', r'\pm ')
                ans = ans.replace('%', r'\%')
            md.append('$')
            md.append(ans)
            if question.numerical_min is not None and question.numerical_max is not None:
                if '+-' in question.numerical_raw:
                    if isinstance(question.numerical_min, int) and isinstance(question.numerical_max, int):
                        md.append(rf' \quad \Rightarrow \quad [{question.numerical_min}, {question.numerical_max}]')
                    else:
                        md.append(rf' \quad \Rightarrow \quad [{question.numerical_min:.4f}, {question.numerical_max:.4f}]')
            md.append('$')
            md.append('\n\n')
            if question.solution is not None:
                md.append(' '*4 + f'`{latex_solution}`{{=tex}}\n\n')
                md.append(' '*4 + '*   ')
                md.append(question.solution.replace('\n', '\n' + ' '*8))
                md.append('\n\n')
    elif question.type == 'essay_question':
        if solutions:
            if question.solution is not None:
                md.append(' '*4 + f'`{latex_solution}`{{=tex}}\n\n')
                md.append(' '*4 + '*   ')
                md.append(question.solution.replace('\n', '\n' + ' '*8))
                md.append('\n\n')
        else:
            md.append(' '*4 + LATEX_ESSAY_ANS_BOX)
    elif question.type == 'file_upload_question':
        if solutions:
            if question.solution is not None:
                md.append(' '*4 + f'`{latex_solution}`{{=tex}}\n\n')
                md.append(' '*4 + '*   ')
                md.append(question.solution.replace('\n', '\n' + ' '*8))
                md.append('\n\n')
        else:
            md.append(' '*4 + '`<file upload>`\n\n')
    else:
        raise ValueError

    return ''.join(md)




def quiz_to_pandoc_markdown(quiz: Quiz, *, solutions=False) -> str:
    '''
    Generate a Pandoc Markdown version of assessment that optionally includes
    solutions.
    '''
    if not solutions:
        raise NotImplementedError

    md = []
    hrule = '{0}\n\n'.format('-'*78)

    title = md_escape(quiz.title_raw or 'Quiz')
    title += r'`\\ \textsc{solutions}`{=latex}'
    title = title.replace('\\', '\\\\').replace(r'"', r'\"')
    md.append(
        textwrap.dedent(
            r'''
            ---
            title: "!{title}"
            header-includes: |
                ```{=latex}
                %%%% Begin text2qti custom preamble
                % Page layout
                \usepackage[margin=1in]{geometry}
                % Graphics
                \usepackage{graphicx}
                % Symbols for solutions
                \usepackage{fontawesome}
                % Units and chem equations
                \usepackage{siunitx}
                \usepackage{mhchem}
                % Answers and solutions use itemize with custom item symbols
                \makeatletter
                \AtBeginDocument{%
                    \let\labelitemi@orig\labelitemi
                    \let\labelitemii@orig\labelitemii
                }
                \newcommand{\texttoqtiresetlabelitemi}{%
                    \global\let\labelitemi\labelitemi@orig
                }
                \newcommand{\texttoqtiresetlabelitemii}{%
                    \global\let\labelitemii\labelitemii@orig
                }
                \makeatother
                %%%% End text2qti custom preamble
                ```
            ...

            '''[1:].replace('!{title}', title)
        )
    )

    if quiz.description_raw:
        md.append(quiz.description_raw)
        md.append('\n\n')
        md.append(hrule)

    len_md_before_questions = len(md)
    in_group = False
    group_needs_hrule = False
    for question_or_delim in quiz.questions_and_delims:
        if isinstance(question_or_delim, TextRegion):
            if question_or_delim.title_raw:
                if len(md) > len_md_before_questions and md[-1] != hrule:
                    md.append(hrule)
                md.append('## {0}\n\n'.format(md_escape(question_or_delim.title_raw.replace('\n', ' '))))
            if question_or_delim.text_raw:
                md.append(question_or_delim.text_raw)
                md.append('\n\n')
            md.append(hrule)
            continue
        if isinstance(question_or_delim, GroupStart):
            in_group = True
            group = question_or_delim.group
            if solutions:
                if quiz.solutions_sample_groups:
                    if group.solutions_pick is None or group.solutions_pick == group.pick:
                        num_questions_displayed = group.pick
                        if group.pick == 1:
                            md.append(f'### Randomized question: representative example is shown\n\n')
                        else:
                            md.append(f'### Randomized questions: {num_questions_displayed} representative examples are shown\n\n')
                    else:
                        if len(md) > len_md_before_questions and md[-1] != hrule:
                            md.append(hrule)
                        group_needs_hrule = True
                        num_questions_displayed = group.solutions_pick
                        if group.pick == 1:
                            md.append(f'### Randomized question: randomly select {group.pick} from representative examples shown\n\n')
                        else:
                            md.append(f'### Randomized questions: randomly select {group.pick} from representative examples shown\n\n')
                else:
                    if len(md) > len_md_before_questions and md[-1] != hrule:
                        md.append(hrule)
                    group_needs_hrule = True
                    num_questions_displayed = len(group.questions)
                    if group.pick == 1:
                        md.append(f'### Randomized question: randomly select {group.pick}\n\n')
                    else:
                        md.append(f'### Randomized questions: randomly select {group.pick}\n\n')
                if num_questions_displayed != group.pick:
                    for _ in range(group.pick):
                        md.append('@.  `<randomly selected>`\n\n')
                if quiz.solutions_randomize_groups:
                    for question in random.choices(question_or_delim.group.questions, num_questions_displayed):
                        md.append(question_to_markdown(question, solutions=solutions, group_format=(num_questions_displayed!=group.pick)))
                else:
                    for question in question_or_delim.group.questions[:num_questions_displayed]:
                        md.append(question_to_markdown(question, solutions=solutions, group_format=(num_questions_displayed!=group.pick)))
            continue
        if isinstance(question_or_delim, GroupEnd):
            in_group = False
            group = question_or_delim.group
            if solutions:
                if group_needs_hrule:
                    md.append(hrule)
                group_needs_hrule = False
            continue
        if isinstance(question_or_delim, Question):
            if not in_group:
                md.append(question_to_markdown(question_or_delim, solutions=solutions, group_format=in_group))
            continue
        raise TypeError

    if md and md[-1] is hrule:
        md.pop()
    return ''.join(md)