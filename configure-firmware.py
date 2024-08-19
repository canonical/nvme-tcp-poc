#!/usr/bin/env python3

import argparse
import tempfile
from pathlib import Path
import uuid

import jinja2

from ubuntu_nvme_tcp_poc import get_initiator_mac, get_target_ip


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-ip", type=str)
    return parser.parse_args()


def render_config_template(template: Path, *, target_ip: str, mac: str) -> str:
    with template.open(encoding="utf-8") as template_stream:
        template = jinja2.Template(template_stream.read())

    context = {
        "targetip": target_ip,
        "targetport": "4420",
        "mac": mac,
        # It is a shame that we need to specify those, because they are
        # automatically set to acceptable values when installing the OS.
        "hostid": str(uuid.uuid4()),
        "hostnqn": "nqn.2024-06.ubuntu-nvmeotcp-poc-initiator",
    }

    return template.render(context)


def create_firmware_config(template: Path, **kwargs) -> Path:
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as stream:
        stream.write(render_config_template(template, **kwargs))
        stream.write("\n")
    return Path(stream.name)


def main() -> None:
    args = parse_cli_args()

    if (target_ip := args.target_ip) is None:
        print("Trying to guess target IP")
        target_ip = get_target_ip()

    mac = get_initiator_mac()
    print(create_firmware_config(Path("resources/Config.j2"), target_ip=target_ip, mac=mac))


if __name__ == "__main__":
    main()
