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
import pathlib
import re
from typing import List, Optional, Set, Union
from .config import Config
from .err import Text2qtiError
from .markdown import Markdown




# regex patterns for parsing quiz
start_patterns = {
    'question': r'\d+\.',
    'correct_choice': r'\*[a-zA-Z]\)',
    'incorrect_choice': r'[a-zA-Z]\)',
    'feedback': r'\.\.\.',
    'correct_feedback': r'\+',
    'incorrect_feedback': r'\-',
    'essay': r'___+',
    'quiz_title': r'[Qq]uiz [Tt]itle:',
    'quiz_description': r'[Qq]uiz [Dd]escription:',
}
no_content = set(['essay'])
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




class Choice(object):
    '''
    A choice for a question plus optional feedback.

    The id is based on a hash of both the question and the choice itself.
    The presence of feedback does not affect the id.
    '''
    def __init__(self, text: str, *,
                 correct: bool, question_hash_digest: bytes, md: Markdown):
        self.choice_raw = text
        self.choice_xml = md.md_to_xml(text)
        self.correct = correct
        self.feedback_raw: Optional[str] = None
        self.feedback_xml: Optional[str] = None
        # ID is based on hash of choice XML as well as question XML.  This
        # gives different IDs for identical choices in different questions.
        self.id = hashlib.blake2b(self.choice_xml.encode('utf8'), key=question_hash_digest).hexdigest()[:64]
        self.md = md

    def append_feedback(self, text: str):
        if self.feedback_raw is not None:
            raise Text2qtiError('Feedback can only be specified once')
        self.feedback_raw = text
        self.feedback_xml = self.md.md_to_xml(text)


