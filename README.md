# arch-installer
Installation program for Arch Linux to assist in the installation of the system

This repository is a modified duplicate of the Talking Arch ISO. To build the ISO for yourself:

* Grab the talkingarch-git package from the AUR and keep it up to date. (This package is provided. To build, run makepkg -si in the talkingarch-git repository as a nonprivileged user. Alternatively, use vagrant, as described below.)
* clone the repository
* make changes (if you like)
* run ./build.sh

The installer is located at airootfs/root/installer.py. Stage II is located at airootfs/root/installer-stage2.py.

## Cloning with vagrant

* Install vagrant.
* Run the following command:

```
vagrant init https://the-gdn.net/GDNXbuild.box
```


* Type vagrant up to boot the VM
* SSH into the VM, sudo su -, and remove tarch. Then clone the repository and follow the steps above.
