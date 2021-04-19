# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


'''
Pandoc-style attribute syntax for Python-Markdown.
Attribute support is currently limited to images.
See https://pandoc.org/MANUAL.html#images.

Inspired by https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/attr_list.py.
'''


from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from typing import List, Tuple
import re


IDENTIFIER_PATTERN = r'[A-Za-z][0-9A-Za-z_\-]+'
ID_PATTERN = rf'#{IDENTIFIER_PATTERN}'
CLASS_PATTERN = rf'\.{IDENTIFIER_PATTERN}'
KV_PATTERN = rf'{IDENTIFIER_PATTERN}=[0-9A-Za-z_\-%]+'
ATTR_PATTERN = (
    r'\{[ ]*(?!\})('
    rf'(?:{ID_PATTERN}(?=[ \}}]))?'
    rf'(?:{CLASS_PATTERN}(?=[ \}}])|{KV_PATTERN}(?=[ \}}])|[ ]+(?=[^ \}}]))*'
    r')[ ]*\}'
)

def _handle_id(scanner: re.Scanner, token: str) -> Tuple[str, str]:
    return '#', token[1:]

def _handle_class(scanner: re.Scanner, token: str) -> Tuple[str, str]:
    return '.', token[1:]

def _handle_key_value(scanner: re.Scanner, token: str) -> Tuple[str, str]:
    return token.split('=', 1)

_scanner = re.Scanner([
    (ID_PATTERN, _handle_id),
    (CLASS_PATTERN, _handle_class),
    (KV_PATTERN, _handle_key_value),
    (r'[ ]+', None),
])

def get_attrs(string: str) -> List[Tuple[str, str]]:
    '''
    Parse a string of attributes `<attrs>` that has already been extracted
    from a string of the form `{<attrs>}`.  Return a list of attribute tuples
    of the form `(<key>, <value>)`.
    '''
    results, remainder = _scanner.scan(string)
    return results


class PandocAttrTreeprocessor(Treeprocessor):
    ATTR_RE = re.compile(ATTR_PATTERN)
    def run(self, doc):
        for elem in doc.iter():
            if self.md.is_block_level(elem.tag):
                pass
            else:
                # inline, only for images currently
                if elem.tag == 'img' and elem.tail and elem.tail.startswith('{'):
                    match = self.ATTR_RE.match(elem.tail)
                    if match:
                        self.assign_attrs(elem, match.group(1))
                        elem.tail = elem.tail[match.end():]

    def assign_attrs(self, elem, attrs):
        '''
        Assign attrs to element.
        '''
        for k, v in get_attrs(attrs):
            if k == '#':
                elem.set('id', v)
            elif k == '.':
                elem_class = elem.get('class')
                if elem_class:
                    elem.set('class', f'{elem_class} {v}')
                else:
                    elem.set('class', v)
            else:
                elem_style = elem.get('style')
                if elem_style:
                    elem.set('style', f'{elem_style} {k}:{v};')
                else:
                    elem.set('style', f'{k}:{v};')


class PandocAttrExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(PandocAttrTreeprocessor(md), 'pandoc_attr', 8)
        md.registerExtension(self)


def makeExtension(**kwargs):
    return PandocAttrExtension(**kwargs)
