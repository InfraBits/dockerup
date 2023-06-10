# dockerup - Simple docker image updater

Intended to be used with apko style images i.e. InfraBits/python3-alpine

## Example usage

`.dockerup.yaml`
```yaml
files:
  - docker/Dockerfile
workflows:
  - CI
```

_Note: Sane defaults are used without a config file_

`.github/workflows/dockerup.yml`
```yaml
name: Update container image tags using dockerup
on: {schedule: [{cron: '13 6 * * *'}], push: {branches: [main]}}
permissions: {contents: read}
jobs: {pipup: {runs-on: ubuntu-20.04,
               steps: [{uses: InfraBits/github-actions/dockerup@main,
                        with: {github_app_id: '${{ secrets.GH_APP_ID }}',
                               github_app_key: '${{ secrets.GH_APP_KEY }}'}}]}}
```

_Note: Change the schedule/branches to suit the local repository_
