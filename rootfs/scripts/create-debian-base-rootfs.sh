#! /usr/bin/env bash
set -ex

DEBIAN_VERSION=${1}

sudo umount ./mountpoint || true
sudo rm -rf ./mountpoint
mkdir -p ./mountpoint
dd if=/dev/zero of=.debian-base-rootfs.ext4 bs=2M count=4096
mkfs.ext4 .debian-base-rootfs.ext4

sudo mount .debian-base-rootfs.ext4 mountpoint
sudo debootstrap --include openssh-server,nano,vim,ffmpeg,libjpeg-dev,zlib1g-dev,tcpdump,build-essential,pkg-config,python3,python3-pip,python3-setuptools,python-dev,python3-dev,gcc,libpq-dev,python-pip,python3-dev,python3-venv,python3-wheel,curl $DEBIAN_VERSION mountpoint http://deb.debian.org/debian/
sudo chroot mountpoint /bin/bash -c "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash"
sudo chroot mountpoint /bin/bash -c "source /root/.bashrc && nvm install 18"

sudo umount mountpoint
mv .debian-base-rootfs.ext4 debian-base-rootfs.ext4
