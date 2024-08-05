#!/usr/bin/env python3

import argparse
import ipaddress
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--console-output", action="store_true")
    parser.add_argument("--installer-iso", type=Path, default="/srv/iso/oracular-live-server-amd64.iso")
    parser.add_argument("--target-ip", type=str)
    parser.add_argument("--target-port", type=int, default=4420)
    return parser.parse_args()


def render_autoinstall_yaml(template: Path, addr: str, port: int) -> str:
    with template.open() as template_stream:
        template_yaml = yaml.safe_load(template_stream)

    template_yaml["autoinstall"]["early-commands"].append(
        ["nvme", "connect-all", "--transport", "tcp", "--traddr", addr, "--trsvcid", str(port)]
    )

    return yaml.dump(template_yaml)


def gen_cloud_config(*args, **kwargs) -> Path:
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as output_stream:
        output_stream.write("#cloud-config\n")
        output_stream.write(render_autoinstall_yaml(*args, **kwargs))
    return output_stream.name


def get_target_ip() -> str:
    out = subprocess.check_output(["virsh", "domifaddr", "ubuntu-nvmeotcp-poc-target", "--source", "agent", "--full"], text=True)

    for line in out.splitlines():
        if line.strip().startswith("enp1s0"):
            ip_with_cidr = ipaddress.ip_interface(line.strip().split()[-1])
            return str(ip_with_cidr.ip)
    raise ValueError("Could not determine IP address of NVMe target")


def main() -> None:
    args = parse_cli_args()

    if (target_ip := args.target_ip) is None:
        print("Trying to guess target IP")
        target_ip = get_target_ip()


    rendered_cloud_config = gen_cloud_config(
            Path("resources/cc-initiator.yaml"),
            addr=target_ip, port=args.target_port)

    bootloader = {
        "loader": str(Path("resources/OVMF_CODE.fd").absolute()),
        "loader.readonly": "yes",
        "loader.type": "pflash",
        "loader.secure": "false",
        "nvram.template": str(Path("resources/OVMF_VARS.fd").absolute()),
    }

    cmd = [
            "virt-install",
            "--autoconsole", "graphical",
            "--noreboot",
            "--connect", "qemu:///session",
            "--name", "ubuntu-nvmeotcp-poc-initiator",
            "--disk", "none",
            "--memory", "2048",
            "--virt-type", "kvm",
            "--location", str(args.installer_iso),
            "--cloud-init", f"user-data={str(rendered_cloud_config)}",
            "--network", "network=poc-network",
            "--boot", ",".join([f"{key}={val}" for key, val in bootloader.items()])
            ]

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
