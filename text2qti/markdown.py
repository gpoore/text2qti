# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import markdown
import re
import urllib.parse
import typing
from .config import Config
from .err import Text2qtiError




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
    def __init__(self, config: Config):
        self.config = config


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
        '''
        latex_render_url = self.config['latex_render_url'].rstrip('/')
        latex_xml_escaped = self.xml_escape(latex)
        # Double url escaping is required
        latex_url_escaped = urllib.parse.quote(urllib.parse.quote(latex))
        return self.CANVAS_EQUATION_TEMPLATE.format(latex_render_url=latex_render_url,
                                                    latex_xml_escaped=latex_xml_escaped,
                                                    latex_url_escaped=latex_url_escaped)


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
            latex_number = f'{significand}\\times 10^{{{magnitude}}}'
        else:
            latex_number = number
        if in_math:
            return latex_number
        return self.latex_to_canvas_img(latex_number)


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
        return self.latex_to_canvas_img(latex_unit)


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
        return self.latex_to_canvas_img(latex)


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


    inline_code_pattern = r'(?P<code>(?<!`)(?P<code_delim>`+)(?!`).+?(?<!`)(?P=code_delim)(?!`))'
    inline_math_pattern = r'(?<!\$)\$(?P<math>[^ $][^$]*)(?<! )\$(?!\$)'
    inline_code_math_siunitx_re = re.compile('|'.join([inline_code_pattern,
                                                       inline_math_pattern,
                                                       siunitx_latex_macros_pattern]))

    def _inline_code_math_siunitx_dispatch(self, match: typing.Match[str]) -> str:
        '''
        Process LaTeX math and siunitx regex matches into Canvas image tags, while
        leaving inline code matches unchanged.
        '''
        lastgroup = match.lastgroup
        if lastgroup == 'code_delim':
            return match.group('code')
        if lastgroup == 'math':
            math = match.group('math')
            math = self.sub_siunitx_to_plain_latex(math, in_math=True)
            return self.latex_to_canvas_img(math)
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
        return self.inline_code_math_siunitx_re.sub(self._inline_code_math_siunitx_dispatch, string)


    markdown_processor = markdown.Markdown(extensions=['smarty', 'sane_lists'])

    def md_to_xml(self, markdown_string: str, strip_p_tags: bool=False) -> str:
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
