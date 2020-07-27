# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


from typing import Union


TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<quiz identifier="{assessment_identifier}" xmlns="http://canvas.instructure.com/xsd/cccv1p0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd">
  <title>{title}</title>
  <description>{description}</description>
  <shuffle_answers>{shuffle_answers}</shuffle_answers>
  <scoring_policy>keep_highest</scoring_policy>
  <hide_results>{hide_results}</hide_results>
  <quiz_type>assignment</quiz_type>
  <points_possible>{points_possible:.1f}</points_possible>
  <require_lockdown_browser>false</require_lockdown_browser>
  <require_lockdown_browser_for_results>false</require_lockdown_browser_for_results>
  <require_lockdown_browser_monitor>false</require_lockdown_browser_monitor>
  <lockdown_browser_monitor_data/>
  <show_correct_answers>{show_correct_answers}</show_correct_answers>
  <anonymous_submissions>false</anonymous_submissions>
  <could_be_locked>false</could_be_locked>
  <allowed_attempts>1</allowed_attempts>
  <one_question_at_a_time>{one_question_at_a_time}</one_question_at_a_time>
  <cant_go_back>{cant_go_back}</cant_go_back>
  <available>false</available>
  <one_time_results>false</one_time_results>
  <show_correct_answers_last_attempt>false</show_correct_answers_last_attempt>
  <only_visible_to_overrides>false</only_visible_to_overrides>
  <module_locked>false</module_locked>
  <assignment identifier="{assignment_identifier}">
    <title>{title}</title>
    <due_at/>
    <lock_at/>
    <unlock_at/>
    <module_locked>false</module_locked>
    <workflow_state>unpublished</workflow_state>
    <assignment_overrides>
    </assignment_overrides>
    <quiz_identifierref>{assessment_identifier}</quiz_identifierref>
    <allowed_extensions></allowed_extensions>
    <has_group_category>false</has_group_category>
    <points_possible>{points_possible:.1f}</points_possible>
    <grading_type>points</grading_type>
    <all_day>false</all_day>
    <submission_types>online_quiz</submission_types>
    <position>1</position>
    <turnitin_enabled>false</turnitin_enabled>
    <vericite_enabled>false</vericite_enabled>
    <peer_review_count>0</peer_review_count>
    <peer_reviews>false</peer_reviews>
    <automatic_peer_reviews>false</automatic_peer_reviews>
    <anonymous_peer_reviews>false</anonymous_peer_reviews>
    <grade_group_students_individually>false</grade_group_students_individually>
    <freeze_on_copy>false</freeze_on_copy>
    <omit_from_final_grade>false</omit_from_final_grade>
    <intra_group_peer_reviews>false</intra_group_peer_reviews>
    <only_visible_to_overrides>false</only_visible_to_overrides>
    <post_to_sis>false</post_to_sis>
    <moderated_grading>false</moderated_grading>
    <grader_count>0</grader_count>
    <grader_comments_visible_to_graders>true</grader_comments_visible_to_graders>
    <anonymous_grading>false</anonymous_grading>
    <graders_anonymous_to_graders>false</graders_anonymous_to_graders>
    <grader_names_visible_to_final_grader>true</grader_names_visible_to_final_grader>
    <anonymous_instructor_annotations>false</anonymous_instructor_annotations>
    <post_policy>
      <post_manually>false</post_manually>
    </post_policy>
  </assignment>
  <assignment_group_identifierref>{assignment_group_identifier}</assignment_group_identifierref>
  <assignment_overrides>
  </assignment_overrides>
</quiz>
'''


def assessment_meta(*,
                    assessment_identifier: str,
                    assignment_group_identifier: str,
                    assignment_identifier: str,
                    title_xml: str,
                    description_html_xml: str,
                    points_possible: Union[int, float],
                    shuffle_answers: str,
                    show_correct_answers: str,
                    one_question_at_a_time: str,
                    cant_go_back: str) -> str:
    '''
    Generate `assessment_meta.xml`.
    '''
    return TEMPLATE.format(assessment_identifier=assessment_identifier,
                           assignment_identifier=assignment_identifier,
                           assignment_group_identifier=assignment_group_identifier,
                           title=title_xml,
                           description=description_html_xml,
                           points_possible=points_possible,
                           shuffle_answers=shuffle_answers,
                           show_correct_answers=show_correct_answers,
                           hide_results='always' if show_correct_answers == 'false' else '',
                           one_question_at_a_time=one_question_at_a_time,
                           cant_go_back=cant_go_back)
