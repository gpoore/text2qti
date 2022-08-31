# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
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

import markdown
# Markdown extensions are imported and initialized explicitly to ensure that
# pyinstaller identifies them.
import markdown.extensions
import markdown.extensions.smarty
import markdown.extensions.sane_lists
import markdown.extensions.def_list
import markdown.extensions.fenced_code
import markdown.extensions.footnotes
import markdown.extensions.tables
import markdown.extensions.md_in_html
from markdown.inlinepatterns import ImageInlineProcessor, IMAGE_LINK_RE

from .config import Config
from .err import Text2qtiError
from .version import __version__ as version
from . import pymd_pandoc_attr


md_extensions = [
    markdown.extensions.smarty.makeExtension(),
    markdown.extensions.sane_lists.makeExtension(),
    markdown.extensions.def_list.makeExtension(),
    markdown.extensions.fenced_code.makeExtension(),
    markdown.extensions.footnotes.makeExtension(),
    markdown.extensions.tables.makeExtension(),
    markdown.extensions.md_in_html.makeExtension(),
    pymd_pandoc_attr.makeExtension(),
]




class Image(object):
    '''
    Raw image data for quiz insertion.
    '''
    def __init__(self, name: str, data: bytes):
        self.name = name
        self.data = data
        h = hashlib.blake2b()
        h.update(data)
        self.id = h.hexdigest()[:64]

    @property
    def src_path(self):
        return f'%24IMS-CC-FILEBASE%24/images/{urllib.parse.quote(self.name)}'

    @property
    def qti_zip_path(self):
        return f'images/{self.name}'

    @property
    def qti_xml_path(self):
        return f'images/{urllib.parse.quote(self.name)}'




