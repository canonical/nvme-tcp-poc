#!/usr/bin/env python3

import argparse
import subprocess
import tempfile
from pathlib import Path

import yaml


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--console-output", action="store_true")
    parser.add_argument("--installer-iso", type=Path, default="/srv/iso/oracular-live-server-amd64.iso")
    parser.add_argument("--target-ip", type=str, required=True)
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


def main() -> None:
    args = parse_cli_args()

    rendered_cloud_config = gen_cloud_config(
            Path("resources/cc-initiator.yaml"),
            addr=args.target_ip, port=args.target_port)
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
            ]

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
