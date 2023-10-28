# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2021, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import argparse
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import textwrap
from .version import __version__ as version
from .err import Text2qtiError
from .config import Config
from .quiz import Quiz
from .qti import QTI
from .export import quiz_to_pandoc




def main():
    '''
    text2qti executable main function.
    '''
    parser = argparse.ArgumentParser(prog='text2qti')
    parser.set_defaults(func=lambda x: parser.print_help())
    parser.add_argument('--version', action='version', version=f'text2qti {version}')
    parser.add_argument('--latex-render-url',
                        help='URL for rendering LaTeX equations')
    parser.add_argument('--run-code-blocks', action='store_const', const=True,
                        help='Allow special code blocks to be executed and insert their output (off by default for security)')
    parser.add_argument('--pandoc-mathml', action='store_const', const=True,
                        help='Convert LaTeX math to MathML using Pandoc (this will create a cache file "_text2qti_cache.zip" in the quiz file directory)')
    soln_group = parser.add_mutually_exclusive_group()
    soln_group.add_argument('--solutions', action='append', metavar='SOLUTIONS_FILE',
                            help='Save solutions in Pandoc Markdown (.md), PDF (.pdf), or HTML (.html) format, and also create a QTI file. '
                                 'Can be used multiple times to export multiple formats. '
                                 'Pandoc Markdown output is only suitable for use with LaTeX or HTML; PDF output requires Pandoc plus LaTeX.')
    soln_group.add_argument('--only-solutions', action='append', metavar='SOLUTIONS_FILE',
                            help='Save solutions in Pandoc Markdown (.md), PDF (.pdf), or HTML (.html) format, but do not create a QTI file. '
                                 'Can be used multiple times to export multiple formats. '
                                 'Pandoc Markdown output is only suitable for use with LaTeX or HTML; PDF output requires Pandoc plus LaTeX. '
                                 'With this option, solutions and QTI may differ if executable code blocks generate problems using random numbers. '
                                 'Consider creating solutions and QTI together, or setting a seed for the random number generator so it is reproducible.')
    parser.add_argument('file',
                        help='File to convert from text to QTI')
    args = parser.parse_args()

    config = Config()
    config.load()
    if not config.loaded_config_file and sys.stdout.isatty() and sys.stdin.isatty():
        latex_render_url = input(textwrap.dedent('''\
            It looks like text2qti has not been installed on this machine
            before.  Would you like to set a custom LaTeX rendering URL?  This
            should typically not be necessary with recent version of Canvas.
            If no, press ENTER to use the default ("/equation_images/").  If
            yes, provide the URL and press ENTER.

            If you use Canvas, the URL will be something like
                https://<institution>.instructure.com/equation_images/
            or
                https://canvas.<institution>.edu/equation_images/
            with "<institution>" replaced by the name or abbreviation for
            your institution.  You can determine "<institution>" by logging
            into Canvas and then looking in the browser address bar for
            something like "<institution>.instructure.com/" or
            "canvas.<institution>.edu/".  If the address is similar to the
            second form, you may need to change the domain from ".edu" to
            the appropriate value for your institution.

            If you do not use Canvas or software with a compatible LaTeX
            rendering URL, you may still be able to use LaTeX via the
            command-line option "--pandoc-mathml".

            LaTeX rendering URL:  '''))
        latex_render_url = latex_render_url.strip()
        if latex_render_url:
            config['latex_render_url'] = latex_render_url
            config.save()
    if args.latex_render_url is not None:
        config['latex_render_url'] = args.latex_render_url
    if args.run_code_blocks is not None:
        config['run_code_blocks'] = args.run_code_blocks
    if args.pandoc_mathml is not None:
        config['pandoc_mathml'] = args.pandoc_mathml

    file_path = pathlib.Path(args.file).expanduser()
    file_path_abs = file_path.absolute()
    try:
        text = file_path.read_text(encoding='utf-8-sig')  # Handle BOM for Windows
    except FileNotFoundError:
        raise Text2qtiError(f'File "{file_path}" does not exist')
    except PermissionError as e:
        raise Text2qtiError(f'File "{file_path}" cannot be read due to permission error:\n{e}')
    except UnicodeDecodeError as e:
        raise Text2qtiError(f'File "{file_path}" is not encoded in valid UTF-8:\n{e}')

    cwd = pathlib.Path.cwd()
    if args.solutions:
        qti_path = pathlib.Path(f'{file_path.stem}.zip')
        solutions_paths = [pathlib.Path(x).expanduser().absolute() for x in args.solutions]
    elif args.only_solutions:
        qti_path = None
        solutions_paths = [pathlib.Path(x).expanduser().absolute() for x in args.only_solutions]
    else:
        qti_path = pathlib.Path(f'{file_path.stem}.zip')
        solutions_paths = None
    if solutions_paths is not None:
        if file_path_abs in solutions_paths:
            raise Text2qtiError(f'Solutions cannot overwrite quiz file "{file_path}"')
        if not all(x.suffix.lower() in ('.md', '.markdown', '.pdf', '.html') for x in solutions_paths):
            invalid_extensions = ', '.join(x.suffix for x in solutions_paths if x.suffix not in ('.md', '.markdown', '.pdf', '.html'))
            raise Text2qtiError(f'Unsupported export format(s) {invalid_extensions} for solutions; use .md, .markdown, .pdf, or .html')
    os.chdir(file_path.parent)
    try:
        # Quiz and any solutions should only be generated once each so that
        # any randomization is only invoked once.
        quiz = Quiz(text, config=config, source_name=file_path.as_posix())
        if solutions_paths is not None:
            solutions_text = quiz_to_pandoc(quiz, solutions=True)
            for solutions_path in solutions_paths:
                if solutions_path.suffix.lower() == '.pdf':
                    if not shutil.which('pandoc'):
                        raise Text2qtiError('Exporting solutions in PDF format requires Pandoc (https://pandoc.org/)')
                    if not shutil.which('pdflatex'):
                        raise Text2qtiError('Exporting solutions in PDF format requires LaTeX (https://www.tug.org/texlive/ or https://miktex.org/)')
                    if platform.system() == 'Windows':
                        cmd = [shutil.which('pandoc'), '-f', 'markdown', '-o', str(solutions_path)]
                    else:
                        cmd = ['pandoc', '-f', 'markdown', '-o', str(solutions_path)]
                    try:
                        proc = subprocess.run(
                            cmd,
                            input=solutions_text,
                            capture_output=True,
                            check=True,
                            encoding='utf8'
                        )
                    except subprocess.CalledProcessError as e:
                        raise Text2qtiError(f'Pandoc failed:\n{"-"*78}\n{e}\n{"-"*78}')
                elif solutions_path.suffix.lower() == '.html':
                    if not shutil.which('pandoc'):
                        raise Text2qtiError('Exporting solutions in HTML format requires Pandoc (https://pandoc.org/)')
                    if platform.system() == 'Windows':
                        cmd = [shutil.which('pandoc'), '-f', 'markdown', '-o', str(solutions_path), '--mathjax', '-s']
                    else:
                        cmd = ['pandoc', '-f', 'markdown', '-o', str(solutions_path), '--mathjax', '-s']
                    try:
                        proc = subprocess.run(
                            cmd,
                            input=solutions_text,
                            capture_output=True,
                            check=True,
                            encoding='utf8'
                        )
                    except subprocess.CalledProcessError as e:
                        raise Text2qtiError(f'Pandoc failed:\n{"-"*78}\n{e}\n{"-"*78}')
                elif solutions_path.suffix.lower() in ('.md', '.markdown'):
                    solutions_path.write_text(solutions_text, encoding='utf8')
                else:
                    raise ValueError
        if qti_path is not None:
            qti = QTI(quiz)
            qti.save(qti_path)
    finally:
        os.chdir(cwd)