class Text2qtiImagePattern(ImageInlineProcessor):
    '''
    Custom image processor for Python-Markdown that modifies local image
    paths to their final QTI form and also accumulates all image data for QTI
    inclusion.
    '''
    def __init__(self, pattern_re, markdown_md, text2qti_md):
        super().__init__(pattern_re, markdown_md)
        self.text2qti_md = text2qti_md

    def handleMatch(self, match, data):
        node, start, end = super().handleMatch(match, data)
        src = node.attrib.get('src')
        if src and not any(src.startswith(x) for x in ('http://', 'https://')):
            src_path = pathlib.Path(src).expanduser()
            try:
                data = src_path.read_bytes()
            except FileNotFoundError:
                raise Text2qtiError(f'File "{src_path}" does not exist')
            except PermissionError as e:
                raise Text2qtiError(f'File "{src_path}" cannot be read due to permission error:\n{e}')
            image = Image(src_path.name, data)
            if image.id in self.text2qti_md.images:
                image = self.text2qti_md.images[image.id]
            else:
                if image.name in self.text2qti_md.image_name_set:
                    n = 8
                    while image.name in self.text2qti_md.image_name_set:
                        image.name = f'{src_path.stem}_{image.id[:n]}{src_path.suffix}'
                        n *= 2
                        if n >= len(image.id)*2:
                            raise Text2qtiError('Hash collision occurred during image deduplication')
                self.text2qti_md.image_name_set.add(image.name)
                self.text2qti_md.images[image.id] = image
            node.attrib['src'] = image.src_path
        return node, start, end




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

        markdown_processor = markdown.Markdown(extensions=md_extensions)
        markdown_image_processor = Text2qtiImagePattern(IMAGE_LINK_RE, markdown_processor, self)
        markdown_processor.inlinePatterns.register(markdown_image_processor, 'image_link', 150)
        self.markdown_processor = markdown_processor

        self.images: Dict[str, Image] = {}
        self.image_name_set: Set[str] = set()

        if config is None:
            self.latex_to_qti = self._latex_to_qti_unconfigured
        elif config['pandoc_mathml']:
            self.latex_to_qti = self.latex_to_pandoc_mathml
            self._prep_cache()
        else:
            self.latex_to_qti = self.latex_to_canvas_img


    def finalize(self):
        if self.config is not None and self.config['pandoc_mathml']:
            self._save_cache()
            self._cache_lock_path.unlink()


    def _latex_to_qti_unconfigured(self, latex: str):
        raise Text2qtiError('Cannot convert LaTeX to QTI unless Markdown configuration is provided')


    def _prep_cache(self):
        self._cache_path = pathlib.Path('_text2qti_cache.zip')
        self._cache_lock_path = pathlib.Path('_text2qti_cache.lock')

        max_lock_wait = 2
        lock_check_interval = 0.1
        lock_time = 0
        while True:
            try:
                self._cache_lock_path.touch(exist_ok=False)
            except FileExistsError:
                if lock_time > max_lock_wait:
                    raise Text2qtiError('The text2qti cache is locked; this usually means that another instance of '
                                        'text2qti is already running and you should try again later')
                time.sleep(lock_check_interval)
                lock_time += lock_check_interval
            else:
                break
        def final_cache_cleanup():
            try:
                self._cache_lock_path.unlink()
            except FileNotFoundError:
                pass
        atexit.register(final_cache_cleanup)

        default_cache = {
            'version': version,
            'pandoc_mathml': {}
        }
        try:
            with zipfile.ZipFile(str(self._cache_path)) as zf:
                with zf.open('cache.json') as f:
                    cache = json.load(f)
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            cache = default_cache
        else:
            if not isinstance(cache, dict) or cache.get('version') != version:
                cache = default_cache
        for v in cache['pandoc_mathml'].values():
            v['unused_count'] += 1
        self._cache = cache


    def _save_cache(self):
        self._cache['pandoc_mathml'] = {k: v for k, v in self._cache['pandoc_mathml'].items()
                                       if v['unused_count'] <= 10}
        with zipfile.ZipFile(str(self._cache_path), 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('cache.json', json.dumps(self._cache))


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


    CANVAS_EQUATION_TEMPLATE = '<img class="equation_image" title="{latex_xml_escaped}" src="{latex_render_url}/{latex_url_escaped}" alt="LaTeX: {latex_xml_escaped}" data-equation-content="{latex_xml_escaped}">'

    def latex_to_canvas_img(self, latex: str) -> str:
        '''
        Convert a LaTeX equation into an img tag suitable for Canvas.

        Requires an institutional LaTeX equation rendering URL.  The URL is stored
        in the text2qti config file or can be passed with flag --latex-render-url.
        It will typically be of the form

            https://<institution>.instructure.com/equation_images/

        or

            https://canvas.<institution>.edu/equation_images/
        '''
        latex_render_url = self.config['latex_render_url'].rstrip('/')
        latex_xml_escaped = self.xml_escape(latex)
        # Double url escaping is required
        latex_url_escaped = urllib.parse.quote(urllib.parse.quote(latex))
        return self.CANVAS_EQUATION_TEMPLATE.format(latex_render_url=latex_render_url,
                                                    latex_xml_escaped=latex_xml_escaped,
                                                    latex_url_escaped=latex_url_escaped)


    def latex_to_pandoc_mathml(self, latex: str) -> str:
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
                proc = subprocess.run(['pandoc', '-f', 'markdown', '-t', 'html', '--mathml'],
                                      input='${0}$'.format(latex), encoding='utf8',
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      startupinfo=startupinfo,
                                      check=True)
            except FileNotFoundError as e:
                raise Text2qtiError(f'Could not find Pandoc:\n{e}')
            except subprocess.CalledProcessError as e:
                raise Text2qtiError(f'Running Pandoc failed:\n{e}')
            mathml = proc.stdout.strip()
            if mathml.startswith('<p>'):
                mathml = mathml[len('<p>'):]
            if mathml.endswith('</p>'):
                mathml = mathml[:-len('</p>')]
            self._cache['pandoc_mathml'][latex] = {
                'mathml': mathml,
                'unused_count': 0,
            }
        return mathml


    siunitx_num_number_re = re.compile(r'[+-]?(?:0|(?:[1-9][0-9]*(?:\.[0-9]+)?|0?\.[0-9]+)(?:[eE][+-]?[1-9][0-9]*)?)$')

    def siunitx_num_to_plain_latex(self, number: str, in_math: bool=False) -> str:
        r'''
        Convert a basic subset of siunitx \num{<number>} syntax into plain LaTeX.
        If `in_math` is true, covert the plain LaTeX to a Canvas img tag.
        '''
        number = number.strip()
        if number.startswith('.'):
            number = f'0{number}'
        if not self.siunitx_num_number_re.match(number):
            raise Text2qtiError(f'Invalid or unsupported LaTeX number "{number}"')
        number = number.lower()
        if 'e' in number:
            significand, magnitude = number.split('e', 1)
            magnitude = magnitude.lstrip('+')
            latex_number = f'{significand}\\times 10^{{{magnitude}}}'
        else:
            latex_number = number
        if in_math:
            return latex_number
        return self.latex_to_qti(latex_number)


    def siunitx_si_to_plain_latex(self, unit: str, in_math: bool=False) -> str:
        r'''
        Convert a basic subset of siunitx \si{<unit>} syntax into plain LaTeX.
        If `in_math` is true, covert the plain LaTeX to a Canvas img tag.
        '''
        unit = unit.strip()
        unit_list = []
        unit_iter = iter(unit)
        char = next(unit_iter, '')
        while True:
            if char == '' or char == ' ':
                pass
            elif char == '.':
                unit_list.append(r'\!\cdot\!')  # Alternative:  r'\,'
            elif char == '^':
                char = next(unit_iter, '')
                if char.isdigit():
                    unit_list.append(f'^{{{char}}}')
                elif char == '\\':
                    unit_list.append('^')
                    continue
                else:
                    raise Text2qtiError(f'Invalid or unsupported LaTeX unit "{unit}"')
            elif char == '/':
                unit_list.append(r'/')  # Alternative: r'\big/'
            elif char == '\\':
                macro = char
                char = next(unit_iter, '')
                while char.isalpha():
                    macro += char
                    char = next(unit_iter, '')
                if macro == r'\degree':
                    unit_list.append(r'^\circ')
                elif macro == r'\celsius':
                    unit_list.append(r'^\circ\textrm{C}')
                elif macro == r'\fahrenheit':
                    unit_list.append(r'^\circ\textrm{F}')
                elif macro == r'\ohm':
                    unit_list.append(r'\Omega')
                elif macro == r'\micro':
                    # Ideally, this would be an upright rather than slanted mu
                    unit_list.append(r'\mu')
                else:
                    unit_list.append(macro)
                continue
            elif char.isalpha():
                unit_list.append(r'\text{')
                unit_list.append(char)
                char = next(unit_iter, '')
                while char.isalpha():
                    unit_list.append(char)
                    char = next(unit_iter, '')
                unit_list.append('}')
                continue
            else:
                raise Text2qtiError(f'Invalid or unsupported LaTeX unit "{unit}"')
            try:
                char = next(unit_iter)
            except StopIteration:
                break
        latex_unit = '{' + ''.join(unit_list) + '}'  # wrapping {} may prevent line breaks
        if in_math:
            return latex_unit
        return self.latex_to_qti(latex_unit)


    def siunitx_SI_to_plain_latex(self, number: str, unit: str, in_math: bool=False) -> str:
        r'''
        Convert a basic subset of siunitx \SI{<number>}{<unit>} syntax into plain
        LaTeX.  If `in_math` is true, covert the plain LaTeX to a Canvas img tag.
        '''
        latex_number = self.siunitx_num_to_plain_latex(number, in_math=True)
        latex_unit = self.siunitx_si_to_plain_latex(unit, in_math=True)
        if latex_unit.startswith(r'^\circ'):
            unit_sep = ''
        else:
            unit_sep = r'\,'  # Alternative: `\>`
        latex = f'{latex_number}{unit_sep}{latex_unit}'
        if in_math:
            return latex
        return self.latex_to_qti(latex)


    siunitx_num_macro_pattern = r'\\num\{(?P<num_number>[^{}]+)\}'
    siunitx_si_macro_pattern = r'\\si\{(?P<si_unit>[^{}]+)\}'
    siunitx_SI_macro_pattern = r'\\SI\{(?P<SI_number>[^{}]+)\}\{(?P<SI_unit>[^{}]+)\}'
    siunitx_latex_macros_pattern = '|'.join([siunitx_num_macro_pattern, siunitx_si_macro_pattern, siunitx_SI_macro_pattern])
    siunitx_latex_macros_re = re.compile(siunitx_latex_macros_pattern)

    def _siunitx_dispatch(self, match: typing.Match[str], in_math: bool) -> str:
        '''
        Convert an siunitx regex match to plain LaTeX.  If `in_math` is true,
        covert the plain LaTeX to a Canvas img tag.
        '''
        lastgroup = match.lastgroup
        if lastgroup == 'SI_unit':
            return self.siunitx_SI_to_plain_latex(match.group('SI_number'), match.group('SI_unit'), in_math)
        if lastgroup == 'num_number':
            return self.siunitx_num_to_plain_latex(match.group('num_number'), in_math)
        if lastgroup == 'si_unit':
            return self.siunitx_si_to_plain_latex(match.group('si_unit'), in_math)
        raise ValueError

    def sub_siunitx_to_plain_latex(self, string: str, in_math: bool=False) -> str:
        '''
        Convert all siunitx macros in a string to plain LaTeX.  If `in_math` is
        true, covert the plain LaTeX to a Canvas img tag.
        '''
        return self.siunitx_latex_macros_re.sub(lambda match: self._siunitx_dispatch(match, in_math), string)


    escape = r'(?P<escape>\\\$)'
    skip = r'(?P<skip>\\.|\\\n|\$\$+(?!\$))'
    html_comment_pattern = r'(?P<html_comment><!--(?:.|\n)*?-->)'
    block_code_pattern = (
        r'^(?P<block_code>'
        r'(?P<indent>[ \t]*)(?P<block_code_delim>```+(?!`)|~~~+(?!~)).*?\n'
        r'(?:[ \t]*\n|(?P=indent).*\n)*?'
        r'(?P=indent)(?P=block_code_delim)[ \t]*(?:\n|$)'
        r')'
    )
    inline_code_pattern = (
        r'(?P<inline_code>'
        r'(?P<inline_code_delim>`+(?!`))'
        r'(?:.|\n[ \t]*(?![ \t\n]))+?'
        r'(?<!`)(?P=inline_code_delim)(?!`)'
        r')'
    )
    inline_math_pattern = (
        r'\$(?=[^ \t\n])'
        r'(?P<math>(?:[^$\n\\]|\\.|\\?\n[ \t]*(?:[^ \t\n$]))+)'
        r'(?<![ \t\n])\$(?!\$)'
    )
    patterns = '|'.join([
        block_code_pattern,
        siunitx_latex_macros_pattern,
        escape,
        skip,
        html_comment_pattern,
        inline_code_pattern,
        inline_math_pattern,
    ])
    skip_or_html_comment_or_code_math_siunitx_re = re.compile(patterns, re.MULTILINE)

    def _html_comment_or_inline_code_math_siunitx_dispatch(self, match: typing.Match[str]) -> str:
        '''
        Process LaTeX math and siunitx regex matches into Canvas image tags,
        while stripping HTML comments and leaving things like backslash
        escapes and code unchanged.
        '''
        lastgroup = match.lastgroup
        if lastgroup == 'html_comment':
            return ''
        if lastgroup == 'escape':
            return match.group('escape')[1:]
        if lastgroup == 'skip':
            return match.group('skip')
        if lastgroup == 'block_code':
            return match.group('block_code')
        if lastgroup == 'inline_code':
            return match.group('inline_code')
        if lastgroup == 'math':
            math = match.group('math')
            math = math.replace('\n ', ' ').replace('\n', ' ')
            math = self.sub_siunitx_to_plain_latex(math, in_math=True)
            return self.latex_to_qti(math)
        if lastgroup == 'SI_unit':
            return self.siunitx_SI_to_plain_latex(match.group('SI_number'), match.group('SI_unit'), in_math=False)
        if lastgroup == 'num_number':
            return self.siunitx_num_to_plain_latex(match.group('num_number'), in_math=False)
        if lastgroup == 'si_unit':
            return self.siunitx_si_to_plain_latex(match.group('si_unit'), in_math=False)
        raise ValueError

    def sub_math_siunitx_to_canvas_img(self, string: str) -> str:
        '''
        Convert all siunitx macros in a string into plain LaTeX.  Then convert
        this LaTeX and all $-delimited LaTeX into Canvas img tags.
        '''
        return self.skip_or_html_comment_or_code_math_siunitx_re.sub(self._html_comment_or_inline_code_math_siunitx_dispatch, string)

    def md_to_html_xml(self, markdown_string: str, strip_p_tags: bool=False) -> str:
        '''
        Convert the Markdown in a string to HTML, then escape the HTML for
        embedding in XML.
        '''
        markdown_string_processed_latex = self.sub_math_siunitx_to_canvas_img(markdown_string)
        try:
            html = self.markdown_processor.reset().convert(markdown_string_processed_latex)
        except Exception as e:
            raise Text2qtiError(f'Conversion from Markdown to HTML failed:\n{e}')
        if strip_p_tags:
            if html.startswith('<p>'):
                html = html[3:]
            if html.endswith('</p>'):
                html = html[:-4]
        xml = self.xml_escape(html, squotes=False, dquotes=False)
        return xml

    def _md_to_pandoc_dispatch(self, match: typing.Match[str],
                                     _passthrough=set(['escape', 'skip', 'block_code', 'inline_code'])) -> str:
        '''
        Process LaTeX math and siunitx regex matches into Pandoc Markdown,
        while stripping HTML comments and leaving things like backslash
        escapes and code unchanged.
        '''
        lastgroup = match.lastgroup
        if lastgroup == 'html_comment':
            return ''
        if lastgroup in _passthrough:
            return match.group(lastgroup)
        if lastgroup == 'math':
            math = match.group('math')
            math = math.replace('\n ', ' ').replace('\n', ' ')
            math = self.sub_siunitx_to_plain_latex(math, in_math=True)
            return '${0}$'.format(math)
        if lastgroup == 'SI_unit':
            return '${0}$'.format(self.siunitx_SI_to_plain_latex(match.group('SI_number'), match.group('SI_unit'), in_math=True))
        if lastgroup == 'num_number':
            return '${0}$'.format(self.siunitx_num_to_plain_latex(match.group('num_number'), in_math=True))
        if lastgroup == 'si_unit':
            return '${0}$'.format(self.siunitx_si_to_plain_latex(match.group('si_unit'), in_math=True))
        raise ValueError

    def md_to_pandoc(self, string: str) -> str:
        '''
        Convert Markdown from a quiz into a form suitable for Pandoc Markdown.

        Convert all siunitx macros in a string into plain LaTeX guaranteed to
        be wrapped in `$`.  This can be processed into multiple formats by
        Pandoc.
        '''
        return self.skip_or_html_comment_or_code_math_siunitx_re.sub(self._md_to_pandoc_dispatch, string)
