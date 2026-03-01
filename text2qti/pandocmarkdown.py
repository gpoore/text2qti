# -*- coding: utf-8 -*-
#
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#

import atexit
import hashlib
import json
import pathlib
import platform
import re
import subprocess
import time
import typing
from typing import Dict, Optional, Set
import urllib.parse
import zipfile


from .config import Config
from .err import Text2qtiError
from .version import __version__ as version
from . import pymd_pandoc_attr
from .postprocessor import CopyPreClassToCode



class Image(object):
    pass

class Markdown(object):
    r'''
    Convert text from Markdown to HTML.  Then escape the HTML for insertion
    into XML templates.

    During the Markdown to HTML conversion, LaTeX math is converted to Canvas
    img tags.  A subset of siunitx (https://ctan.org/pkg/siunitx) LaTeX macros
    are also supported, with limited features:  `\SI`, `\si`, and `\num`.
    siunitx macros are extracted via regex and then converted into plain
    LaTeX, since Canvas LaTeX support does not cover siunitx.
    '''
    def __init__(self, config: Optional[Config]=None):
        self.config = config
        self.images = dict()
        self._cache = dict()
        self._cache['pandoc_mathml'] = dict()
        self.postprocessors = [CopyPreClassToCode()]

    def finalize(self):
        pass

    XML_ESCAPES = (('&', '&amp;'),
                ('<', '&lt;'),
                ('>', '&gt;'),
                ('"', '&quot;'),
                ("'", '&apos;'))
    XML_ESCAPES_LESS_QUOTES = tuple(x for x in XML_ESCAPES if x[0] not in ("'", '"'))
    XML_ESCAPES_LESS_SQUOTE = tuple(x for x in XML_ESCAPES if x[0] != "'")
    XML_ESCAPES_LESS_DQUOTE = tuple(x for x in XML_ESCAPES if x[0] != '"')
    def xml_escape(self, string: str, *, squotes: bool=True, dquotes: bool=True) -> str:
        '''
        Escape a string for XML insertion, with options not to escape quotes.
        '''
        if squotes and dquotes:
            escapes = self.XML_ESCAPES
        elif squotes:
            escapes = self.XML_ESCAPES_LESS_DQUOTE
        elif dquotes:
            escapes = self.XML_ESCAPES_LESS_SQUOTE
        else:
            escapes = self.XML_ESCAPES_LESS_QUOTES
        for char, esc in escapes:
            string = string.replace(char, esc)
        return string


    def latex_to_pandoc_mathml(self, latex: str, input_template='{0}') -> str:
        '''
        Convert a LaTeX equation into MathML using Pandoc.
        '''
        data = self._cache['pandoc_mathml'].get(latex)
        if data is not None:
            mathml = data['mathml']
            data['unused_count'] = 0
        else:
            if platform.system() == 'Windows':
                # Prevent console from appearing for an instant
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            else:
                startupinfo = None
            try:
                proc = subprocess.run(['pandoc', '-f',
                                       'markdown+tex_math_dollars+latex_macros+backtick_code_blocks',
                                       '-t', 'html', '--mathml',
                                       '--no-highlight'],
                                      input=input_template.format(latex), encoding='utf8',
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      startupinfo=startupinfo,
                                      check=True)
            except FileNotFoundError as e:
                raise Text2qtiError(f'Could not find Pandoc:\n{e}')
            except subprocess.CalledProcessError as e:
                raise Text2qtiError(f'Running Pandoc failed:\n{e}')
            mathml = proc.stdout.strip()
            mathml = self.postprocess(mathml)
            self._cache['pandoc_mathml'][latex] = {
                'mathml': mathml,
                'unused_count': 0,
            }
        return mathml

    def postprocess(self, mathml: str) -> str:
        for processors in self.postprocessors:
            mathml = processors.postprocess(mathml)
        return mathml

    def md_to_html_xml(self, markdown_string: str, strip_p_tags: bool=False) -> str:
        '''
        Convert the Markdown in a string to HTML, then escape the HTML for
        embedding in XML.
        '''
        try:
            html = self.latex_to_pandoc_mathml(markdown_string)
        except Exception as e:
            raise Text2qtiError(f'Conversion from Markdown to HTML failed:\n{e}')
        if strip_p_tags:
            if html.startswith('<p>'):
                html = html[3:]
            if html.endswith('</p>'):
                html = html[:-4]
        xml = self.xml_escape(html, squotes=False, dquotes=False)
        return xml
