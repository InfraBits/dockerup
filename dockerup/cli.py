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
import base64
import logging
import sys
import uuid
from pathlib import PosixPath
from typing import List, Optional

import click

from dockerup.github import GithubApp, GitHubApi
from dockerup.models import File
from dockerup.settings import Settings
from dockerup.updater import Updater

logger: logging.Logger = logging.getLogger(__name__)


def _update(path: PosixPath,
            settings: Settings,
            github_app: Optional[GithubApp]) -> Optional[List[File]]:
    updater = Updater(path, settings, github_app)

    logger.info('Resolving files')
    updater.resolve_files()

    logger.info('Updating files')
    updated_files = updater.update_files()

    if not any([
        file.has_updates()
        for file in updated_files
    ]):
        logger.info('No updates required')
        return None

    logger.info('Saving updated files')
    for file in updated_files:
        if file.has_updates():
            logger.info(f' - {file.file_path}')
            with (path / file.file_path).open('w') as fh:
                fh.write(file.contents)

    return updated_files


def _merge(settings: Settings, repository: str,
           updated_files: List[File],
           github_app: Optional[GithubApp]) -> None:
    branch_name = f'dockerup-{uuid.uuid4()}'
    logger.info(f'Merging updated files files using {branch_name}')

    # Handle the merging logic as required
    git = GitHubApi(repository, branch_name, github_app)
    head_ref, head_sha = git.get_head_ref()
    if not head_ref or not head_sha:
        logger.error('Failed to get head ref')
        return

    git.create_branch(head_sha)

    pull_request_summary = f'dockerup ({len(updated_files)})'
    pull_request_description = ''
    branch_sha = None
    for file in updated_files:
        if file.has_updates():
            commit_summary = file.update_summary()
            commit_description = file.update_detail()

            pull_request_description += f'{file.file_path}:\n'
            pull_request_description += f'{commit_description}\n'

            logger.info(f' - {file.file_path}')
            logger.info(f'  Using commit summary: {commit_summary}')
            logger.info(f'  Using commit description: {commit_description}')
            branch_sha = git.update_branch_file(file.file_path,
                                                file.contents,
                                                commit_summary,
                                                commit_description)

    logger.info(f'Creating pull request for {branch_name}')
    assert branch_sha is not None
    if pull_request_id := git.create_pull_request(head_ref,
                                                  pull_request_summary,
                                                  pull_request_description.strip()):
        logger.info(f'Waiting for workflows to complete on {branch_name}')
        if git.wait_for_workflows(settings.workflows, pull_request_id):
            logger.info(f'Merging pull request {pull_request_id}')
            git.merge_pull_request(pull_request_id)
        else:
            logger.info(f'Closing failed pull request {pull_request_id}')
            try:
                git.create_commit_comment(
                    branch_sha,
                    f'Expected workflow ({", ".join(settings.workflows)}) failed'
                )
            except Exception as e:
                logger.exception('Failed to create commit comment', e)
            git.delete_branch()


@click.command()
@click.option('--debug', is_flag=True, help='Increase logging level to debug')
@click.option('--merge', is_flag=True, help='Merge changes into a GitHub repo')
@click.option('--repository', help='Name of the GitHub repo these files belong to')
@click.option('--github-app-id', type=int, help='GitHub app id')
@click.option('--github-app-key', type=str, help='GitHub app private key')
@click.option('--path', help='Path to update', type=PosixPath, default=PosixPath.cwd())
def cli(debug: bool,
        path: PosixPath,
        merge: bool,
        repository: str,
        github_app_id: Optional[int] = None,
        github_app_key: Optional[str] = None) -> None:
    '''dockerup - Simple docker image updater.'''
    logging.basicConfig(stream=sys.stderr,
                        level=(logging.DEBUG if debug else logging.INFO),
                        format='%(asctime)-15s %(message)s')

    if merge and not repository:
        click.echo("--merge requires --repository")
        return

    # Load the settings for our runtime
    settings = Settings.load(path)
    logger.info(f'Using settings: {settings}')

    # Setup a GithubApp if needed
    github_app: Optional[GithubApp] = None
    if github_app_id and github_app_key:
        github_app = GithubApp(github_app_id, base64.b64decode(github_app_key).decode('utf-8'))

    # Perform the actual updates
    updated_files = _update(path, settings, github_app)

    # Create a pull request if required & we have changes
    if merge and updated_files:
        _merge(settings, repository, updated_files, github_app)


if __name__ == '__main__':
    cli()
