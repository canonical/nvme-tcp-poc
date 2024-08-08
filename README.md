### Download the installer ISO

```bash
mkdir --parents /srv/iso
wget https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso \
 --directory-prefix /srv/iso
wget https://cdimage.ubuntu.com/ubuntu-server/daily-live/20240801/oracular-live-server-amd64.iso \
 --directory-prefix /srv/iso
```

### Prepare the libvirt pool

```bash
mkdir --parents pool
virsh pool-create-as ubuntu-nvmeotcp-poc --type dir --target "$PWD/pool"
```

### Prepare the network

```bash
./setup-network.sh
```

**TODO**: Ensure that:
 * IPv4 forwarding is enabled
 * the firewall accepts forwarding to the trunk
 * packets are properly NATed

### Create the target VM

```bash
./create-target-vm.py
```

### Install Ubuntu on the initiator

```bash
./create-initiator-vm.py
```
