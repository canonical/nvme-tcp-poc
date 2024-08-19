# NVMe/TCP booting Ubuntu Server (PoC)

The instructions in this proof of concept (PoC) will guide you through the
steps to demonstrate the use of NVMe over TCP on Ubuntu, using two virtual
machines on an Ubuntu Desktop 24.04 host system.

The PoC uses libvirt to manage the VMs and uses KVM as the hypervisor. It is
meant to be run on an x86_64 system.

The first VM (a.k.a., the NVMe target VM) will run Ubuntu Server 24.04 and will
be responsible for exposing a NVMe drive over TCP.

Theoretically speaking, there is no need for the NVMe target system to run a
specific version of Ubuntu, or even a specific OS. If you already have an
available system exposing a NVMe drive over TCP, it should be usable for the
PoC without deviating too much from the instructions. In this document, we will
assume that the NVMe target system was created using the instructions below ;
but if you feel like experimenting, here's a non-exhaustive list of
expectations for the NVMe target system:

 * the system runs the qemu-guest-agent daemon
 * the NVMe drive is exposed using TCP port 4420 (some of the scripts accept a
   --target-port but not all)
 * the network interface on the system is called enp1s0
 * the libvirt domain name for the system is "ubuntu-nvmeotcp-poc-target"

The second VM (a.k.a., the NVMe initiator VM) will be a disk-less system
running Ubuntu Server 24.10 (or Ubuntu 24.04.x in the future) using the NVMe
drive exposed on the network.

## Prerequisites

### Install the required packages on the host

Install all the dependencies on the host to run the PoC.

At the time of writing, there is a bug in virt-install preventing it from
installing Ubuntu in a fully automated way (see [bug
2073461](https://bugs.launchpad.net/ubuntu/+source/virt-manager/+bug/2073461)).
A fix is available in the PPA
[ppa:ogayot/nvme-o-tcp](https://launchpad.net/~ogayot/+archive/ubuntu/nvme-o-tcp).

```bash
sudo add-apt-repository ppa://ogayot/nvme-o-tcp
```

```bash
sudo apt install \
  libvirt-daemon libvirt-clients virtinst virt-viewer virt-manager qemu-system-x86 \
  libcap2-bin \
  wget \
  python3-jinja2 python3-yaml
```

### Download the installer ISOs

Download the necessary installer ISOs. Ubuntu 24.04 will be installed on the
NVMe target VM whereas Ubuntu 24.10 will be installed on the NVMe initiator VM.

```bash
sudo mkdir --parents /srv/iso
sudo chown -- "$UID" /srv/iso
wget https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso \
 --directory-prefix /srv/iso
wget https://cdimage.ubuntu.com/ubuntu-server/daily-live/current/oracular-live-server-amd64.iso \
 --directory-prefix /srv/iso
```

### Prepare the libvirt pool

```bash
mkdir --parents pool
virsh pool-define-as ubuntu-nvmeotcp-poc --type dir --target "$PWD/pool"
virsh pool-autostart ubuntu-nvmeotcp-poc
virsh pool-start ubuntu-nvmeotcp-poc
```

### Prepare the network

```bash
./setup-network.sh
```

**TODO**: Ensure that:
 * the firewall accepts forwarding to the trunk
 * packets are properly NATed when using IPv4

### Optional: setting up virt-manager for the PoC

Run `virt-manager` once to make it connect to the QEMU/KVM User session:

```bash
virt-manager qemu:///session
```

The VMs that will soon be created will now be visible in `virt-manager`. We can
use this tool to start, stop, delete and edit VMs. Everything can also be done
directly using `virsh`.

## Create the VMs

### Create and setup the target VM

The setup to deploy the target VM uses Subiquity's autoinstall directives and
should be entirely automated. Wait until the VM shuts down.

```bash
./create-target-vm.py
```

Now start the VM (using virt-manager or the command below) and move on to the
next step:

```bash
virsh start ubuntu-nvmeotcp-poc-target
```

### Create and setup the initiator VM

The setup to deploy the initiator VM is assisted (NVMe drives discovery happens
in the background) but not automated. To deploy this VM you need to run the command below:

```bash
./create-initiator-vm.py
```

And then follow the normal steps to install Ubuntu Server:

1. Go through the language and keyboard selection screens as you would like.
2. On the source selection screen, select "Ubuntu Server (minimized)" and
   uncheck the "Search for third-party drivers" checkbox. This is optional but
   will speed up the installation.
3. Go through the network, proxy and mirror screens as you would like.
4. When reaching the "Guided storage configuration screen", select "Custom Storage layout".
5. On the next screen, ensure no partitions already exist on the NVMe/TCP
   drive. Otherwise select the drive and choose "Reformat".
6. Select the free space and choose "Add GPT Partition" (you can leave the
   default settings and hit "Create").
7. Ensure the summary at the top shows two partitions (i.e., "/" and
   "/boot/efi") to be created on the NVMe/TCP drive.
8. Move on to the next screen and confirm the changes when asked.
9. Go through the next screens normally and wait for the installation to finish.
10. When the "Installation complete!" screen is shown, select "Reboot now".
11. If the VM does not completely shut down, you can use virt-manager to force
    it off. See the "Known issues" section at the end of this document.

### Configure the firmware

TODO

## Known issues

 * "When installing the target VM, the installer waits for me to select a language instead of running automatically.". This should be addressed by installing the virtinst package from the [ogayot/nvme-o-tcp PPA](https://launchpad.net/~ogayot/+archive/ubuntu/nvme-o-tcp). See [bug 2073461](https://bugs.launchpad.net/ubuntu/+source/virt-manager/+bug/2073461).

 * "I chose "Use an entire disk" instead of "Custom storage layout" and ended up with a system that does not boot.". Please use "Custom storage layout" for now. The progress is tracked in [bug 2073119](https://bugs.launchpad.net/subiquity/+bug/2073119).
 * The installer removes dracut and reinstalls initramfs-tools at the end of the installation. See [bug 2073125](https://bugs.launchpad.net/subiquity/+bug/2073125). There is a workaround in the PoC (see resources/cc-initiator.yaml) to reinstall dracut after it gets removed.
 * Installing dracut removes the `ubuntu-server` metapackage. There is no workaround or fix for now but it should not affect the usability of the installed system.
 * The initiator VM takes forever to shutdown. There is no workaround or fix for now. You can use the "Force Off" button with virt-manager.
