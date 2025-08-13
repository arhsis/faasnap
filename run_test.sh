#!/bin/bash
# set -eux
# better exec after `sudo -s`
function download_vm_deps(){
    wget -O vmlinux https://cloud.tsinghua.edu.cn/f/ef649f94564e4b40a1c2/?dl=1 && \
    wget -O firecracker https://cloud.tsinghua.edu.cn/f/fa90c80489c842608a51/?dl=1 && \
    chmod +x vmlinux firecracker

    wget -O debian-nodejs-rootfs.ext4.zip https://cloud.tsinghua.edu.cn/f/0b2144137441475495a3/?dl=1 && \
    wget -O debian-python-rootfs.ext4.zip https://cloud.tsinghua.edu.cn/f/72ba9d8cdaac4abf8856/?dl=1
    apt install unzip && unzip debian-nodejs-rootfs.ext4.zip && unzip debian-python-rootfs.ext4.zip
}

function download_faasnap_deps(){
    apt update && apt install redis
    
    wget https://go.dev/dl/go1.21.13.linux-amd64.tar.gz
    rm -rf /usr/local/go && tar -C /usr/local -xzf go1.21.13.linux-amd64.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    source ~/.bashrc && go version

    go install github.com/go-swagger/go-swagger/cmd/swagger@latest
    # pls correct the path of faasnap and the go/bin
    ~/go/bin/swagger generate server -f api/swagger.yaml
    go get ./... && go build cmd/faasnap-server/main.go
}

function prep_env(){
    # 1. network settings
    apt install acl -y
    ./prep.sh
    # 2. edit the first "faasnap" block settings in the `test-2inputs.json`

    # 3. prepare redis kvs
    apt install pip -y
    pip install redis
    chmod +x *.py
    ./prepare-redis.py
}

# download_vm_deps
# download_faasnap_deps
# prep_env

pkill -9 main
pkill -9 firecracker

go build cmd/faasnap-server/main.go
# rm /mnt/*
# rm /users/muhan/faasnap/nfs-dir/snapshot/*
# rm -rf /users/muhan/faasnap/nfs-dir/vm/*
python3 test.py ./test-2inputs.json

# setsid ./main --host=0.0.0.0 --port=8080 &> /users/muhan/faasnap/faasnap.log &
# python3 prepare-faasnap.py faasnap ./test-2inputs.json | tee test-2inputs.output
# python3 -m pdb prepare-faasnap.py faasnap ./test-2inputs.json
