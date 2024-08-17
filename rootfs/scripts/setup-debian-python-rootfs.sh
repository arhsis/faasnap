#! /usr/bin/env bash
set -ex

echo "debian" > /etc/hostname
echo root:rootroot | chpasswd

apt install -y gpg wget
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 
wget https://github.com/Kitware/CMake/releases/download/v3.22.2/cmake-3.22.2-linux-x86_64.tar.gz -O /opt/cmake-3.22.2-linux-x86_64.tar.gz
unset http_proxy https_proxy
pushd /opt
tar xzvf cmake-3.22.2-linux-x86_64.tar.gz
export PATH=$PATH:/opt/cmake-3.22.2-linux-x86_64/bin/
popd


pushd /root
# apt install -y tcpdump build-essential pkg-config python3-setuptools python-dev python3-dev gcc libpq-dev python-pip python3-dev python3-pip python3-venv python3-wheel
pip install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple virtualenv
virtualenv --no-periodic-update faas
virtualenv --no-periodic-update ir
popd
/root/faas/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip setuptools wheel
/root/ir/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip setuptools wheel

/root/faas/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask waitress Chameleon jinja2 numpy opencv-python-headless pillow psutil pyaes six igraph virtualenv
# pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple torch==2.0.1+cpu torchvision==0.2.1 
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 
/root/ir/bin/pip install --extra-index-url https://download.pytorch.org/whl/cpu torch==2.0.1+cpu torchvision==0.2.1
unset http_proxy https_proxy
/root/ir/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pillow==6.2.2

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

cat <<EOF > /etc/systemd/system/init-entropy.service
[Unit]
Description=Init entropy
Wants=network-online.target
After=network-online.target
[Service]
Type=simple
User=root
ExecStart=python3 /app/entropy.py
[Install]
WantedBy=multi-user.target
EOF
chmod 644 /etc/systemd/system/init-entropy.service
systemctl enable init-entropy.service

cat <<EOF > /etc/systemd/system/function-daemon.service
[Unit]
Description=Serverless function daemon
Wants=init-entropy.service
After=init-entropy.service
StartLimitIntervalSec=0
[Service]
Type=simple
Restart=always
RestartSec=1
User=root
ExecStart=/root/faas/bin/python /app/daemon.py
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

# systemctl disable systemd-timesyncd.service
systemctl disable systemd-update-utmp.service
# systemctl disable redis-server.service
