#!/usr/bin/env python3

import argparse
import contextlib
from pathlib import Path
import shutil
import subprocess
import tempfile
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


@contextlib.contextmanager
def fuse_mount(source: Path, mountpoint: Path):
    subprocess.run(["fusefat", source, mountpoint, "-o", "rw+"], check=True)
    try:
        yield
    finally:
        subprocess.run(["fusermount", "-u", mountpoint], check=True)


@contextlib.contextmanager
def create_efidisk(config: Path) -> Path:
    with tempfile.TemporaryDirectory() as tempdir_s:
        tempdir = Path(tempdir_s)
        efidisk = tempdir / "efidisk.img"
        efipart = tempdir / "efipart.img"
        subprocess.run(["dd", "if=/dev/zero", f"of={efidisk}", "bs=1M", "count=21"], check=True)
        with Path("resources/sfdisk-script").open() as script:
            subprocess.run(["sfdisk", efidisk], check=True, stdin=script)
        # Gymnastics to avoid needing root. fusefat does not accept offsets.
        subprocess.run(["dd", "if=/dev/zero", f"of={efipart}", "bs=1M", "count=20"], check=True)
        subprocess.run(["mkfs.vfat", efipart], check=True)
        (tempdir / "mnt").mkdir()
        with fuse_mount(efipart, tempdir / "mnt"):
            bootdir = tempdir / "mnt/EFI/BOOT"
            bootdir.mkdir(parents=True)
            shutil.copyfile("resources/NvmeOfCli.efi", bootdir / "NvmeOfCli.efi")
            shutil.copyfile("resources/startup.nsh", bootdir / "startup.nsh")
            shutil.copyfile(config, bootdir / "Config")

        subprocess.run(
                ["dd",
                 f"if={efipart}",
                 f"of={efidisk}",
                 "bs=512", "seek=2048", "conv=notrunc"], check=True)
        yield efidisk


def main() -> None:
    args = parse_cli_args()

    if (target_ip := args.target_ip) is None:
        print("Trying to guess target IP")
        target_ip = get_target_ip()

    mac = get_initiator_mac()
    config_path = create_firmware_config(Path("resources/Config.j2"), target_ip=target_ip, mac=mac)

    with create_efidisk(config_path) as efidisk:
        pass

if __name__ == "__main__":
    main()
