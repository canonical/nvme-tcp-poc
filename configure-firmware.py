#!/usr/bin/env python3

import tempfile
from pathlib import Path

import jinja2

from ubuntu_nvme_tcp_poc import get_initiator_mac, get_target_ip


def render_config_template(template: Path, *, target_ip: str, mac: str) -> str:
    with template.open(encoding="utf-8") as template_stream:
        template = jinja2.Template(template_stream.read())

    context = {
        "targetip": target_ip,
        "targetport": "4420",
        "mac": mac,
    }

    return template.render(context)


def create_firmware_config(template: Path, **kwargs) -> Path:
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as stream:
        stream.write(render_config_template(template, **kwargs))
    return Path(stream.name)


def main() -> None:
    target_ip = get_target_ip()
    mac = get_initiator_mac()
    print(create_firmware_config(Path("resources/Config.j2"), target_ip=target_ip, mac=mac))


if __name__ == "__main__":
    main()
