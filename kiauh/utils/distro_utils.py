# ======================================================================= #
#  Copyright (C) 2025 - KIAUH-arch contributors                          #
#                                                                         #
#  This file is part of KIAUH-arch - Arch Linux adaptation of KIAUH      #
#  https://github.com/wesioplayconstructor/kiauh-arch                    #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license #
# ======================================================================= #
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple

DistroId = str  # "debian" | "arch" | "unknown"


def detect_distro() -> DistroId:
    """
    Detect the current Linux distribution by checking /etc/os-release
    and available package managers.
    """
    os_release = Path("/etc/os-release")
    if os_release.exists():
        with open(os_release) as f:
            content = f.read().lower()

        if "arch linux" in content or "arch" in content:
            return "arch"
        if "debian" in content or "ubuntu" in content:
            return "debian"
        if "raspbian" in content:
            return "debian"

    # Fallback: check which package manager is available
    if _has_cmd("pacman"):
        return "arch"
    if _has_cmd("apt-get"):
        return "debian"

    return "unknown"


def _has_cmd(cmd: str) -> bool:
    return subprocess.run(
        ["which", cmd], capture_output=True
    ).returncode == 0


def has_yay() -> bool:
    return _has_cmd("yay")


def is_arch() -> bool:
    return detect_distro() == "arch"


def is_debian() -> bool:
    d = detect_distro()
    return d == "debian"


# ──────────────────────────────────────────────
# Package manager command helpers
# ──────────────────────────────────────────────

PkgManager = Dict[str, List[str]]

_ARCH_CMDS: PkgManager = {
    "update": ["sudo", "pacman", "-Sy"],
    "install": ["yay", "-S", "--noconfirm"],
    "upgrade": ["yay", "-Su", "--noconfirm"],
    "list_upgradable": ["yay", "-Qu"],
    "check_installed": ["pacman", "-Qi"],
}

_DEBIAN_CMDS: PkgManager = {
    "update": ["sudo", "apt-get", "update"],
    "install": ["sudo", "apt-get", "install", "-y"],
    "upgrade": ["sudo", "apt-get", "upgrade", "-y"],
    "list_upgradable": ["apt", "list", "--upgradable"],
    "check_installed": ["dpkg-query", "-f'${Status}'", "--show"],
}


def pkg_cmd(key: str) -> List[str]:
    """Return the base command list for a given operation."""
    if is_arch():
        return list(_ARCH_CMDS.get(key, []))
    return list(_DEBIAN_CMDS.get(key, []))


def pkg_install_cmd(packages: List[str]) -> List[str]:
    cmd = pkg_cmd("install")
    cmd.extend(packages)
    return cmd


def pkg_update_cmd() -> List[str]:
    return pkg_cmd("update")


def pkg_upgrade_cmd(packages: List[str]) -> List[str]:
    cmd = pkg_cmd("upgrade")
    cmd.extend(packages)
    return cmd


# ──────────────────────────────────────────────
# Package name mappings Debian → Arch
# ──────────────────────────────────────────────

_PACKAGE_MAP: Dict[str, str] = {
    # Global deps
    "python3-virtualenv": "python-virtualenv",
    "python3-dev": "python",
    "build-essential": "base-devel",
    "libffi-dev": "libffi",
    "libncurses-dev": "ncurses",
    "avahi-daemon": "avahi",
    "libssl-dev": "openssl",
    "libusb-1.0-0-dev": "libusb",
    "libglib2.0-dev": "glib2",
    "libgudev-dev": "libgudev",
    "libavahi-client-dev": "avahi",
    "dpkg-dev": "dpkg",
    # Python deps
    "python3": "python",
    "python3-pip": "python-pip",
    "python3-venv": "python-virtualenv",
    # nginx
    "nginx-full": "nginx-mainline",
    "nginx": "nginx-mainline",
    # system utilities
    "curl": "curl",
    "wget": "wget",
    "git": "git",
    "unzip": "unzip",
    "dfu-util": "dfu-util",
    # Klipper build deps
    "make": "make",
    "gcc": "gcc",
    "gcc-arm-none-eabi": "arm-none-eabi-gcc",
    "binutils-arm-none-eabi": "arm-none-eabi-binutils",
    "gcc-avr": "avr-gcc",
    "binutils-avr": "avr-binutils",
    "avr-libc": "avr-libc",
    "avrdude": "avrdude",
    "stm32flash": "stm32flash",
    "libnewlib-arm-none-eabi": "arm-none-eabi-newlib",
    # Dev libraries
    "libffi-dev": "libffi",
    "libncurses-dev": "ncurses",
    "libusb-dev": "libusb",
    "libusb-1.0": "libusb",
    "libusb-1.0-0": "libusb",
    "libgcc-10-dev": "",  # not needed on Arch
    "libstdc++-10-dev": "",  # not needed on Arch
    # Python
    "virtualenv": "python-virtualenv",
    "python3-dev": "python",
    "python3-numpy": "python-numpy",
    "python3-matplotlib": "python-matplotlib",
    "libopenblas-dev": "openblas",
    # Moonraker system deps
    "libopenjp2-7": "openjpeg2",
    "libsodium-dev": "libsodium",
    "zlib1g-dev": "zlib",
    "libjpeg-dev": "libjpeg-turbo",
    "wireless-tools": "wireless_tools",
    "packagekit": "packagekit",
    # Moonraker compiled Python deps (system packages for Python 3.14 compat)
    "python3-pillow": "python-pillow",
    "pillow": "python-pillow",
    # Additional Arch mappings required by KlipperScreen/Cage and sysdeps
    "python3-setuptools": "python-setuptools",
    "libyaml-dev": "libyaml",
    "pkg-config": "pkgconf",
    "xserver-xorg": "xorg-server",
    "xinit": "xorg-xinit",
    "xinput": "xorg-xinput",
    "x11-xserver-utils": "xorg-xrandr",
    "xserver-xorg-input-evdev": "xf86-input-evdev",
    "xserver-xorg-legacy": "",
    "libgtk-3-0": "gtk3",
    "libdbus-glib-1-2": "dbus-glib",
    "python3-gi": "python-gobject",
    "gir1.2-gtk-3.0": "gtk3",
    "fonts-freefont-ttf": "ttf-freefont",
    "matchbox-keyboard": "matchbox-keyboard",
    "xdotool": "xdotool",
    "cage": "cage",
    "seatd": "seatd",
}


