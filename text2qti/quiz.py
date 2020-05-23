# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


'''
Parse text into a Quiz object that contains a list of Question objects, each
of which contains a list of Choice objects.
'''


import hashlib
import io
import itertools
import locale
import pathlib
import re
import shlex
import subprocess
import tempfile
from typing import Dict, List, Optional, Set, Union
from .config import Config
from .err import Text2qtiError
from .markdown import Image, Markdown




# regex patterns for parsing quiz content
start_patterns = {
    'question': r'\d+\.',
    'mctf_correct_choice': r'\*[a-zA-Z]\)',
    'mctf_incorrect_choice': r'[a-zA-Z]\)',
    'multans_correct_choice': r'\[\*\]',
    'multans_incorrect_choice': r'\[ ?\]',
    'feedback': r'\.\.\.',
    'correct_feedback': r'\+',
    'incorrect_feedback': r'\-',
    'essay': r'___+',
    'numerical': r'=',
    'question_title': r'[Tt]itle:',
    'question_points': r'[Pp]oints:',
    'quiz_title': r'[Qq]uiz [Tt]itle:',
    'quiz_description': r'[Qq]uiz [Dd]escription:',
    'start_group': r'GROUP',
    'end_group': r'END_GROUP',
    'group_pick': r'[Pp]ick:',
    'group_points_per_question': r'[Pp]oints per question:',
    'start_code': r'```+\s*\S.*',
    'end_code': r'```+',
}
# comments are currently handled separately from content
comment_patterns = {
    'start_multiline_comment': r'COMMENT',
    'end_multiline_comment': r'END_COMMENT',
    'line_comment': r'%',
}
# whether regex needs to check after pattern for content on the same line
no_content = set(['essay', 'start_group', 'end_group', 'start_code', 'end_code'])
# whether parser needs to check for multi-line content
multi_line = set([x for x in start_patterns
                  if x not in no_content and not any(y in x for y in ('pick', 'points', 'numerical'))])
# whether parser needs to check for multi-paragraph content
multi_para = set([x for x in start_patterns
                  if x not in no_content and not any(y in x for y in ('title', 'pick', 'points', 'numerical'))])
start_re = re.compile('|'.join(r'(?P<{0}>{1}[ \t]+(?=\S))'.format(name, pattern)
                               if name not in no_content else
                               r'(?P<{0}>{1}\s*)$'.format(name, pattern)
                               for name, pattern in start_patterns.items()))
start_missing_content_re = re.compile('|'.join(r'(?P<{0}>{1}[ \t]*$)'.format(name, pattern)
                                               for name, pattern in start_patterns.items()
                                               if name not in no_content))
start_missing_whitespace_re = re.compile('|'.join(r'(?P<{0}>{1}(?=\S))'.format(name, pattern)
                                                  for name, pattern in start_patterns.items()
                                                  if name not in no_content))
start_code_supported_info_re = re.compile(r'\{\s*\.[a-zA-Z](?:[a-zA-Z0-9]+|(?:_+|-+)[a-zA-Z0-9]+)*\s+\.run\s*\}$')
int_re = re.compile('(?:0|[+-]?[1-9](?:[0-9]+|_[0-9]+)*)$')




class Choice(object):
    '''
    A choice for a question plus optional feedback.

    The id is based on a hash of both the question and the choice itself.
    The presence of feedback does not affect the id.
    '''
    def __init__(self, text: str, *,
                 correct: bool, question_hash_digest: bytes, md: Markdown):
        self.choice_raw = text
        self.choice_html_xml = md.md_to_html_xml(text)
        self.correct = correct
        self.feedback_raw: Optional[str] = None
        self.feedback_html_xml: Optional[str] = None
        # ID is based on hash of choice XML as well as question XML.  This
        # gives different IDs for identical choices in different questions.
        self.id = hashlib.blake2b(self.choice_html_xml.encode('utf8'), key=question_hash_digest).hexdigest()[:64]
        self.md = md

    def append_feedback(self, text: str):
        if self.feedback_raw is not None:
            raise Text2qtiError('Feedback can only be specified once')
        self.feedback_raw = text
        self.feedback_html_xml = self.md.md_to_html_xml(text)


