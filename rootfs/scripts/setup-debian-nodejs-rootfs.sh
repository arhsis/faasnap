#! /usr/bin/env bash
set -ex

echo "debian" > /etc/hostname
echo root:rootroot | chpasswd

# apt install -y tcpdump build-essential pkg-config python3-setuptools python-dev python3-dev gcc libpq-dev python-pip python3-dev python3-pip python3-venv python3-wheel
source /root/.bashrc
npm config set registry https://registry.npmmirror.com
pushd /app/
npm install express@4.16.2 body-parser@1.18.2 sharp@0.32.6
popd

mkdir -p /etc/systemd/system/serial-getty@ttyS0.service.d/
cat <<EOF > /etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root -o '-p -- \\u' --keep-baud 115200,38400,9600 %I $TERM
EOF

cat <<EOF > /etc/network/interfaces.d/eth0
auto eth0
allow-hotplug eth0
iface eth0 inet static
address 172.16.0.2/24
gateway 172.16.0.1
EOF

cat <<EOF > /etc/systemd/system/function-daemon.service
[Unit]
Description=Serverless function daemon
StartLimitIntervalSec=0
[Service]
Type=simple
Restart=always
RestartSec=1
User=root
Environment="NODE_ENV=production"
ExecStart=bash -c "source /root/.bashrc && node /app/daemon.js"
WorkingDirectory=/app
[Install]
WantedBy=multi-user.target
EOF

cat <<EOF >> /etc/sysctl.conf
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF

# cat <<EOF >> /etc/rsyslog.conf
# *.*    -/dev/shm/syslog
# EOF

cat <<EOF >> /etc/ssh/sshd_config
PermitRootLogin yes
EOF

ln -s /dev/shm /usr/tmp

chmod 644 /etc/systemd/system/function-daemon.service
systemctl enable function-daemon.service

systemctl disable systemd-timesyncd.service
systemctl disable systemd-update-utmp.service
