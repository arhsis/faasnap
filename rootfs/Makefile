.PHONY: all clean

DIST=debian
DEBIAN_VERSION=buster # buster-slim
GUESTFILES := $(wildcard guest/*)

all:

debian-base-rootfs.ext4: scripts/create-debian-base-rootfs.sh
	scripts/create-debian-base-rootfs.sh $(DEBIAN_VERSION) # install base image

debian-python-provisioned-rootfs.ext4: debian-base-rootfs.ext4 scripts/provision-debian-rootfs.sh scripts/setup-debian-python-rootfs.sh
	scripts/provision-debian-rootfs.sh python  # install dependencies, sys config

debian-nodejs-provisioned-rootfs.ext4: debian-base-rootfs.ext4 scripts/provision-debian-rootfs.sh scripts/setup-debian-nodejs-rootfs.sh
	scripts/provision-debian-rootfs.sh nodejs # install dependencies, sys config

debian-python-rootfs.ext4: debian-python-provisioned-rootfs.ext4 scripts/ready-debian-rootfs.sh $(GUESTFILES)
	scripts/ready-debian-rootfs.sh debian-python-provisioned-rootfs.ext4 debian-python-rootfs.ext4 python # install functions

debian-nodejs-rootfs.ext4: debian-nodejs-provisioned-rootfs.ext4 scripts/ready-debian-rootfs.sh $(GUESTFILES)
	scripts/ready-debian-rootfs.sh debian-nodejs-provisioned-rootfs.ext4 debian-nodejs-rootfs.ext4 nodejs # install functions

debian-rootfs: debian-python-rootfs.ext4 debian-nodejs-rootfs.ext4


clean:
	rm -rf *.ext4

