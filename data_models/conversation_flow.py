# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class Question(Enum):
    CLAIMNUMBER = 1
    FILENOTETEXT = 2
    DATE = 3
    NONE = 4
    OTHER = 5
    TASK = 6
    FILENOTE = 7
    THANKS = 8

class ConversationFlow:
    def __init__(
        self, last_question_asked: Question = Question.NONE,
    ):
        self.last_question_asked = last_question_asked
