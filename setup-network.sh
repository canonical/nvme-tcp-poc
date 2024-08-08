#!/bin/bash

set -e

nmcli connection add \
  con-name "POC bridge" \
  ifname pocbr0 \
  type bridge \
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

virsh net-create /tmp/netdef.xml
