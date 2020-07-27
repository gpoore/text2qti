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
from .quiz import Quiz
from .xml_imsmanifest import imsmanifest
from .xml_assessment_meta import assessment_meta
from .xml_assessment import assessment


class QTI(object):
    '''
    Create QTI from a Quiz object.
    '''
    def __init__(self, quiz: Quiz):
        self.quiz = quiz
        id_base = 'text2qti'
        self.manifest_identifier = f'{id_base}_manifest_{quiz.id}'
        self.assessment_identifier = f'{id_base}_assessment_{quiz.id}'
        self.dependency_identifier = f'{id_base}_dependency_{quiz.id}'
        self.assignment_identifier = f'{id_base}_assignment_{quiz.id}'
        self.assignment_group_identifier = f'{id_base}_assignment-group_{quiz.id}'

        self.imsmanifest_xml = imsmanifest(manifest_identifier=self.manifest_identifier,
                                           assessment_identifier=self.assessment_identifier,
                                           dependency_identifier=self.dependency_identifier,
                                           images=self.quiz.images)
        self.assessment_meta = assessment_meta(assessment_identifier=self.assessment_identifier,
                                               assignment_identifier=self.assignment_identifier,
                                               assignment_group_identifier=self.assignment_group_identifier,
                                               title_xml=quiz.title_xml,
                                               description_html_xml=quiz.description_html_xml,
                                               points_possible=quiz.points_possible,
                                               shuffle_answers=quiz.shuffle_answers_xml,
                                               show_correct_answers=quiz.show_correct_answers_xml,
                                               one_question_at_a_time=quiz.one_question_at_a_time_xml,
                                               cant_go_back=quiz.cant_go_back_xml)
        self.assessment = assessment(quiz=quiz,
                                     assessment_identifier=self.assessment_identifier,
                                     title_xml=quiz.title_xml)


    def write(self, bytes_stream: BinaryIO):
        with zipfile.ZipFile(bytes_stream, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('imsmanifest.xml', self.imsmanifest_xml)
            zf.writestr(zipfile.ZipInfo('non_cc_assessments/'), b'')
            zf.writestr(f'{self.assessment_identifier}/assessment_meta.xml', self.assessment_meta)
            zf.writestr(f'{self.assessment_identifier}/{self.assessment_identifier}.xml', self.assessment)
            for image in self.quiz.images.values():
                zf.writestr(image.qti_zip_path, image.data)


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
