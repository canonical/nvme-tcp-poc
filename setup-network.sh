#!/bin/bash

set -e

if [ "$(sysctl --values net.ipv4.ip_forward)" -ne 1 ]; then
    echo "IPv4 forwarding is not enabled, please ensure to enable it using the following command:" >&2
    echo "sudo sysctl net.ipv4.ip_forward=1" >&2
    exit 1
fi

if [ "$(sysctl --values net.ipv6.conf.all.forwarding)" -ne 1 ]; then
    echo "IPv6 forwarding is not enabled, please ensure to enable it using the following command:" >&2
    echo "sudo sysctl net.ipv6.conf.all.forwarding=1" >&2
    exit 1
fi

nmcli connection add \
  con-name "POC bridge" \
  ifname pocbr0 \
  type bridge \
  autoconnect yes \
  ipv4.method shared \
  ipv6.method ignore

sudo setcap cap_net_admin+ep /usr/lib/qemu/qemu-bridge-helper
sudo mkdir --parents /etc/qemu
echo "allow pocbr0" | sudo dd of=/etc/qemu/bridge.conf

cat > /tmp/netdef.xml <<EOF
<network>
  <name>poc-network</name>
  <forward mode="bridge"/>
  <bridge name="pocbr0"/>
</network>
EOF

virsh --connect qemu:///session net-define /tmp/netdef.xml
virsh --connect qemu:///session net-start poc-network
virsh --connect qemu:///session net-autostart poc-network
