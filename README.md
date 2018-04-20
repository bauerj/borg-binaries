# ARM builds for borg binaries

These scripts are used to generate the binaries on borg.bauerj.eu.
Everything is just hacked together but if you really want to use these scripts yourself:

## Prerequisites
You need to set up at least the following in order to use the scripts:

* SSH access to a system running the target architecture.
This could be a real device or a QEMU VM (I use a VM but it's very slow).
The systems should run Debian wheezy with:
  * pyenv installed for root
  * `build-essential`
  * git
* Modify the start and stop commands in `build.py` if you use something else to start the VMs or don't use VMs.
* Modify the host names and ports in `build.py`.

This is probably incomplete. If you find something missing, please open a PR.

## `check_release.py`
This script just checks if a binary for the current version already exists.
It is used in a systemd timer to start `build.py`.

## `build.py`
This is used to start the build. You can pass a tag name or commit hash to it to build that instead of the latest tag.
It uses systemd to start the VMs and SSH to log into them.

## `build_on_device.py`
As the name suggests, this script runs inside the VM to actually build the binary.