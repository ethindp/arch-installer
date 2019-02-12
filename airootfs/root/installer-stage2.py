import sys
import os
import subprocess
import shlex
import shutil
import platform
import tempfile


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


print("Installing required python modules")
run("pip install console-menu click netifaces")
from consolemenu import SelectionMenu
import click
import netifaces


DE_PACKAGES = []
DM = -1
if click.confirm("Would you like to install a desktop environment?"):
    MENU = SelectionMenu(['Gnome', 'LXDE (GTK2)', 'LXDE (GTK3)', 'Mate'], title="Select a desktop environment to install")
    MENU.show(False)
    SELECTION = MENU.selected_item.index
    DM = MENU.selected_item.index
    DE_PACKAGES.extend(["xorg", "xorg-apps", "xorg-drivers", "xorg-fonts"])
    if SELECTION == 0:
        DE_PACKAGES.extend(["gnome", "gnome-extra", "orca"])
    elif SELECTION == 1:
        DE_PACKAGES.extend(["lxde", "orca"])
    elif SELECTION == 2:
        DE_PACKAGES.extend(["lxde-gtk3", "orca"])
    elif SELECTION == 3:
        DE_PACKAGES.extend(["mate", "mate-extra", "orca"])
    DE_PACKAGES.sort()
    print("Installing selected desktop environment")
    run(f"""pacman -Syu {" ".join(DE_PACKAGES)} --noconfirm""")

if click.confirm("Would you like to add any other packages to the system?"):
    print("Enter all packages separated by a space.")
    PACKAGES = click.prompt("Packages to add")
    print(f"Installing {shlex.split(PACKAGES)} packages...")
    run(f"pacman -Syu {PACKAGES} --noconfirm")

print("Setting timezone to default")
if os.path.exists("/etc/localtime"):
    os.remove("/etc/localtime")
run("ln -sf /usr/share/zoneinfo/America/Chicago /etc/localtime")
run("hwclock --systohc")
while True:
    print("These are the settings for your current time/date configuration:")
    print(execute("timedatectl")[0])
    if click.confirm("Would you like to change them?"):
        TZS = execute("timedatectl list-timezones")[0].split()
        FD, FNAME = tempfile.mkstemp(text=True)
        with os.fdopen(FD, "w") as f:
            f.write("The following timezones are available:\n")
            for count, tz in enumerate(TZS, start=0):
                f.write(f"{count+1}: {tz}\n")
            f.flush()
            os.fsync(f.fileno())
        try:
            os.close(FD)
        except OSError:
            pass
        subprocess.run(shlex.split(f"less -- {FNAME}"))
        while True:
            TZID = click.prompt(f"Enter timezone number (1-{len(TZS)}")
            if int(TZID) < 1 or int(TZID) > len(TZS):
                print("Error: invalid timezone number")
                continue
            else:
                run(f"timedatectl set-timezone {TZS[TZID-1]}")
                break
    else:
        break

print("Setting and generating locale")
run("sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen")
run("locale-gen")
with open("/etc/locale.conf", "w") as f:
    f.write("LANG=en_US.UTF-8")

if click.confirm("Would you like to set a system hostname?"):
    HOSTNAME = click.prompt("Enter your hostname")
    with open("/etc/hostname", "w") as f:
        f.write(HOSTNAME)

print("Please specify the root password when prompted:")
subprocess.run("passwd")
if click.confirm("Would you like to enable microcode updates for this system?"):
    if platform.processor().lower().find("intel"):
        print("Enabling Intel microcode updates")
        run("pacman -S intel-ucode --noconfirm")
    elif platform.processor().lower().find("amd"):
        print("Enabling AMD microcode updates")
        run("pacman -S amd-ucode --noconfirm")
    else:
        print("Processor does not need microcode updates, skipping")

print("Installing boot loader")
if os.path.exists("/sys/firmware/efi") or os.path.exists("/sys/firmware/efi/efivars") or os.path.exists("/sys/firmware/efi/vars"):
    if platform.architecture()[0] == "64bit":
        run("grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB")
    elif platform.architecture()[0] == "32bit":
        run("grub-install --target=i386-efi --efi-directory=/boot --bootloader-id=GRUB")
    else:
        print("Error: unknown CPU architecture!")
        sys.exit(0)
else:
    run(f"grub-install --target=i386-pc {sys.argv[1]}")

if click.confirm("Would you like to modify the grub configuration file (/etc/default/grub)?"):
    print("Opening grub configuration file. When done, save with ctrl+x.")
    print("The installation procedure will continue as soon as Nano is closed.")
    subprocess.run(shlex.split("nano /etc/default/grub"))
