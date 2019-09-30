#!/bin/sh

export GIT_MERGE_AUTOEDIT=no

BUMP_PART=${1:-"release"}
NEW_VERSION=${2:-`bump2version --dry-run --list ${BUMP_PART} | grep new_version= | sed 's/new_version=//'`}
CUR_VERSION=`bump2version --dry-run --list ${BUMP_PART} | grep current_version= | sed 's/current_version=//'`
DATE=`date +%F`

git flow release start ${NEW_VERSION}

bump2version --verbose --no-commit --new-version ${NEW_VERSION} ${BUMP_PART}

pre-commit run trailing-whitespace --file .bumpversion.cfg
pre-commit run end-of-file-fixer --file .bumpversion.cfg

git add .bumpversion.cfg
git add ms_graph_exporter/__init__.py
git add pyproject.toml

git commit --message "chg: pkg: Bump version: ${CUR_VERSION} → ${NEW_VERSION} !minor"

gitchangelog | sed 's/^.*!wip.*$//' | sed '/^$/N;/^\n$/D' | sed "s/## (unreleased)/## ${NEW_VERSION} (${DATE})/" > CHANGELOG.md

pre-commit run end-of-file-fixer --file CHANGELOG.md

git add CHANGELOG.md

pre-commit run trailing-whitespace
pre-commit run end-of-file-fixer

git commit --message "new: pkg: Generate latest CHANGELOG. !minor"

gitchangelog ^${CUR_VERSION} HEAD | sed 's/^.*!wip.*$//' | sed '/^$/N;/^\n$/D' | sed "s/## (unreleased)/${NEW_VERSION} (${DATE})/" | sed 's/### //' > RELEASE.md

git flow release finish --showcommands -f RELEASE.md ${NEW_VERSION}

rm RELEASE.md

unset GIT_MERGE_AUTOEDIT
