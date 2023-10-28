# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import bespon
import pathlib
import textwrap
import warnings
from .err import Text2qtiError




class Config(dict):
    '''
    Dict-like configuration that raises an error when invalid keys are set.
    If `.load()` is invoked, a config file in BespON format is loaded if it
    exists, and otherwise is created if possible.
    '''
    def __init__(self, *args, **kwargs):
        self.loaded_config_file = False
        self.update(self._defaults)
        self.update(dict(*args, **kwargs))

    _defaults = {
        'latex_render_url': '/equation_images/',
        'pandoc_mathml': False,
        'run_code_blocks': False,
    }
    _key_check = {
        'latex_render_url': lambda x: isinstance(x, str),
        'pandoc_mathml': lambda x: isinstance(x, bool),
        'run_code_blocks': lambda x: isinstance(x, bool),
    }
    _config_path = pathlib.Path('~/.text2qti.bespon').expanduser()

    def __setitem__(self, key, value):
        if key not in self._key_check:
            raise Text2qtiError(f'Invalid configuration option "{key}"')
        if not self._key_check[key](value):
            raise Text2qtiError(f'Configuration option "{key}" has invalid value "{value}"')
        super().__setitem__(key, value)


    def update(self, other: dict):
        '''
        Send all keys through __setitem__ so that they are checked for
        validity.
        '''
        for k, v in other.items():
            self[k] = v


    def __missing__(self, key):
        if self.loaded_config_file:
            raise Text2qtiError(textwrap.dedent(f'''\
                Configuration option "{key}" has not been set.
                Open "{self._config_path}" to edit config manually.
                '''))
        raise Text2qtiError(f'Configuration option "{key}" has not been set.')


    _default_config_template = textwrap.dedent('''\
        # To set a default LaTeX rendering URL for Canvas, uncomment the
        # appropriate config line below and replace <institution> with the name or
        # abbreviation for your institution.  You can find this by looking at
        # your browser address bar when logged into Canvas.  In some cases, more
        # modifications may be necessary than simply replacing <institution>.

        # For Canvas through Instructure:
        # latex_render_url = "https://<institution>.instructure.com/equation_images/"

        # For Canvas through your institution (may need to change ".edu" domain):
        # latex_render_url = "https://canvas.<institution>.edu/equation_images/"
        ''')

    def load(self):
        '''
        Load config file.
        '''
        config_path = self._config_path
        config_text = None
        try:
            config_text = config_path.read_text('utf8')
            self.loaded_config_file = True
        except FileNotFoundError:
            try:
                config_path.write_text(self._default_config_template, encoding='utf8')
            except FileNotFoundError:
                warnings.warn(f'Could not create default text2qti config file "{config_path}" due to FileNotFoundError (directory does not exist).')
            except PermissionError:
                warnings.warn(f'Could not create default text2qti config file "{config_path}" due to PermissionError.')
        except PermissionError:
            raise Text2qtiError(f'Could not open text2qti config file "{config_path}" due to PermissionError.')
        except UnicodeDecodeError:
            raise Text2qtiError(f'Could not open text2qti config file "{config_path}" due to UnicodeDecodeError. File may be corrupt.')

        if config_text is not None:
            try:
                config_dict = bespon.loads(config_text, empty_default=dict)
            except Exception as e:
                raise Text2qtiError(f'Failed to load config file "{config_path}":\n{e}')
            try:
                self.update(config_dict)
            except Text2qtiError as e:
                raise Text2qtiError(f'Failed to load config file "{config_path}":\n{e}')

    def save(self):
        '''
        Save config file.
        '''
        config_path = self._config_path
        try:
            bespon_text = bespon.dumps(dict(self))
        except Exception as e:
            raise Text2qtiError(f'Failed to convert config data to config file format (invalid data?):\n{e}')
        try:
            config_path.write_text(bespon_text, 'utf8')
        except FileNotFoundError:
            raise Text2qtiError(f'Could not create text2qti config file "{config_path}" due to FileNotFoundError (directory does not exist).')
        except PermissionError:
            raise Text2qtiError(f'Could not create text2qti config file "{config_path}" due to PermissionError.')
