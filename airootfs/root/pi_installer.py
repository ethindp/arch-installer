"""Raspberry pi flashing utility
Copyright (C) 2019 The FreeOS project and its developers and contributors
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

Flashes raspberry pi images to an SD card. Borrows components from the installer stage 1 program."""
import sys
import os
import subprocess
import socket
import shlex
import json
import shutil
import requests
import click
from consolemenu import SelectionMenu


# executes the given command, but does not display output.
def run(command: str, rshell: bool = False):
    proc = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=rshell)
    if proc.returncode != 0:  # assume failure
        print("The following command failed when executed:")
        print(command)
        if click.confirm("Would you like to view the processes output?"):
            print(proc.stdout.decode())
            print(proc.stderr.decode())
        if not click.confirm("Would you like to continue the installation process?"):
            sys.exit(0)


# Does same thing as run() but returns output
def execute(command: str, rshell: bool = False) -> tuple:
    proc = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=rshell)
    if proc.returncode != 0:  # assume failure
        print("The following command failed when executed:")
        print(command)
        if click.confirm("Would you like to view the processes output?"):
            print(proc.stdout.decode())
            print(proc.stderr.decode())
        if not click.confirm("Would you like to continue the installation process?"):
            sys.exit(0)
            return (None, None)
    else:
        return (proc.stdout.decode(), proc.stderr.decode())

# First let's make sure we can be heard.
run("amixer sset Master 100%")
# Step 1 - determine that we are connected to the internet
try:
    socket.gethostbyname("google.com")
except socket.gaierror:
    print("You are not connected to the internet. Please connect to the internet first to continue.")
    sys.exit(1)

DISK_JSON = json.loads(execute("lsblk -dJO")[0])
DISKS = []
for blockdevice in DISK_JSON["blockdevices"]:
    DISKS.append(f"""{blockdevice["name"].upper()}: {blockdevice["path"]}, {blockdevice["size"]}""")

MENU = SelectionMenu(DISKS, title="Select SD Card to flash")
MENU.show(False)

DISK = DISK_JSON["blockdevices"][MENU.selected_item.index]["path"]
print("Partitioning disk")
run(f"parted -s {DISK} -- mklabel msdos")
run(f"parted -s {DISK} -- mkpart primary fat32 0% 100MB")
run(f"parted -s {DISK} -- mkpart primary ext4 100MB 100%")
run(f"parted -s {DISK} -- set 1 lba on")
print("Setting up filesystems")
run(f"mkfs.vfat {DISK}1")
run(f"mkfs.ext4 -F {DISK}2")
if os.path.exists("boot"):
    shutil.rmtree("boot")

if os.path.exists("root"):
    shutil.rmtree("root")

run(f"mount {DISK}1 boot")
run(f"mount {DISK}2 root")
print("Downloading Arch Linux ARM package")
ARCHLINUX_RPI = requests.get("http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-latest.tar.gz").content
ARCHLINUX_RPI_CHECKSUM = requests.get("http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-latest.tar.gz.md5").content

with open("ArchLinuxARM-rpi-latest.tar.gz", "wb") as f:
    f.write(ARCHLINUX_RPI)


with open("ArchLinuxARM-rpi-latest.tar.gz.md5", "wb") as f:
    f.write(ARCHLINUX_RPI_CHECKSUM)


run("sync")
print("Verifying package integrity")
PROC = subprocess.run(shlex.split("md5sum --quiet --status -c ArchLinuxARM-rpi-latest.tar.gz.md5"))
if (PROC.returncode!=0:
    if not click.confirm("The integrity of this package is questionable and its checksum does not match the checksum on the arch linux arm website. Are you sure you want to flash this image?"):
        print("Aborting.")
        sys.exit(1)


print("Extracting image")
run("bsdtar -xpf ArchLinuxARM-rpi-latest.tar.gz -C root")
run("sync")
print("Moving boot files to boot partition")
run("mv root/boot/* boot")
print("Unmounting partitions")
run("umount boot root")
print("Arch linux ARM has been fully installed to your SD Card. Unplug the SD card and plug it into your pi and SSHin with the username alarm and password alarm.")
