# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import io
import pathlib
from typing import Union, BinaryIO
import zipfile
from .config import Config
from .quiz import Quiz
from .xml_imsmanifest import imsmanifest
from .xml_assessment_meta import assessment_meta
from .xml_assessment import assessment


class QTI(object):
    '''
    Create QTI from a Quiz object.
    '''
    def __init__(self, quiz: Quiz, *, config: Config):
        id_base = 'text2qti'
        self.manifest_identifier = f'{id_base}_manifest_{quiz.id}'
        self.assessment_identifier = f'{id_base}_assessment_{quiz.id}'
        self.dependency_identifier = f'{id_base}_dependency_{quiz.id}'
        self.assignment_identifier = f'{id_base}_assignment_{quiz.id}'
        self.assignment_group_identifier = f'{id_base}_assignment-group_{quiz.id}'
        self.title_raw = quiz.title_raw
        self.title_xml = quiz.title_xml
        self.description_raw = quiz.description_raw
        self.description_xml = quiz.description_xml
        self.points_possible = quiz.points_possible

        self.imsmanifest_xml = imsmanifest(manifest_identifier=self.manifest_identifier,
                                           assessment_identifier=self.assessment_identifier,
                                           dependency_identifier=self.dependency_identifier)
        self.assessment_meta = assessment_meta(assessment_identifier=self.assessment_identifier,
                                               assignment_identifier=self.assessment_identifier,
                                               assignment_group_identifier=self.assignment_group_identifier,
                                               title_xml=self.title_xml,
                                               description_xml=self.description_xml,
                                               points_possible=self.points_possible)
        self.assessment = assessment(quiz=quiz,
                                     assessment_identifier=self.assignment_identifier,
                                     title_xml=self.title_xml)


    def write(self, bytes_stream: BinaryIO):
        with zipfile.ZipFile(bytes_stream, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('ismanifest.xml', self.imsmanifest_xml)
            zf.writestr(zipfile.ZipInfo('non_cc_assessments/'), b'')
            zf.writestr(f'{self.assessment_identifier}/assessment_meta.xml', self.assessment_meta)
            zf.writestr(f'{self.assessment_identifier}/{self.assessment_identifier}.xml', self.assessment)\


    def zip_bytes(self) -> bytes:
        stream = io.BytesIO()
        self.write(stream)
        return stream.getvalue()


    def save(self, qti_path: Union[str, pathlib.Path]):
        if isinstance(qti_path, str):
            qti_path = pathlib.Path(qti_path)
        elif not isinstance(qti_path, pathlib.Path):
            raise TypeError
        qti_path.write_bytes(self.zip_bytes())
