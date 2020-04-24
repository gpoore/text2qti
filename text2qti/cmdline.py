# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import argparse
import os
import pathlib
import textwrap
from .version import __version__ as version
from .err import Text2qtiError
from .config import Config
from .quiz import Quiz
from .qti import QTI




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
    parser.add_argument('file',
                        help='File to convert from text to QTI')
    args = parser.parse_args()

    config = Config()
    config.load()
    if not config.loaded_config_file:
        latex_render_url = input(textwrap.dedent('''\
            It looks like text2qti has not been installed on this machine
            before.  Would you like to set a default LaTeX rendering URL?  If
            no, press ENTER.  If yes, provide the URL and press ENTER.

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

            LaTeX rendering URL:  '''))
        latex_render_url = latex_render_url.strip()
        if latex_render_url:
            config['latex_render_url'] = latex_render_url
            config.save()
    if args.latex_render_url is not None:
        config['latex_render_url'] = args.latex_render_url
    if args.run_code_blocks is not None:
        config['run_code_blocks'] = args.run_code_blocks

    file_path = pathlib.Path(args.file).expanduser()
    try:
        text = file_path.read_text(encoding='utf-8-sig')  # Handle BOM for Windows
    except FileNotFoundError:
        raise Text2qtiError(f'File "{file_path}" does not exist')
    except PermissionError as e:
        raise Text2qtiError(f'File "{file_path}" cannot be read due to permission error:\n{e}')
    except UnicodeDecodeError as e:
        raise Text2qtiError(f'File "{file_path}" is not encoded in valid UTF-8:\n{e}')

    cwd = pathlib.Path.cwd()
    os.chdir(file_path.parent)
    try:
        quiz = Quiz(text, config=config, source_name=file_path.as_posix())
        qti = QTI(quiz)
        qti.save(file_path.parent / f'{file_path.stem}.zip')
    finally:
        os.chdir(cwd)
