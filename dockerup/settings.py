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
import logging
from dataclasses import dataclass
from pathlib import PosixPath
from typing import List, Dict

import yaml

logger: logging.Logger = logging.getLogger(__name__)



@dataclass(init=True, frozen=True)
class Settings:
    files: List[str]
    workflows: List[str]
    supported_images: Dict[str, str]

    @staticmethod
    def load(path: PosixPath) -> 'Settings':
        settings_path = path / '.dockerup.yaml'
        settings = {
            'files': ['docker/Dockerfile'],
            'workflows': ['CI'],
            'supported_images': {
                'ghcr.io/infrabits/python3-alpine': 'InfraBits/python3-alpine',
                'ghcr.io/infrabits/python3-alpine-3.10': 'InfraBits/python3-alpine',
                'ghcr.io/infrabits/python3-alpine-3.11': 'InfraBits/python3-alpine',
                'ghcr.io/infrabits/python3-alpine-3.12': 'InfraBits/python3-alpine',
            },
        }

        if settings_path.is_file():
            logger.debug(f'Loading settings from {settings_path}')
            with settings_path.open('r') as fh:
                settings_data = yaml.load(fh, Loader=yaml.SafeLoader)
                logger.debug(f'Merging {settings_data} into {settings}')
                settings.update(settings_data)

        return Settings(
            files=settings['files'],
            workflows=settings['workflows'],
            supported_images=settings['supported_images'],
        )
