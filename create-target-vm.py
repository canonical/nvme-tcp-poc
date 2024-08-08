#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--console-output", action="store_true")
    parser.add_argument("--installer-iso", type=Path, default="/srv/iso/ubuntu-24.04-live-server-amd64.iso")
    parser.add_argument("--nvme-volume-name", default="nvme-target.qcow2")
    return parser.parse_args()


def find_nvme_target_drive(nvme_volume_name: str, *, create=False) -> Path:
    if create:
        subprocess.run(["virsh", "vol-create-as",
                        "--pool", "ubuntu-nvmeotcp-poc",
                        "--name", nvme_volume_name,
                        "--capacity", "8G",
                        "--format", "qcow2"])

    cmd = ["virsh", "vol-path",
           "--pool", "ubuntu-nvmeotcp-poc",
           "--vol", nvme_volume_name]
    return Path(subprocess.check_output(cmd, text=True).rstrip())


def main() -> None:
    args = parse_cli_args()

    extra_args = ["autoinstall"]

    if args.console_output:
        extra_args.append("console=tty0")

    nvme_target_file = find_nvme_target_drive(args.nvme_volume_name, create=True)

    cmd = [
            "virt-install",
            "--noreboot",
            "--connect", "qemu:///session",
            "--name", "ubuntu-nvmeotcp-poc-target",
            "--disk", "size=10,pool=ubuntu-nvmeotcp-poc",
            "--memory", "1024",
            "--virt-type", "kvm",
            "--location", str(args.installer_iso),
            "--cloud-init", "user-data=resources/cc-nvmet.yaml",
            "--extra-args", " ".join(extra_args),
            f"--qemu-commandline=-drive file={nvme_target_file},if=none,id=nvm",
            "--qemu-commandline=-device nvme,drive=nvm,serial=nvme-1,addr=0x10",
            "--network", "network=poc-network",
            ]

    subprocess.run(cmd)

if __name__ == "__main__":
    main()
