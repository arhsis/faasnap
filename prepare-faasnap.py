#!/usr/bin/env python3
import os
import time
import sys
import json

sys.path.extend(["./python_client"])
from swagger_client.api.default_api import DefaultApi
import swagger_client as faasnap
from swagger_client.configuration import Configuration
from types import SimpleNamespace

os.umask(0o777)


def addNetwork(client: DefaultApi, idx: int):
    ns = "fc%d" % idx
    guest_mac = "AA:FC:00:00:00:01"  # fixed MAC
    guest_addr = "172.16.0.2"  # fixed guest IP
    unique_addr = "192.168.0.%d" % (idx + 2)
    client.net_ifaces_namespace_put(
        namespace=ns,
        interface={
            "host_dev_name": "vmtap0",
            "iface_id": "eth0",
            "guest_mac": guest_mac,
            "guest_addr": guest_addr,
            "unique_addr": unique_addr,
        },
    )


def prepareMincore(
    params, client: DefaultApi, setting, func_name, func_param, namespace
):
    vm = client.vms_post(vm={"func_name": func_name, "namespace": namespace})
    time.sleep(5)
    base_snap = client.snapshots_post(
        snapshot=faasnap.Snapshot(
            vm_id=vm.vm_id,
            snapshot_type="Full",
            snapshot_path=params.test_dir + f"/{func_name}_full.snapshot",
            mem_file_path=params.test_dir + f"/{func_name}_full.memfile",
            version="0.23.0",
        )
    )
    client.vms_vm_id_delete(vm_id=vm.vm_id)
    client.snapshots_ss_id_patch(
        ss_id=base_snap.ss_id, state=vars(setting.patch_base_state)
    )  # drop cache
    time.sleep(2)
    if setting.mincore_size > 0:
        mincore = -1
    else:
        mincore = 100
    invoc = faasnap.Invocation(
        func_name=func_name,
        ss_id=base_snap.ss_id,
        params=func_param,
        mincore=mincore,
        mincore_size=setting.mincore_size,
        enable_reap=False,
        namespace=namespace,
        use_mem_file=True,
    )
    ret = client.invocations_post(invocation=invoc)
    newVmID = ret.vm_id
    print("prepare invoc ret:", ret)
    ret = client.invocations_post(
        invocation=faasnap.Invocation(
            func_name="run",
            vm_id=newVmID,
            params="{\"command\": \"echo 8 > /proc/sys/vm/drop_caches\"}",
            mincore=-1,
            enable_reap=False,
        )
    )  # disable sanitizing
    warm_snap = client.snapshots_post(
        snapshot=faasnap.Snapshot(
            vm_id=newVmID,
            snapshot_type="Full",
            snapshot_path=params.test_dir + f"/{func_name}_warm.snapshot",
            mem_file_path=params.test_dir + f"/{func_name}_warm.memfile",
            version="0.23.0",
            **vars(setting.record_regions),
        )
    )
    client.vms_vm_id_delete(vm_id=newVmID)
    time.sleep(2)
    client.snapshots_ss_id_mincore_put(
        ss_id=warm_snap.ss_id, source=base_snap.ss_id
    )  # carry over mincore to new snapshot
    state = vars(setting.patch_mincore)
    state["to_ws_file"] = params.test_dir + f"/{func_name}_wsfile"
    client.snapshots_ss_id_mincore_patch(
        ss_id=warm_snap.ss_id, state=state
    )
    client.snapshots_ss_id_patch(
        ss_id=base_snap.ss_id, state=vars(setting.patch_base_state)
    )  # drop cache
    client.snapshots_ss_id_patch(
        ss_id=warm_snap.ss_id, state=vars(setting.patch_state)
    )  # drop cache
    client.snapshots_ss_id_mincore_patch(
        ss_id=warm_snap.ss_id, state={"drop_ws_cache": True}
    )

    return warm_snap.ss_id


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: %s <test.json>" % sys.argv[0])
        exit(1)

    with open(sys.argv[1], "r") as f:
        params = json.load(f, object_hook=lambda d: SimpleNamespace(**d))
    conf = Configuration()
    conf.host = params.host

    # params.settings.faasnap.patch_mincore.to_ws_file = params.test_dir + "/wsfile"

    with open("/etc/faasnap.json", "w") as f:
        json.dump(
            params.faasnap, f, default=lambda o: o.__dict__, sort_keys=False, indent=4
        )

    print("kernels:", params.faasnap.kernels)
    print("vcpu:", params.vcpu)

    ssIds = {}
    setting = params.settings.faasnap
    client = faasnap.DefaultApi(faasnap.ApiClient(conf))

    for index, func in enumerate(params.function, start=1):
        print(f"========== preparing: {func} ==========")
        addNetwork(client, index)
        func_config = vars(params.functions)[func]
        client.functions_post(
            function=faasnap.Function(
                func_name=func_config.name,
                image=func_config.image,
                kernel=setting.kernel,
                vcpu=params.vcpu,
            )
        )

        ssIds[func] = prepareMincore(
            params=params,
            client=client,
            setting=setting,
            func_name=func,
            func_param=func_config.params[0],
            namespace=f"fc{index}",
        )

        time.sleep(1)

    print("========== DONE ==========")
    print("ssIds:", ssIds)

    if not os.path.isdir(params.test_dir):
        os.mkdir(params.test_dir)
    with open(os.path.join(params.test_dir, "snapshots.json"), "w") as f:
        json.dump(ssIds, f, default=lambda o: o.__dict__)
