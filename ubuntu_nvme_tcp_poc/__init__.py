import ipaddress
import subprocess


def get_target_ip() -> str:
    out = subprocess.check_output(
        ["virsh", "domifaddr", "ubuntu-nvmeotcp-poc-target", "--source", "agent", "--full"],
        text=True)

    for line in out.splitlines():
        if line.strip().startswith("enp1s0"):
            ip_with_cidr = ipaddress.ip_interface(line.strip().split()[-1])
            return str(ip_with_cidr.ip)
    raise ValueError("Could not determine IP address of NVMe target")
