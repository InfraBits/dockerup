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
from pathlib import PosixPath
from typing import List, Optional, Dict

from dockerup.github import GithubApp, GitHubApi
from dockerup.models import File, Image, Update
from dockerup.settings import Settings

logger: logging.Logger = logging.getLogger(__name__)


class Updater:
    def __init__(self,
                 path: PosixPath,
                 settings: Settings,
                 github_app: Optional[GithubApp]) -> None:
        self._path = path
        self._settings = settings
        self._github_app = github_app
        self._files: List[File] = []
        self._latest_tags: Dict[str, str] = {}

    def _get_latest_tag(self, image: str) -> str:
        repo = self._settings.supported_images[image]
        if repo not in self._latest_tags:
            latest_tag = GitHubApi(repo, 'main', self._github_app).get_latest_release()
            assert latest_tag is not None
            self._latest_tags[repo] = latest_tag
        return self._latest_tags[repo]

    def resolve_files(self) -> List[File]:
        # Search for files to update
        for file_path in self._settings.files:
            file = self._path / file_path
            if not file.is_file():
                logger.info(f'Skipping: {file}')
                continue

            logger.info(f'Discovered: {file}')
            with file.open('r') as fh:
                contents = fh.read()

            self._files.append(File(
                PosixPath(file_path),
                [
                    Image(
                        line.split(' ')[1].split(':')[0],
                        line.split(' ')[1].split(':')[1] if ':' in line.split(' ')[1] else None,
                    )
                    for line in contents.splitlines()
                    if line.startswith('FROM ')
                ],
                contents,
                []))
        return self._files

    def update_files(self) -> List[File]:
        _files: List[File] = []
        for file in self._files:
            updates = []
            for image in file.images:
                if image.image not in self._settings.supported_images:
                    logger.info(f'Skipping: {image}')
                    continue
                latest_tag = self._get_latest_tag(image.image)
                if image.tag != latest_tag:
                    logger.info(f'Updating {image.image} from {image.tag} to {latest_tag}')
                    updates.append(Update(image.image, image.tag, latest_tag))

            updates = list(set(updates))
            contents = file.contents
            for update in updates:
                contents = contents.replace(
                    (
                        f'FROM {update.image}:{update.previous_tag}'
                        if update.previous_tag else
                        f'FROM {update.image}'
                    ),
                    f'FROM {update.image}:{update.new_tag}'
                )
            _files.append(File(file.file_path, file.images, contents, updates))
        return _files
