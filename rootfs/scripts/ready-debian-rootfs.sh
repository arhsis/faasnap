#! /usr/bin/env bash

set -ex

IN=$1
OUT=$2
LANGUAGE_ENV=$3
TMPOUT=.$OUT

sudo umount ./mountpoint || true
sudo rm -rf ./mountpoint
mkdir -p ./mountpoint
cp $IN $TMPOUT

sudo mount $TMPOUT mountpoint
sudo mkdir mountpoint/app
sudo cp -r guest/$LANGUAGE_ENV/* mountpoint/app/

sudo umount mountpoint
mv $TMPOUT $OUT
