#! /usr/bin/env bash
set -ex

LANGUAGE_ENV=$1

IN=debian-base-rootfs.ext4
OUT=debian-$LANGUAGE_ENV-provisioned-rootfs.ext4
TMPOUT=.$OUT

sudo umount ./mountpoint || true
sudo rm -rf ./mountpoint
mkdir -p ./mountpoint
cp $IN $TMPOUT

sudo mount $TMPOUT mountpoint
sudo cp scripts/setup-debian-$LANGUAGE_ENV-rootfs.sh mountpoint/
mkdir -p mountpoint/app
sudo chroot mountpoint /bin/bash /setup-debian-$LANGUAGE_ENV-rootfs.sh

sudo umount mountpoint
mv $TMPOUT $OUT