class Question(object):
    '''
    A question, along with a list of possible choices and optional feedback of
    various types.
    '''
    def __init__(self, text: str, *, title: Optional[str], points: Optional[str], md: Markdown):
        # Question type is set once it is known.  For true/false or multiple
        # choice, this is done during .finalize(), once all choices are
        # available.  For essay, this is done as soon as essay response is
        # specified.
        self.type: Optional[str] = None
        if title is None:
            self.title_raw: Optional[str] = None
            self.title_xml = 'Question'
        else:
            self.title_raw: Optional[str] = title
            self.title_xml = md.xml_escape(title)
        self.question_raw = text
        self.question_html_xml = md.md_to_html_xml(text)
        self.choices: List[Choice] = []
        # The set for detecting duplicate choices uses the XML version of the
        # choices, to avoid the issue of multiple Markdown representations of
        # the same XML.
        self._choice_set: Set[str] = set()
        self.numerical_min: Optional[Union[int, float]] = None
        self.numerical_min_html_xml: Optional[str] = None
        self.numerical_exact: Optional[Union[int, float]] = None
        self.numerical_exact_html_xml: Optional[str] = None
        self.numerical_max: Optional[Union[int, float]] = None
        self.numerical_max_html_xml: Optional[str] = None
        self.correct_choices = 0
        if points is None:
            self.points_possible_raw: Optional[str] = None
            self.points_possible: Union[int, float] = 1
        else:
            self.points_possible_raw: Optional[str] = points
            try:
                points_num = float(points)
            except ValueError:
                raise Text2qtiError(f'Invalid points value "{points}"; need positive integer or half-integer')
            if points_num <= 0:
                raise Text2qtiError(f'Invalid points value "{points}"; need positive integer or half-integer')
            if points_num.is_integer():
                points_num = int(points)
            elif abs(points_num-round(points_num)) != 0.5:
                raise Text2qtiError(f'Invalid points value "{points}"; need positive integer or half-integer')
            self.points_possible: Union[int, float] = points_num
        self.feedback_raw: Optional[str] = None
        self.feedback_html_xml: Optional[str] = None
        self.correct_feedback_raw: Optional[str] = None
        self.correct_feedback_html_xml: Optional[str] = None
        self.incorrect_feedback_raw: Optional[str] = None
        self.incorrect_feedback_html_xml: Optional[str] = None
        h = hashlib.blake2b(self.question_html_xml.encode('utf8'))
        self.hash_digest = h.digest()
        self.id = h.hexdigest()[:64]
        self.md = md


    _no_feedback_question_types = set(['essay_question'])

    def append_feedback(self, text: str):
        if self.type is not None:
            if self.type in self._no_feedback_question_types:
                raise Text2qtiError(f'Question type "{self.type}" does not support feedback')
            raise Text2qtiError('Question feedback must immediately follow the question')
        if not self.choices:
            if self.feedback_raw is not None:
                raise Text2qtiError('Feedback can only be specified once')
            self.feedback_raw = text
            self.feedback_html_xml = self.md.md_to_html_xml(text)
        else:
            self.choices[-1].append_feedback(text)

    def append_correct_feedback(self, text: str):
        if self.type is not None:
            if self.type in self._no_feedback_question_types:
                raise Text2qtiError(f'Question type "{self.type}" does not support feedback')
            raise Text2qtiError('Question feedback must immediately follow the question')
        if self.choices:
            raise Text2qtiError('Correct feedback can only be specified for questions, not choices')
        if self.correct_feedback_raw is not None:
            raise Text2qtiError('Feedback can only be specified once')
        self.correct_feedback_raw = text
        self.correct_feedback_html_xml = self.md.md_to_html_xml(text)

    def append_incorrect_feedback(self, text: str):
        if self.type is not None:
            if self.type in self._no_feedback_question_types:
                raise Text2qtiError(f'Question type "{self.type}" does not support feedback')
            raise Text2qtiError('Question feedback must immediately follow the question')
        if self.choices:
            raise Text2qtiError('Incorrect feedback can only be specified for questions, not choices')
        if self.incorrect_feedback_raw is not None:
            raise Text2qtiError('Feedback can only be specified once')
        self.incorrect_feedback_raw = text
        self.incorrect_feedback_html_xml = self.md.md_to_html_xml(text)

    def append_mctf_correct_choice(self, text: str):
        if self.type is not None:
            raise Text2qtiError(f'Question type "{self.type}" does not support multiple choice')
        choice = Choice(text, correct=True, question_hash_digest=self.hash_digest, md=self.md)
        if choice.choice_html_xml in self._choice_set:
            raise Text2qtiError('Duplicate choice for question')
        self._choice_set.add(choice.choice_html_xml)
        self.choices.append(choice)
        self.correct_choices += 1

    def append_mctf_incorrect_choice(self, text: str):
        if self.type is not None:
            raise Text2qtiError(f'Question type "{self.type}" does not support multiple choice')
        choice = Choice(text, correct=False, question_hash_digest=self.hash_digest, md=self.md)
        if choice.choice_html_xml in self._choice_set:
            raise Text2qtiError('Duplicate choice for question')
        self._choice_set.add(choice.choice_html_xml)
        self.choices.append(choice)

    def append_multans_correct_choice(self, text: str):
        if self.type is None:
            self.type = 'multiple_answers_question'
            if self.choices:
                raise Text2qtiError(f'Question type "{self.type}" is not compatible with existing choices')
        elif self.type != 'multiple_answers_question':
            raise Text2qtiError(f'Question type "{self.type}" does not support multiple answers')
        choice = Choice(text, correct=True, question_hash_digest=self.hash_digest, md=self.md)
        if choice.choice_html_xml in self._choice_set:
            raise Text2qtiError('Duplicate choice for question')
        self._choice_set.add(choice.choice_html_xml)
        self.choices.append(choice)
        self.correct_choices += 1

    def append_multans_incorrect_choice(self, text: str):
        if self.type is None:
            self.type = 'multiple_answers_question'
            if self.choices:
                raise Text2qtiError(f'Question type "{self.type}" is not compatible with existing choices')
        elif self.type != 'multiple_answers_question':
            raise Text2qtiError(f'Question type "{self.type}" does not support multiple answers')
        choice = Choice(text, correct=False, question_hash_digest=self.hash_digest, md=self.md)
        if choice.choice_html_xml in self._choice_set:
            raise Text2qtiError('Duplicate choice for question')
        self._choice_set.add(choice.choice_html_xml)
        self.choices.append(choice)

    def append_essay(self, text: str):
        if text:
            # The essay response indicator consumes its entire line, leaving
            # the empty string; `text` just gives all append functions
            # the same form.
            raise ValueError
        if self.type is not None:
            if self.type == 'essay_question':
                raise Text2qtiError(f'Cannot specify essay response multiple times')
            raise Text2qtiError(f'Question type "{self.type}" does not support essay response')
        self.type = 'essay_question'
        if self.choices:
            raise Text2qtiError(f'Question type "{self.type}" is not compatible with existing choices')
        if any(x is not None for x in (self.feedback_raw, self.correct_feedback_raw, self.incorrect_feedback_raw)):
            raise Text2qtiError(f'Question type "{self.type}" does not support feedback')

    def append_numerical(self, text: str):
        if self.type is not None:
            if self.type == 'numerical_question':
                raise Text2qtiError(f'Cannot specify numerical response multiple times')
            raise Text2qtiError(f'Question type "{self.type}" does not support numerical response')
        self.type = 'numerical_question'
        if self.choices:
            raise Text2qtiError(f'Question type "{self.type}" is not compatible with existing choices')
        if text.startswith('['):
            if not text.endswith(']') or ',' not in text:
                raise Text2qtiError('Invalid numerical response; need "[<min>, <max>]" or "<number> +- <margin>" or "<integer>"')
            min, max = text[1:-1].split(',', 1)
            try:
                min = float(min)
                max = float(max)
            except Exception:
                raise Text2qtiError('Invalid numerical response; need "[<min>, <max>]" or "<number> +- <margin>" or "<integer>"')
            if min > max:
                raise Text2qtiError('Invalid numerical response; need "[<min>, <max>]" with min < max')
            self.numerical_min = min
            self.numerical_max = max
            if min.is_integer() and max.is_integer():
                self.numerical_min_html_xml = f'{min}'
                self.numerical_max_html_xml = f'{max}'
            else:
                self.numerical_min_html_xml = f'{min:.4f}'
                self.numerical_max_html_xml = f'{max:.4f}'
        elif '+-' in text:
            num, margin = text.split('+-', 1)
            if margin.endswith('%'):
                margin_is_percentage = True
                margin = margin[:-1]
            else:
                margin_is_percentage = False
            try:
                num = float(num)
                margin = float(margin)
            except Exception:
                raise Text2qtiError('Invalid numerical response; need "[<min>, <max>]" or "<number> +- <margin>" or "<integer>"')
            if margin < 0:
                raise Text2qtiError('Invalid numerical response; need "<number> +- <margin>" with margin > 0')
            if margin_is_percentage:
                min = num - abs(num)*(margin/100)
                max = num + abs(num)*(margin/100)
            else:
                min = num - margin
                max = num + margin
            self.numerical_min = min
            self.numerical_exact = num
            self.numerical_max = max
            if min.is_integer() and num.is_integer() and max.is_integer():
                self.numerical_min_html_xml = f'{min}'
                self.numerical_exact_html_xml = f'{num}'
                self.numerical_max_html_xml = f'{max}'
            else:
                self.numerical_min_html_xml = f'{min:.4f}'
                self.numerical_exact_html_xml = f'{num:.4f}'
                self.numerical_max_html_xml = f'{max:.4f}'
        elif int_re.match(text):
            num = int(text)
            min = max = num
            self.numerical_min = min
            self.numerical_exact = num
            self.numerical_max = max
            self.numerical_min_html_xml = f'{min}'
            self.numerical_exact_html_xml = f'{num}'
            self.numerical_max_html_xml = f'{max}'
        else:
            raise Text2qtiError('Invalid numerical response; need "[<min>, <max>]" or "<number> +- <margin>" or "<integer>"')
        if abs(min) < 1e-4 or abs(max) < 1e-4:
            raise Text2qtiError('Invalid numerical response; all acceptable values must have a magnitude >= 0.0001')


    def finalize(self):
        if self.type is None:
            if len(self.choices) == 2 and all(c.choice_raw.lower() in ('true', 'false') for c in self.choices):
                self.type = 'true_false_question'
            else:
                self.type = 'multiple_choice_question'
            if not self.choices:
                raise Text2qtiError('Question must provide choices')
            if len(self.choices) < 2:
                raise Text2qtiError('Question must provide more than one choice')
            if self.correct_choices < 1:
                raise Text2qtiError('Question must specify a correct choice')
            if self.correct_choices > 1:
                raise Text2qtiError('Question must specify only one correct choice')
        elif self.type == 'multiple_answers_question':
            # There must be at least one choice for the type to be set, so
            # don't need to check for zero choices
            if len(self.choices) < 2:
                raise Text2qtiError('Question must provide more than one choice')
            if self.correct_choices < 1:
                raise Text2qtiError('Question must specify a correct choice')




