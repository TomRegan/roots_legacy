#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015 Tom Regan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import namedtuple
from difflib import SequenceMatcher

Added = namedtuple('Added', 'text')
Removed = namedtuple('Removed', 'text')
Modified = namedtuple('Modified', 'text')
Unchanged = namedtuple('Unchanged', 'text')

def diff(original, replacement):
    result = {}
    for key in replacement.keys():
        if not key in original and key in replacement:
            result[key] = [Added(replacement[key])]
        if key in original and key in replacement:
            matcher = SequenceMatcher(
                a=original[key],
                b=replacement[key])
            opcodes = matcher.get_opcodes()
            chunks = []
            for opcode in opcodes:
                if opcode[0] == 'insert':
                    start, end = opcode[3], opcode[4]
                    chunks.append(Added(replacement[key][start:end]))
                if opcode[0] == 'replace':
                    start, end = opcode[3], opcode[4]
                    chunks.append(Modified(replacement[key][start:end]))
                if opcode[0] == 'delete':
                    start, end = opcode[1], opcode[2]
                    chunks.append(Removed(original[key][start:end]))
                if opcode[0] == 'equal':
                    start, end = opcode[1], opcode[2]
                    chunks.append(Unchanged(original[key][start:end]))
                result[key] = chunks
    return result