print("Generating boot loader configuration")
run("grub-mkconfig -o /boot/grub/grub.cfg")
print("Creating administrative user accounts")
USERS = []
while True:
    USERNAME = click.prompt("Username")
    PROC = subprocess.run(shlex.split(f"useradd -m -g users -G power,storage,wheel -s /bin/bash {USERNAME}"))
    if PROC.returncode != 0:
        print("Error: invalid username specification; user was not added to system. Please try again.")
        continue
    else:
        subprocess.call(["passwd", USERNAME])
        USERS.append(USERNAME)
        if not click.confirm("Add another?"):
            break

if click.confirm("Modify sudoers file for administrator accounts?"):
    print("Opening sudoers file in Nano. When done, press ctrl+x.")
    print("The installation will continue immediately thereafter.")
    os.environ["EDITOR"] = "nano"
    subprocess.run(["visudo"])
if DE_PACKAGES:
    if click.confirm("Would you like to boot into a display manager/desktop environment?"):
        if DM == 0:
            print("Enabling GDM as display manager")
            run("systemctl enable gdm")
        elif DM in (1, 2):
            print("Enabling LXDM as display manager")
            run("systemctl enable lxdm")
        elif DM == 3:
            print("Enabling LightDM as display manager")
            run("pacman -Syu lightdm --noconfirm")
            run("systemctl enable lightdm")

if click.confirm("Would you like to enable orca accessibility?"):
    print("Enabling orca accessibility for all non-root users")
    run("pacman -Syu orca --noconfirm")
    run("gsettings set org.gnome.desktop.interface toolkit-accessibility true")
    for user in USERS:
        run(f"runuser --user {user} -- gsettings set org.mate.interface accessibility true")
        run(f"runuser --user {user} -- gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled true")

if click.confirm("Would you like to enable AUR support?"):
    print("Enabling AUR support with Yay")
    run("pacman -U /yay-9.1.0-1-x86_64.pkg.tar.xz --noconfirm")
    os.remove("/yay-9.1.0-1-x86_64.pkg.tar.xz")
else:
    os.remove("/yay-9.1.0-1-x86_64.pkg.tar.xz")

if click.confirm("Would you like to enable a console screen reader? This will disable the currently enabled display manager."):
    MENU = SelectionMenu(["Speakup", "Fenrir"], title="Select a console screen reader to enable")
    MENU.show(False)
    if MENU.selected_item.index == 0:
        print("Enabling speakup")
        print("Installing espeakup and speakup-utils")
        run("pacman -Syu espeakup speakup-utils --noconfirm")
        print("Disabling display manager")
        if DM == 0:
            run("systemctl disable gdm")
        elif DM in (1, 2):
            run("systemctl disable lxdm")
        elif DM == 3:
            run("systemctl disable lightdm")
        print("Enabling espeakup service")
        run("systemctl enable espeakup")
    elif MENU.selected_item.index == 1:
        print("Enabling fenrir")
        print("Installing dependencies")
        run("pacman -Syu python-dbus-common python-wcwidth python-daemonize python-dbus python-evdev python-pyte python-pyudev python-pyenchant sox espeak-ng aspell aspell-de aspell-en aspell-es aspell-fr aspell-nl aspell-ca aspell-cs aspell-el aspell-hu aspell-it aspell-pl aspell-pt aspell-ru aspell-sv aspell-uk --noconfirm")
        print("InstallingFenrir")
        run("pacman -U /fenrir-1.9.5-1-any.pkg.tar.xz --noconfirm")
        os.remove("/fenrir-1.9.5-1-any.pkg.tar.xz")
        print("Disabling display manager")
        if DM == 0:
            run("systemctl disable gdm")
        elif DM in (1, 2):
            run("systemctl disable lxdm")
        elif DM == 3:
            run("systemctl disable lightdm")
        print("Copying ISO settings file")
        os.remove("/etc/fenrirscreenreader/settings/settings.conf")
        shutil.move("/settings.conf", "/etc/fenrirscreenreader/settings")
        print("Installing pip modules")
        run("pip install pyttsx3 pexpect")
        print("Enabling fenrirscreenreader service")
        run("systemctl enable fenrirscreenreader")
else:
    os.remove("/fenrir-1.9.5-1-any.pkg.tar.xz")
    os.remove("/settings.conf")

# Make sure the system is audible when it boots.
run("amixer sset Master 100%")
run("alsactl store")

# as dhcpcd has become more prevalent, automatically enable it for all network interfaces
print("Configuring network interfaces")
if subprocess.run("pacman -Qsq dhcpcd", stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
    run("pacman -Syu dhcpcd --noconfirm")
for interface in netifaces.interfaces():
    if interface.lower() == "lo":
        continue
    run(f"systemctl enable dhcpcd@{interface}")

print("Main installation complete!")