def map_package(pkg: str) -> str:
    """Map a Debian package name to its Arch equivalent."""
    return _PACKAGE_MAP.get(pkg, pkg)


def map_packages(packages: List[str]) -> List[str]:
    """Map a list of Debian package names to Arch equivalents."""
    mapped_packages: List[str] = []
    for package in packages:
        mapped = map_package(package)
        if mapped:
            mapped_packages.append(mapped)
    return mapped_packages


def map_packages_set(packages: Set[str]) -> Set[str]:
    """Map a set of Debian package names to Arch equivalents."""
    mapped_packages: Set[str] = set()
    for package in packages:
        mapped = map_package(package)
        if mapped:
            mapped_packages.add(mapped)
    return mapped_packages


def get_global_deps() -> Set[str]:
    """Return the appropriate global dependencies for the current distro."""
    debs = {"git", "wget", "curl", "unzip", "dfu-util", "python3-virtualenv"}
    if is_arch():
        return map_packages_set(debs)
    return debs


# ──────────────────────────────────────────────
# Nginx directory / config helpers
# ──────────────────────────────────────────────

def ensure_nginx_dirs() -> List[str]:
    """
    On Arch Linux, /etc/nginx/sites-available and /etc/nginx/sites-enabled
    don"t exist by default. Create them and ensure the main nginx.conf
    includes sites-enabled/*.
    Returns a list of sudo commands run (for logging).
    """
    import subprocess
    from pathlib import Path

    commands_run: List[str] = []
    if not is_arch():
        return commands_run

    dirs = [
        Path("/etc/nginx/conf.d"),
        Path("/etc/nginx/sites-available"),
        Path("/etc/nginx/sites-enabled"),
    ]
    for d in dirs:
        if not d.exists():
            subprocess.run(["sudo", "mkdir", "-p", str(d)], check=True)
            commands_run.append(f"mkdir -p {d}")

    # Ensure nginx.conf includes conf.d and sites-enabled
    nginx_conf = Path("/etc/nginx/nginx.conf")
    if nginx_conf.exists():
        content = nginx_conf.read_text()
        confd_include = "include /etc/nginx/conf.d/*.conf;"
        sites_include = "include /etc/nginx/sites-enabled/*;"
        modified = False
        
        # Add conf.d include if missing
        if confd_include not in content:
            # Insert before sites-enabled or before closing }
            if sites_include in content:
                content = content.replace(sites_include, f"{confd_include}\n    {sites_include}")
            else:
                # Add before closing } of http block
                new_content = content.rstrip()
                if new_content.endswith("}"):
                    content = new_content[:-1] + f"\n    {confd_include}\n}}"
                else:
                    content += f"\n{confd_include}\n"
            modified = True
        
        # Add sites-enabled include if missing
        if sites_include not in content:
            new_content = content.rstrip()
            if new_content.endswith("}"):
                content = new_content[:-1] + f"\n    {sites_include}\n}}"
            else:
                content += f"\n{sites_include}\n"
            modified = True
        
        if modified:
            # Write with sudo via tempfile
            tmp = Path("/tmp/_kiauh_nginx_conf")
            tmp.write_text(content)
            subprocess.run(["sudo", "cp", str(tmp), str(nginx_conf)], check=True)
            tmp.unlink()
            if confd_include in content:
                commands_run.append(f"Added '{confd_include}' to nginx.conf")
            if sites_include in content:
                commands_run.append(f"Added '{sites_include}' to nginx.conf")

    return commands_run