class Question(object):
    '''
    A question, along with a list of possible choices and optional feedback of
    various types.
    '''
    def __init__(self, text: str, *, md: Markdown):
        # Question type is set once it is known.  For true/false or multiple
        # choice, this is done during .finalize(), once all choices are
        # available.  For essay, this is done as soon as essay response is
        # specified.
        self.type: Optional[str] = None
        self.title_raw = 'Question'
        self.title_xml = 'Question'
        self.question_raw = text
        self.question_xml = md.md_to_xml(text)
        self.choices: List[Choice] = []
        # The set for detecting duplicate choices uses the XML version of the
        # choices, to avoid the issue of multiple Markdown representations of
        # the same XML.
        self._choice_set: Set[str] = set()
        self.correct_choices = 0
        self.points_possible = 1
        self.feedback_raw: Optional[str] = None
        self.feedback_xml: Optional[str] = None
        self.correct_feedback_raw: Optional[str] = None
        self.correct_feedback_xml: Optional[str] = None
        self.incorrect_feedback_raw: Optional[str] = None
        self.incorrect_feedback_xml: Optional[str] = None
        h = hashlib.blake2b(self.question_xml.encode('utf8'))
        self.question_hash_digest = h.digest()
        self.id = h.hexdigest()[:64]
        self.md = md

    def append_correct_choice(self, text: str):
        if self.type is not None:
            raise Text2qtiError(f'Question type "{self.type}" does not support choices')
        choice = Choice(text, correct=True, question_hash_digest=self.question_hash_digest, md=self.md)
        if choice.choice_xml in self._choice_set:
            raise Text2qtiError('Duplicate choice for question')
        self._choice_set.add(choice.choice_xml)
        self.choices.append(choice)
        self.correct_choices += 1

    def append_incorrect_choice(self, text: str):
        if self.type is not None:
            raise Text2qtiError(f'Question type "{self.type}" does not support choices')
        choice = Choice(text, correct=False, question_hash_digest=self.question_hash_digest, md=self.md)
        if choice.choice_xml in self._choice_set:
            raise Text2qtiError('Duplicate choice for question')
        self._choice_set.add(choice.choice_xml)
        self.choices.append(choice)

    def append_feedback(self, text: str):
        if self.type is not None:
            raise Text2qtiError(f'Question type "{self.type}" does not support feedback')
        if not self.choices:
            if self.feedback_raw is not None:
                raise Text2qtiError('Feedback can only be specified once')
            self.feedback_raw = text
            self.feedback_xml = self.md.md_to_xml(text)
        else:
            self.choices[-1].append_feedback(text)

    def append_correct_feedback(self, text: str):
        if self.type is not None:
            raise Text2qtiError(f'Question type "{self.type}" does not support feedback')
        if self.choices:
            raise Text2qtiError('Correct feedback can only be specified for questions, not choices')
        if self.correct_feedback_raw is not None:
            raise Text2qtiError('Feedback can only be specified once')
        self.correct_feedback_raw = text
        self.correct_feedback_xml = self.md.md_to_xml(text)

    def append_incorrect_feedback(self, text: str):
        if self.type is not None:
            raise Text2qtiError(f'Question type "{self.type}" does not support feedback')
        if self.choices:
            raise Text2qtiError('Incorrect feedback can only be specified for questions, not choices')
        if self.incorrect_feedback_raw is not None:
            raise Text2qtiError('Feedback can only be specified once')
        self.incorrect_feedback_raw = text
        self.incorrect_feedback_xml = self.md.md_to_xml(text)

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
        if self.choices:
            raise Text2qtiError(f'Question type "{self.type}" does not support choices')
        if any(x is not None for x in (self.feedback_raw, self.correct_feedback_raw, self.incorrect_feedback_raw)):
            raise Text2qtiError(f'Question type "{self.type}" does not support feedback')
        self.type = 'essay_question'

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
        self.source_name = '<string>' if source_name is None else source_name
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
        self.description_xml = ''
        self.questions: List[Question] = []
        # The set for detecting duplicate questions uses the XML version of
        # the question, to avoid the issue of multiple Markdown
        # representations of the same XML.
        self.question_set: Set[str] = set()
        self.md = Markdown(config)

        parse_actions = {}
        for k in start_patterns:
            parse_actions[k] = getattr(self, f'append_{k}')
        parse_actions[None] = self.append_unknown
        # Enhancement: revise to allow elements to span multiple paragraphs
        n_line_iter = iter(x for x in enumerate(string.splitlines()))
        n, line = next(n_line_iter, (0, None))
        lookahead = True
        while line is not None:
            match = start_re.match(line)
            if match:
                action = match.lastgroup
                text = line[match.end():].strip()
                if action not in no_content:
                    wrapped_expanded_indent = ' '*len(line[:len(line)-len(text)].expandtabs(4))
                    n, line = next(n_line_iter, (0, None))
                    line_expandtabs = line.expandtabs(4) if line is not None else None
                    lookahead = True
                    while (line is not None and
                            line_expandtabs.startswith(wrapped_expanded_indent) and
                            line_expandtabs[len(wrapped_expanded_indent):len(wrapped_expanded_indent)+1] not in ('', ' ', '\t')):
                        if not text.endswith(' '):
                            text += ' '
                        text += line_expandtabs[len(wrapped_expanded_indent):]
                        n, line = next(n_line_iter, (0, None))
                        line_expandtabs = line.expandtabs(4) if line is not None else None
            else:
                action = None
                text = line
            try:
                parse_actions[action](text)
            except Text2qtiError as e:
                if lookahead:
                    raise Text2qtiError(f'In {self.source_name} on line {n}:\n{e}')
                raise Text2qtiError(f'In {self.source_name} on line {n+1}:\n{e}')
            if not lookahead:
                n, line = next(n_line_iter, (0, None))
            lookahead = False
        if not self.questions:
            raise Text2qtiError('No questions were found')
        try:
            self.questions[-1].finalize()
        except Text2qtiError as e:
            raise Text2qtiError(f'In {self.source_name} on line {len(string.splitlines())}:\n{e}')

        self.points_possible = sum(q.points_possible for q in self.questions)

        h = hashlib.blake2b()
        for digest in sorted(x.question_hash_digest for x in self.questions):
            h.update(digest)
        self.id = h.hexdigest()[:64]

    def append_quiz_title(self, text: str):
        if self.title_raw is not None:
            raise Text2qtiError('Quiz title has already been given')
        if self.questions:
            raise Text2qtiError('Must give quiz title before questions')
        if self.description_raw is not None:
            raise Text2qtiError('Must give quiz title before quiz description')
        self.title_raw = text
        self.title_xml = self.md.md_to_xml(text, strip_p_tags=True)

    def append_quiz_description(self, text: str):
        if self.description_raw is not None:
            raise Text2qtiError('Quiz description has already been given')
        if self.questions:
            raise Text2qtiError('Must give quiz description before questions')
        self.description_raw = text
        self.description_xml = self.md.md_to_xml(text)

    def append_question(self, text: str):
        if self.questions:
            self.questions[-1].finalize()
        question = Question(text, md=self.md)
        if question.question_xml in self.question_set:
            raise Text2qtiError('Duplicate question')
        self.question_set.add(question.question_xml)
        self.questions.append(question)

    def append_correct_choice(self, text: str):
        if not self.questions:
            raise Text2qtiError('Cannot have a choice without a question')
        self.questions[-1].append_correct_choice(text)

    def append_incorrect_choice(self, text: str):
        if not self.questions:
            raise Text2qtiError('Cannot have a choice without a question')
        self.questions[-1].append_incorrect_choice(text)

    def append_feedback(self, text: str):
        if not self.questions:
            raise Text2qtiError('Cannot have feedback without a question')
        self.questions[-1].append_feedback(text)

    def append_correct_feedback(self, text: str):
        if not self.questions:
            raise Text2qtiError('Cannot have feedback without a question')
        self.questions[-1].append_correct_feedback(text)

    def append_incorrect_feedback(self, text: str):
        if not self.questions:
            raise Text2qtiError('Cannot have feedback without a question')
        self.questions[-1].append_incorrect_feedback(text)

    def append_essay(self, text: str):
        if not self.questions:
            raise Text2qtiError('Cannot have an essay response without a question')
        self.questions[-1].append_essay(text)

    def append_unknown(self, text: str):
        if text and not text.isspace():
            match = start_missing_whitespace_re.match(text)
            if match:
                raise Text2qtiError(f'Missing whitespace after "{match.group().strip()}"')
            match = start_missing_content_re.match(text)
            if match:
                raise Text2qtiError(f'Missing content after "{match.group().strip()}"')
            raise Text2qtiError('Syntax error; unexpected text, or incorrect indentation for a wrapped paragraph')
