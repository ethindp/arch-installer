import sys
import os
import subprocess
import socket
import shlex
import json
import shutil
import platform
import tempfile

# executes the given command, but does not display output.
def run(command: str, rshell: bool=False):
	proc=subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=rshell)
	if proc.returncode!=0: # assume failure
		print ("The following command failed when executed:")
		print(command)
		if click.confirm("Would you like to view the processes output?"):
			print(proc.stdout.decode())
			print(proc.stderr.decode())
		if not click.confirm("Would you like to continue the installation process?"):
			sys.exit(0)

# Does same thing as run() but returns output
def execute(command: str, rshell: bool=False)->tuple:
	proc=subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=rshell)
	if proc.returncode!=0: # assume failure
		print ("The following command failed when executed:")
		print(command)
		if click.confirm("Would you like to view the processes output?"):
			print(proc.stdout.decode())
			print(proc.stderr.decode())
		if not click.confirm("Would you like to continue the installation process?"):
			sys.exit(0)
	else:
		return (proc.stdout.decode(), proc.stderr.decode())

print ("Installing modules that you may find useful")
run("pip install console-menu click wifi")
from consolemenu import *
from consolemenu.items import *
import click
de_packages=[]
dm=-1
if click.confirm("Would you like to install a desktop environment?"):
	menu=SelectionMenu(['Budgie', 'Cinnamon', 'Deepin', 'Enlightenment', 'GNOME Flashback', 'Gnome', 'KDE', 'KDE Plasma', 'Kodi', 'LXDE (GTK2)', 'LXDE (GTK3)', 'LXQT', 'Mate', 'Pantheon', 'Sugar', 'XFCE'], title="Select a desktop environment to install")
	menu.show(False)
	selection=menu.selected_item.index
	if selection==0:
		de_packages.append("budgie-desktop")
	elif selection==1:
		de_packages.append("cinnamon")
	elif selection==2:
		de_packages.extend(["deepin", "deepin-extra"])
	elif selection==3:
		de_packages.append("enlightenment")
	elif selection==4:
		de_packages.extend(["gnome-flashback", "gnome-applets", "sensors-applet", "gnome", "gnome-backgrounds", "gnome-control-center", "gnome-screensaver", "network-manager-applet", "orca"])
	elif selection==5:
		de_packages.extend(["gnome", "gnome-extra", "orca"])
	elif selection==6:
		de_packages.extend(["kde-applications", "kdeaccessibility", "kdeadmin", "kdebase", "kdebindings", "kdeedu", "kdegames", "kdegraphics", "kdemultimedia", "kdenetwork", "kdepim", "kdesdk", "kdeutils", "kdewebdev"])
	elif selection==7:
		de_packages.extend("plasma")
	elif selection==8:
		de_packages.extend(["kodi", "kodi-addons", "orca"])
		dm=5
	elif selection==9:
		de_packages.extend(["lxde", "orca"])
	elif selection==10:
		de_packages.extend(["lxde-gtk3", "orca"])
	elif selection==11:
		de_packages.extend(["lxqt", "orca"])
	elif selection==12:
		de_packages.extend(["mate", "mate-extra", "orca"])
	elif selection==13:
		de_packages.extend(["pantheon"])
	elif selection==14:
		de_packages.extend(["sugar", "sugar-fructose"])
	elif selection==15:
		de_packages.extend(["xfce4", "xfce4-goodies"])
	de_packages.extend(["xorg", "xorg-apps", "xorg-drivers", "xorg-fonts"])
	de_packages.sort()
	print ("Installing selected environment")
	run(f"""pacman -Syu {" ".join(de_packages)} --noconfirm""")

if click.confirm("Would you like to add any other packages to the system?"):
	print("Enter all packages separated by a space.")
	packages=click.prompt("Packages to add")
	print (f"Installing {shlex.split(packages)} packages...")
	run(f"pacman -Syu {packages} --noconfirm")

print ("Setting timezone to default")
if os.path.exists("/etc/localtime"):
	os.remove("/etc/localtime")
run("ln -sf /usr/share/zoneinfo/America/Chicago /etc/localtime")
run("hwclock --systohc")
while True:
	print ("These are the settings for your current time/date configuration:")
	print(execute("timedatectl")[0])
	if click.confirm("Would you like to change them?"):
		tzs=execute("timedatectl list-timezones")[0].split()
		fd, fname=tempfile.mkstemp(text=True)
		with os.fdopen(fd, "w") as f:
			f.write("The following timezones are available:\n")
			for count, tz in enumerate(tzs):
				f.write(f"{count}: {tz}\n")
			f.flush()
			os.fsync(f.fileno())
		os.close(fd)
		subprocess.run(f"less -- {fname}")
		while True:
			tzid=click.prompt(f"Enter timezone number (1-{len(tzs)}")
			if tzid<1 or tzid>len(tzs):
				print ("Error: invalid timezone number")
				continue
			else:
				run(f"timedatectl set-timezone {tzs[tzid-1]}")
				break
	else:
		break
print ("Setting and generating locale")
run("sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen")
run("locale-gen")
with open("/etc/locale.conf", "w") as f:
	f.write("LANG=en_US.UTF-8")

if click.confirm("Would you like to set a system hostname?"):
	hostname=click.prompt("Enter system hostname")
	with open("/etc/hostname", "w") as f:
		f.write(hostname)

print ("Please specify the root password when prompted.")
subprocess.run("passwd")
if click.confirm("Would you like to enable microcode updates for this system?"):
	if platform.processor().lower().find("intel"):
		print ("Enabling Intel microcode updates")
		run("pacman -S intel-ucode --noconfirm")
	elif platform.processor().lower().find("amd"):
		print ("Enabling AMD microcode updates")
		run("pacman -S amd-ucode --noconfirm")
	else:
		print ("Processor does not need microcode updates, skipping")