class Group(object):
    '''
    A group of questions.  A random subset of the questions in a group is
    actually displayed.
    '''
    def __init__(self):
        self.pick = 1
        self._pick_is_set = False
        self.points_per_question = 1
        self._points_per_question_is_set = False
        self.questions: List[Question] = []
        self._question_points_possible: Optional[int] = None
        self.title_raw: Optional[str] = None
        self.title_xml = 'Group'

    def append_group_pick(self, text: str):
        if self.questions:
            raise Text2qtiError('Question group options must be set at the very start of the group')
        if self._pick_is_set:
            Text2qtiError('"Pick" has already been set for this question group')
        try:
            self.pick = int(text)
        except Exception as e:
            raise Text2qtiError(f'"Pick" value is invalid (must be positive number):\n{e}')
        if self.pick <= 0:
            raise Text2qtiError(f'"Pick" value is invalid (must be positive number)')
        self._pick_is_set = True

    def append_group_points_per_question(self, text: str):
        if self.questions:
            raise Text2qtiError('Question group options must be set at the very start of the group')
        if self._points_per_question_is_set:
            Text2qtiError('"Points per question" has already been set for this question group')
        try:
            self.points_per_question = int(text)
        except Exception as e:
            raise Text2qtiError(f'"Points per question" value is invalid (must be positive number):\n{e}')
        if self.points_per_question <= 0:
            raise Text2qtiError(f'"Points per question" value is invalid (must be positive number):')
        self._points_per_question_is_set = True

    def append_question(self, question: Question):
        if self._question_points_possible is None:
            self._question_points_possible = question.points_possible
        elif question.points_possible != self._question_points_possible:
            raise Text2qtiError('Question groups must only contain questions with the same point value')
        self.questions.append(question)

    def finalize(self):
        if len(self.questions) <= self.pick:
            raise Text2qtiError(f'Question group only contains {len(self.questions)} questions, needs at least {self.pick+1}')
        h = hashlib.blake2b()
        for digest in sorted(q.hash_digest for q in self.questions):
            h.update(digest)
        self.hash_digest = h.digest()
        self.id = h.hexdigest()[:64]

