#!/bin/sh

export GIT_MERGE_AUTOEDIT=no

BUMP_PART=${1:-"release"}
NEW_VERSION=${2:-`bump2version --dry-run --allow-dirty --list $BUMP_PART | grep new_version= | sed 's/new_version=//'`}
CUR_VERSION=`bump2version --dry-run --allow-dirty --list $BUMP_PART | grep current_version= | sed 's/current_version=//'`
DATE=`date +%F`

git flow release start $NEW_VERSION

bump2version --allow-dirty --new-version $NEW_VERSION $BUMP_PART

gitchangelog | sed "s/## (unreleased)/## $NEW_VERSION ($DATE)/" > CHANGELOG.md

git add CHANGELOG.md

git commit --message "new: pkg: Generate latest CHANGELOG. !minor"

gitchangelog ^$CUR_VERSION HEAD | sed "s/## (unreleased)/$NEW_VERSION ($DATE)/" | sed "s/### //" > RELEASE.md

git flow release finish --showcommands -f RELEASE.md $NEW_VERSION

rm RELEASE.md

unset GIT_MERGE_AUTOEDIT
