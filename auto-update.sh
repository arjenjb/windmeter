#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd $DIR

sudo -u arjen git fetch

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @ "$UPSTREAM")

if [ $LOCAL = $REMOTE ]; then
    echo "Up-to-date"
elif [ $LOCAL = $BASE ]; then
    echo "Need to pull"
    service windmeter stop
    ./knipperlicht.py &
    sudo -u arjen git pull
    service windmeter start

elif [ $REMOTE = $BASE ]; then
    echo "Need to push"
else
    echo "Diverged"
fi