print ("Installing boot loader")
if os.path.exists("/sys/firmware/efi") or os.path.exists("/sys/firmware/efi/efivars") or os.path.exists("/sys/firmware/efi/vars"):
	if platform.architecture()[0]=="64bit":
		run("grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB")
	elif platform.architecture()[0]=="32bit":
		run("grub-install --target=i386-efi --efi-directory=/boot --bootloader-id=GRUB")
	else:
		print("Error: unknown CPU architecture!")
		sys.exit(0)
else:
	run(f"grub-install --target=i386-pc {sys.argv[1]}")

if click.confirm("Would you like to modify the grub configuration file (/etc/default/grub)?"):
	print ("Opening grub configuration file. When done, save with ctrl+x.")
	print ("The installation procedure will continue as soon as Nano is closed.")
	subprocess.run(shlex.split("nano /etc/default/grub"))
print ("Generating boot loader configuration")
run("grub-mkconfig -o /boot/grub/grub.cfg")
print ("Creating administrative user accounts")
users=[]
while True:
	username=input("Username: ")
	run(f"useradd -m -g users -G power,storage,wheel -s /bin/bash {username}")
	subprocess.call(["passwd", username])
	users.append(username)
	if not click.confirm("Add another?"):
		break

if click.confirm("Modify sudoers file for administrator accounts?"):
	print ("Opening sudoers file in Nano. When done, press ctrl+x.")
	print ("The installation will continue immediately thereafter.")
	os.environ["EDITOR"]="nano"
	subprocess.run(["visudo"])
if len(de_packages)>0:
	if click.confirm("Would you like to boot into a display manager/desktop environment? Do not say yes if you wish to use Kodi standalone."):
		menu=SelectionMenu(["GDM", "LightDM", "LXDM", "SDDM", "XDM", "Kodi"], title="Select a display manager to install")
		menu.show(False)
		dm=menu.selected_item.index
		if menu.selected_item.index==0:
			run("pacman -Syu gdm --noconfirm")
			run("systemctl enable gdm")
		elif menu.selected_item.index==1:
			run("pacman -Syu lightdm --noconfirm")
			run("systemctl enable lightdm")
		elif menu.selected_item.index==2:
			run("pacman -Syu lxdm --noconfirm")
			run("systemctl enable lxdm")
		elif menu.selected_item.index==3:
			run("pacman -Syu sddm --noconfirm")
			run("systemctl enable sddm")
		elif menu.selected_item.index==4:
			run("pacman -Syu xorg-xdm --noconfirm")
			run("systemctl enable xdm")
if click.confirm("Would you like to enable orca accessibility?"):
	print ("Enabling Mate accessibility for all non-root users")
	run("pacman -Syu orca --noconfirm")
	for user in users:
		run(f"runuser --user {user} -- gsettings set org.mate.interface accessibility true")
	run(f"runuser --user {user} -- gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled true")

if click.confirm("Would you like to enable AUR support?"):
	print ("Enabling AUR support with Yay")
	run("pacman -U /yay-9.1.0-1-x86_64.pkg.tar.xz --noconfirm")
	os.remove("/yay-9.1.0-1-x86_64.pkg.tar.xz")
else:
	os.remove("/yay-9.1.0-1-x86_64.pkg.tar.xz")

if click.confirm("Would you like to enable a console screen reader? This will disable desktop environment support, but will leave your desktop environment as is."):
	menu=SelectionMenu(["Speakup", "Fenrir"], title="Select a console screen reader to enable")
	menu.show(False)
	if menu.selected_item.index==0:
		print ("Enabling speakup")
		print ("Installing espeakup and speakup-utils")
		run("pacman -Syu espeakup speakup-utils --noconfirm")
		print ("Disabling display manager")
		if dm==0:
			run("systemctl disable gdm")
		elif dm==1:
			run("systemctl disable lightdm")
		elif dm==2:
			run("systemctl disable lxdm")
		elif dm==3:
			run("systemctl disable sddm")
		elif dm==4:
			run("systemctl disable xdm")
		print ("Enabling espeakup service")
		run("systemctl enable espeakup")
	elif menu.selected_item.index==1:
		print ("Enabling fenrir")
		print ("Installing dependencies")
		run("pacman -Syu python-dbus-common python-wcwidth python-daemonize python-dbus python-evdev python-pyte python-pyudev python-pyenchant sox espeak aspell aspell-de aspell-en aspell-es aspell-fr aspell-nl aspell-ca aspell-cs aspell-el aspell-hu aspell-it aspell-pl aspell-pt aspell-ru aspell-sv aspell-uk --noconfirm")
		print ("InstallingFenrir")
		run("pacman -U /fenrir-1.9.5-1-any.pkg.tar.xz --noconfirm")
		os.remove("/fenrir-1.9.5-1-any.pkg.tar.xz")
		print ("Disabling display manager")
		if dm==0:
			run("systemctl disable gdm")
		elif dm==1:
			run("systemctl disable lightdm")
		elif dm==2:
			run("systemctl disable lxdm")
		elif dm==3:
			run("systemctl disable sddm")
		elif dm==4:
			run("systemctl disable xdm")
		print ("Copying ISO settings file")
		os.remove("/etc/fenrirscreenreader/settings/settings.conf")
		shutil.move("/settings.conf", "/etc/fenrirscreenreader/settings")
		print ("Installing pip modules")
		run("pip install pyttsx3 pexpect")
		print ("Enabling fenrirscreenreader service")
		run("systemctl enable fenrirscreenreader")
else:
	os.remove("/fenrir-1.9.5-1-any.pkg.tar.xz")
	os.remove("/settings.conf")

print ("Main installation complete!")
