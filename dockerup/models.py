'''
dockerup - Simple docker image updater

MIT License

Copyright (c) 2023 Infra Bits

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
import dataclasses
import logging
from pathlib import PosixPath
from typing import List, Optional

logger: logging.Logger = logging.getLogger(__name__)


@dataclasses.dataclass(init=True, frozen=True)
class Image:
    image: str
    tag: Optional[str]


@dataclasses.dataclass(init=True, frozen=True)
class Update:
    image: str
    previous_tag: Optional[str]
    new_tag: str


@dataclasses.dataclass(init=True, frozen=True)
class File:
    file_path: PosixPath
    images: List[Image]
    contents: str
    updates: List[Update]

    def has_updates(self) -> bool:
        return len(self.updates) > 0

    def update_summary(self) -> str:
        return f'dockerup: {len(self.updates)} images updated in {self.file_path}'

    def update_detail(self) -> str:
        commit_body = ''
        for update in sorted(self.updates, key=lambda u: (u.image,
                                                          u.previous_tag,
                                                          u.new_tag)):
            commit_body += f'* {update.image}:'
            if update.previous_tag:
                commit_body += f' {update.previous_tag}'
            commit_body += f' -> {update.new_tag}\n'
        return commit_body
