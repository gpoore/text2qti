# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import datetime
from typing import Dict, Optional
from .quiz import Image

from importlib.resources import files

def MANIFEST_START(template):
    return files(f"text2qti.templates.{template}").joinpath(
            'MANIFEST_START.xml').read_text()

IMAGE = '''\
    <resource identifier="text2qti_image_{ident}" type="webcontent" href="{path}">
      <file href="{path}"/>
    </resource>
'''

MANIFEST_END = '''\
  </resources>
</manifest>
'''


def imsmanifest(*,
                template: str,
                manifest_identifier: str,
                assessment_identifier: str,
                dependency_identifier: str,
                images: Dict[str, Image],
                date: Optional[str]=None) -> str:
    '''
    Generate `imsmanifest.xml`.
    '''
    if date is None:
        date = str(datetime.date.today())
    xml = []
    xml.append(MANIFEST_START(template).format(manifest_identifier=manifest_identifier,
                                     assessment_identifier=assessment_identifier,
                                     dependency_identifier=dependency_identifier,
                                     date=date))
    for image in images.values():
        xml.append(IMAGE.format(ident=image.id, path=image.qti_xml_path))
    xml.append(MANIFEST_END)
    return ''.join(xml)