class GroupStart(object):
    '''
    Start delim for a group of questions.
    '''
    def __init__(self, group: Group):
        self.group = group

class GroupEnd(object):
    '''
    End delim for a group of questions.
    '''
    def __init__(self, group: Group):
        self.group = group




class Quiz(object):
    '''
    A quiz or assessment.  Contains a list of questions along with possible
    choices and feedback.
    '''
    def __init__(self, string: str, *, config: Config,
                 source_name: Optional[str]=None,
                 resource_path: Optional[Union[str, pathlib.Path]]=None):
        self.string = string
        self.config = config
        self.source_name = '<string>' if source_name is None else f'"{source_name}"'
        if resource_path is not None:
            if isinstance(resource_path, str):
                resource_path = pathlib.Path(resource_path)
            else:
                raise TypeError
            if not resource_path.is_dir():
                raise Text2qtiError(f'Resource path "{resource_path.as_posix()}" does not exist')
        self.resource_path = resource_path
        self.title_raw = None
        self.title_xml = 'Quiz'
        self.description_raw = None
        self.description_html_xml = ''
        self.questions_and_delims: List[Union[Question, GroupStart, GroupEnd]] = []
        self._current_group: Optional[Group] = None
        # The set for detecting duplicate questions uses the XML version of
        # the question, to avoid the issue of multiple Markdown
        # representations of the same XML.
        self.question_set: Set[str] = set()
        self.md = Markdown(config)
        self.images: Dict[str, Image] = self.md.images
        self._next_question_attr = {}

        parse_actions = {}
        for k in start_patterns:
            parse_actions[k] = getattr(self, f'append_{k}')
        parse_actions[None] = self.append_unknown
        start_multiline_comment_pattern = comment_patterns['start_multiline_comment']
        end_multiline_comment_pattern = comment_patterns['end_multiline_comment']
        line_comment_pattern = comment_patterns['line_comment']
        n_line_iter = iter(x for x in enumerate(string.splitlines()))
        n, line = next(n_line_iter, (0, None))
        lookahead = False
        n_code_start = 0
        while line is not None:
            match = start_re.match(line)
            if match:
                action = match.lastgroup
                text = line[match.end():].strip()
                if action == 'start_code':
                    info = line.lstrip('`').strip()
                    if not start_code_supported_info_re.match(info):
                        pass
                    else:
                        executable = info.replace('.run', '').strip('{} \t.')
                        delim = '`'*(len(line) - len(line.lstrip('`')))
                        n_code_start = n
                        code_lines = []
                        n, line = next(n_line_iter, (0, None))
                        # No lookahead here; all lines are consumed
                        while line is not None and not (line.startswith(delim) and line[len(delim):] == line.lstrip('`')):
                            code_lines.append(line)
                            n, line = next(n_line_iter, (0, None))
                        if line is None:
                            raise Text2qtiError(f'In {self.source_name} on line {n}:\nCode closing fence is missing')
                        if line.lstrip('`').strip():
                            raise Text2qtiError(f'In {self.source_name} on line {n+1}:\nCode closing fence is missing')
                        code_lines.append('\n')
                        code = '\n'.join(code_lines)
                        try:
                            stdout = self._run_code(executable, code)
                        except Exception as e:
                            raise Text2qtiError(f'In {self.source_name} on line {n_code_start+1}:\n{e}')
                        code_n_line_iter = ((n_code_start, stdout_line) for stdout_line in stdout.splitlines())
                        n_line_iter = itertools.chain(code_n_line_iter, n_line_iter)
                        n, line = next(n_line_iter, (0, None))
                        continue
                elif action in multi_line:
                    if start_patterns[action].endswith(':'):
                        indent_expandtabs = None
                    else:
                        indent_expandtabs = ' '*len(line[:match.end()].expandtabs(4))
                    text_lines = [text]
                    n, line = next(n_line_iter, (0, None))
                    line_expandtabs = line.expandtabs(4) if line is not None else None
                    lookahead = True
                    while (line is not None and
                            (not line or line.isspace() or
                                indent_expandtabs is None or line_expandtabs.startswith(indent_expandtabs))):
                        if not line or line.isspace():
                            if action in multi_para:
                                text_lines.append('')
                            else:
                                break
                        else:
                            if indent_expandtabs is None:
                                if not line.startswith(' '):
                                    break
                                indent_expandtabs = ' '*(len(line_expandtabs)-len(line_expandtabs.lstrip(' ')))
                                if len(indent_expandtabs) < 2:
                                    raise Text2qtiError(f'In {self.source_name} on line {n+1}:\nIndentation must be at least 2 spaces or 1 tab here')
                            # The `rstrip()` prevents trailing double
                            # spaces from becoming `<br />`.
                            text_lines.append(line_expandtabs[len(indent_expandtabs):].rstrip())
                        n, line = next(n_line_iter, (0, None))
                        line_expandtabs = line.expandtabs(4) if line is not None else None
                    text = '\n'.join(text_lines)
            elif line.startswith(line_comment_pattern):
                n, line = next(n_line_iter, (0, None))
                continue
            elif line.startswith(start_multiline_comment_pattern):
                if line.strip() != start_multiline_comment_pattern:
                    raise Text2qtiError(f'In {self.source_name} on line {n+1}:\nUnexpected content after "{start_multiline_comment_pattern}"')
                n, line = next(n_line_iter, (0, None))
                while line is not None and not line.startswith(end_multiline_comment_pattern):
                    n, line = next(n_line_iter, (0, None))
                if line is None:
                    raise Text2qtiError(f'In {self.source_name} on line {n+1}:\nf"{start_multiline_comment_pattern}" without following "{end_multiline_comment_pattern}"')
                if line.strip() != end_multiline_comment_pattern:
                    raise Text2qtiError(f'In {self.source_name} on line {n+1}:\nUnexpected content after "{end_multiline_comment_pattern}"')
                n, line = next(n_line_iter, (0, None))
                continue
            elif line.startswith(end_multiline_comment_pattern):
                raise Text2qtiError(f'In {self.source_name} on line {n+1}:\n"{end_multiline_comment_pattern}" without preceding "{start_multiline_comment_pattern}"')
            else:
                action = None
                text = line
            try:
                parse_actions[action](text)
            except Text2qtiError as e:
                if lookahead and n != n_code_start:
                    raise Text2qtiError(f'In {self.source_name} on line {n}:\n{e}')
                raise Text2qtiError(f'In {self.source_name} on line {n+1}:\n{e}')
            if not lookahead:
                n, line = next(n_line_iter, (0, None))
            lookahead = False
        if not self.questions_and_delims:
            raise Text2qtiError('No questions were found')
        if self._current_group is not None:
            raise Text2qtiError(f'In {self.source_name} on line {len(string.splitlines())}:\nQuestion group never ended')
        last_question_or_delim = self.questions_and_delims[-1]
        if isinstance(last_question_or_delim, Question):
            try:
                last_question_or_delim.finalize()
            except Text2qtiError as e:
                raise Text2qtiError(f'In {self.source_name} on line {len(string.splitlines())}:\n{e}')

        points_possible = 0
        digests = []
        for x in self.questions_and_delims:
            if isinstance(x, Question):
                points_possible += x.points_possible
                digests.append(x.hash_digest)
            elif isinstance(x, GroupStart):
                points_possible += x.group.points_per_question*len(x.group.questions)
                digests.append(x.group.hash_digest)
            elif isinstance(x, GroupEnd):
                pass
            else:
                raise TypeError
        self.points_possible = points_possible
        h = hashlib.blake2b()
        for digest in sorted(digests):
            h.update(digest)
        self.hash_digest = h.digest()
        self.id = h.hexdigest()[:64]

        self.md.finalize()

    def _run_code(self, executable: str, code: str) -> str:
        if not self.config['run_code_blocks']:
            raise Text2qtiError('Code execution for code blocks is not enabled; use --run-code-blocks, or set run_code_blocks = true in config')
        h = hashlib.blake2b()
        h.update(code.encode('utf8'))
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_path = pathlib.Path(tempdir)
            code_path = tempdir_path / f'{h.hexdigest()[:16]}.code'
            code_path.write_text(code, encoding='utf8')
            cmd = shlex.split(f'{executable} {code_path.as_posix()}')
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except FileNotFoundError as e:
                raise Text2qtiError(f'Failed to execute code (missing executable "{executable}"?):\n{e}')
            except Exception as e:
                raise Text2qtiError(f'Failed to execute code with command "{cmd}":\n{e}')
        # Use io to handle output as if read from a file in terms of newline
        # treatment
        if proc.returncode != 0:
            stderr_str = io.TextIOWrapper(io.BytesIO(proc.stderr),
                                          encoding=locale.getpreferredencoding(False),
                                          errors='backslashreplace').read()
            raise Text2qtiError(f'Code execution resulted in errors:\n{"-"*50}\n{stderr_str}\n{"-"*50}')
        try:
            stdout_str = io.TextIOWrapper(io.BytesIO(proc.stdout),
                                          encoding=locale.getpreferredencoding(False)).read()
        except Exception as e:
            raise Text2qtiError(f'Failed to decode output of executed code:\n{e}')
        return stdout_str


    def append_quiz_title(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if self.title_raw is not None:
            raise Text2qtiError('Quiz title has already been given')
        if self.questions_and_delims:
            raise Text2qtiError('Must give quiz title before questions')
        if self.description_raw is not None:
            raise Text2qtiError('Must give quiz title before quiz description')
        self.title_raw = text
        self.title_xml = self.md.xml_escape(text)

    def append_quiz_description(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if self.description_raw is not None:
            raise Text2qtiError('Quiz description has already been given')
        if self.questions_and_delims:
            raise Text2qtiError('Must give quiz description before questions')
        self.description_raw = text
        self.description_html_xml = self.md.md_to_html_xml(text)

    def append_question(self, text: str):
        if self.questions_and_delims:
            last_question_or_delim = self.questions_and_delims[-1]
            if isinstance(last_question_or_delim, Question):
                last_question_or_delim.finalize()
        question = Question(text,
                            title=self._next_question_attr.get('title'),
                            points=self._next_question_attr.get('points'),
                            md=self.md)
        self._next_question_attr = {}
        if question.question_html_xml in self.question_set:
            raise Text2qtiError('Duplicate question')
        self.question_set.add(question.question_html_xml)
        self.questions_and_delims.append(question)
        if self._current_group is not None:
            self._current_group.append_question(question)

    def append_question_title(self, text: str):
        if 'title' in self._next_question_attr:
            raise Text2qtiError('Title for next question has already been set')
        self._next_question_attr['title'] = text

    def append_question_points(self, text: str):
        if 'points' in self._next_question_attr:
            raise Text2qtiError('Points for next question has already been set')
        self._next_question_attr['points'] = text

    def append_feedback(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have feedback without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have feedback without a question')
        last_question_or_delim.append_feedback(text)

    def append_correct_feedback(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have feedback without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have feedback without a question')
        last_question_or_delim.append_correct_feedback(text)

    def append_incorrect_feedback(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have feedback without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have feedback without a question')
        last_question_or_delim.append_incorrect_feedback(text)

    def append_mctf_correct_choice(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have a choice without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have a choice without a question')
        last_question_or_delim.append_mctf_correct_choice(text)

    def append_mctf_incorrect_choice(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have a choice without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have a choice without a question')
        last_question_or_delim.append_mctf_incorrect_choice(text)

    def append_multans_correct_choice(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have a choice without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have a choice without a question')
        last_question_or_delim.append_multans_correct_choice(text)

    def append_multans_incorrect_choice(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have a choice without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have a choice without a question')
        last_question_or_delim.append_multans_incorrect_choice(text)

    def append_essay(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have an essay response without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have an essay response without a question')
        last_question_or_delim.append_essay(text)

    def append_numerical(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if not self.questions_and_delims:
            raise Text2qtiError('Cannot have a numerical response without a question')
        last_question_or_delim = self.questions_and_delims[-1]
        if not isinstance(last_question_or_delim, Question):
            raise Text2qtiError('Cannot have a numerical response without a question')
        last_question_or_delim.append_numerical(text)

    def append_start_group(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if text:
            raise ValueError
        if self._current_group is not None:
            raise Text2qtiError('Question groups cannot be nested')
        if self.questions_and_delims:
            last_question_or_delim = self.questions_and_delims[-1]
            if isinstance(last_question_or_delim, Question):
                last_question_or_delim.finalize()
        group = Group()
        self._current_group = group
        self.questions_and_delims.append(GroupStart(group))

    def append_end_group(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if text:
            raise ValueError
        if self._current_group is None:
            raise Text2qtiError('No question group to end')
        if self.questions_and_delims:
            last_question_or_delim = self.questions_and_delims[-1]
            if isinstance(last_question_or_delim, Question):
                last_question_or_delim.finalize()
        self._current_group.finalize()
        self.questions_and_delims.append(GroupEnd(self._current_group))
        self._current_group = None

    def append_group_pick(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if self._current_group is None:
            raise Text2qtiError('No question group for setting properties')
        self._current_group.append_group_pick(text)

    def append_group_points_per_question(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if self._current_group is None:
            raise Text2qtiError('No question group for setting properties')
        self._current_group.append_group_points_per_question(text)

    def append_start_code(self, text: str):
        raise Text2qtiError('Invalid code block start')

    def append_end_code(self, text: str):
        raise Text2qtiError('Code block end missing code block start')

    def append_unknown(self, text: str):
        if self._next_question_attr:
            raise Text2qtiError('Expected question; question title and/or points were given but not used')
        if text and not text.isspace():
            match = start_missing_whitespace_re.match(text)
            if match:
                raise Text2qtiError(f'Missing whitespace after "{match.group().strip()}"')
            match = start_missing_content_re.match(text)
            if match:
                raise Text2qtiError(f'Missing content after "{match.group().strip()}"')
            raise Text2qtiError(f'Syntax error; unexpected text, or incorrect indentation for a wrapped paragraph:\n"{text}"')
