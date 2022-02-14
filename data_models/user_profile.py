# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class UserProfile:
    def __init__(self, name: str = None, age: int = 0, date: str = None):
        self.name = name
        self.age = age
        self.date = date


class FileNoteContext:
    def __init__(self, claimNumber: str = None, text: str = None):
        self.claimNumber = claimNumber
        self.text = text