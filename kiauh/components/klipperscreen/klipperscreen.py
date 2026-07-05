# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import os
import shutil
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run
from typing import List

from components.klipper.klipper import Klipper
from components.klipperscreen import (
    KLIPPERSCREEN_DIR,
    KLIPPERSCREEN_ENV_DIR,
    KLIPPERSCREEN_INSTALL_SCRIPT,
    KLIPPERSCREEN_LOG_NAME,
    KLIPPERSCREEN_REPO,
    KLIPPERSCREEN_REQ_FILE,
    KLIPPERSCREEN_SERVICE_FILE,
    KLIPPERSCREEN_SERVICE_NAME,
    KLIPPERSCREEN_UPDATER_SECTION_NAME,
)
from components.moonraker.moonraker import Moonraker
from core.constants import SYSTEMD
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.settings.kiauh_settings import KiauhSettings
from core.types.component_status import ComponentStatus
from utils.common import (
    check_install_dependencies,
    get_install_status,
)
from utils.config_utils import add_config_section, remove_config_section
from utils.fs_utils import remove_with_sudo
from utils.git_utils import (
    git_clone_wrapper,
    git_pull_wrapper,
)
from utils.distro_utils import is_arch
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    check_python_version,
    cmd_sysctl_service,
    create_python_venv,
    create_service_file,
    install_python_requirements,
    install_system_packages,
    remove_system_service,
)


def install_klipperscreen() -> None:
    Logger.print_status("Installing KlipperScreen ...")

    if not check_python_version(3, 7):
        return

    mr_instances = get_instances(Moonraker)
    if not mr_instances:
        Logger.print_dialog(
            DialogType.WARNING,
            [
                "Moonraker not found! KlipperScreen will not properly work "
                "without a working Moonraker installation.",
                "\n\n",
                "KlipperScreens update manager configuration for Moonraker "
                "will not be added to any moonraker.conf.",
            ],
        )
        if not get_confirm(
            "Continue KlipperScreen installation?",
            default_choice=False,
            allow_go_back=True,
        ):
            return

    check_install_dependencies()

    git_clone_wrapper(KLIPPERSCREEN_REPO, KLIPPERSCREEN_DIR)

    try:
        if is_arch():
            install_klipperscreen_arch()
        else:
            run(KLIPPERSCREEN_INSTALL_SCRIPT.as_posix(), shell=True, check=True)
        if mr_instances:
            patch_klipperscreen_update_manager(mr_instances)
            InstanceManager.restart_all(mr_instances)
        else:
            Logger.print_info(
                "Moonraker is not installed! Cannot add "
                "KlipperScreen to update manager!"
            )
        Logger.print_ok("KlipperScreen successfully installed!")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing KlipperScreen:\n{e}")
        return


def install_klipperscreen_arch() -> None:
    """Install KlipperScreen on Arch without running the upstream apt script."""
    Logger.print_status("Installing KlipperScreen dependencies for Arch ...")
    use_cage = get_confirm(
        "Use Wayland/Cage backend for KlipperScreen?",
        default_choice=True,
    )

    packages = [
        "python3-virtualenv",
        "python3-pip",
        "python3-setuptools",
        "libyaml-dev",
        "pkg-config",
        "libgtk-3-0",
        "libdbus-glib-1-2",
        "python3-gi",
        "gir1.2-gtk-3.0",
        "fonts-freefont-ttf",
        "xdotool",
    ]
    if use_cage:
        packages.extend(["cage", "seatd"])
    else:
        packages.extend([
            "xserver-xorg",
            "xinit",
            "xinput",
            "x11-xserver-utils",
            "xserver-xorg-input-evdev",
        ])

    install_system_packages(packages)

    if use_cage:
        _configure_seatd_for_klipperscreen()

    if create_python_venv(KLIPPERSCREEN_ENV_DIR, force=False):
        install_python_requirements(KLIPPERSCREEN_ENV_DIR, KLIPPERSCREEN_REQ_FILE)
    elif KLIPPERSCREEN_ENV_DIR.joinpath("bin/pip").exists():
        install_python_requirements(KLIPPERSCREEN_ENV_DIR, KLIPPERSCREEN_REQ_FILE)
    else:
        raise CalledProcessError(1, "create KlipperScreen virtualenv")

    create_service_file(
        KLIPPERSCREEN_SERVICE_NAME,
        _prep_klipperscreen_service_content(use_cage),
    )
    cmd_sysctl_service(KLIPPERSCREEN_SERVICE_NAME, "enable")
    cmd_sysctl_service(KLIPPERSCREEN_SERVICE_NAME, "restart")


def _configure_seatd_for_klipperscreen() -> None:
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or Path.home().name
    for group in ("input", "video", "render", "seat"):
        if run(["getent", "group", group], stdout=DEVNULL, stderr=DEVNULL).returncode == 0:
            run(["sudo", "usermod", "-aG", group, user], check=False)

    cmd_sysctl_service("seatd.service", "enable")
    cmd_sysctl_service("seatd.service", "start")


def _prep_klipperscreen_service_content(use_cage: bool) -> str:
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or Path.home().name
    python_bin = KLIPPERSCREEN_ENV_DIR.joinpath("bin/python")
    screen_py = KLIPPERSCREEN_DIR.joinpath("screen.py")

    if use_cage:
        after = "After=network.target seatd.service"
        wants = "Wants=seatd.service"
        environment = "Environment=GDK_BACKEND=wayland"
        exec_start = f"/usr/bin/cage -ds -- {python_bin} {screen_py}"
    else:
        after = "After=network.target"
        wants = ""
        environment = "Environment=DISPLAY=:0"
        exec_start = f"/usr/bin/xinit {python_bin} {screen_py} -- :0 -nolisten tcp"

    wants_line = f"{wants}\n" if wants else ""
    return f"""[Unit]
Description=KlipperScreen
{after}
{wants_line}
[Service]
Type=simple
User={user}
WorkingDirectory={KLIPPERSCREEN_DIR}
{environment}
ExecStart={exec_start}
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""


def patch_klipperscreen_update_manager(instances: List[Moonraker]) -> None:
    BackupService().backup_moonraker_conf()
    options = [
        ("type", "git_repo"),
        ("path", KLIPPERSCREEN_DIR.as_posix()),
        ("origin", KLIPPERSCREEN_REPO),
        ("managed_services", "KlipperScreen"),
        ("env", f"{KLIPPERSCREEN_ENV_DIR}/bin/python"),
        ("requirements", KLIPPERSCREEN_REQ_FILE.as_posix()),
    ]
    if not is_arch():
        options.append(("install_script", KLIPPERSCREEN_INSTALL_SCRIPT.as_posix()))

    add_config_section(
        section=KLIPPERSCREEN_UPDATER_SECTION_NAME,
        instances=instances,
        options=options,
    )


def update_klipperscreen() -> None:
    if not KLIPPERSCREEN_DIR.exists():
        Logger.print_info("KlipperScreen does not seem to be installed! Skipping ...")
        return

    try:
        Logger.print_status("Updating KlipperScreen ...")

        cmd_sysctl_service(KLIPPERSCREEN_SERVICE_NAME, "stop")

        settings = KiauhSettings()
        if settings.kiauh.backup_before_update:
            backup_klipperscreen_dir()

        git_pull_wrapper(KLIPPERSCREEN_DIR)

        install_python_requirements(KLIPPERSCREEN_ENV_DIR, KLIPPERSCREEN_REQ_FILE)

        cmd_sysctl_service(KLIPPERSCREEN_SERVICE_NAME, "start")

        Logger.print_ok("KlipperScreen updated successfully.", end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(f"Error updating KlipperScreen:\n{e}")
        return


def get_klipperscreen_status() -> ComponentStatus:
    return get_install_status(
        KLIPPERSCREEN_DIR,
        KLIPPERSCREEN_ENV_DIR,
        files=[SYSTEMD.joinpath(KLIPPERSCREEN_SERVICE_NAME)],
    )


def remove_klipperscreen() -> None:
    Logger.print_status("Removing KlipperScreen ...")
    try:
        if KLIPPERSCREEN_DIR.exists():
            Logger.print_status("Removing KlipperScreen directory ...")
            shutil.rmtree(KLIPPERSCREEN_DIR)
            Logger.print_ok("KlipperScreen directory successfully removed!")
        else:
            Logger.print_warn("KlipperScreen directory not found!")

        if KLIPPERSCREEN_ENV_DIR.exists():
            Logger.print_status("Removing KlipperScreen environment ...")
            shutil.rmtree(KLIPPERSCREEN_ENV_DIR)
            Logger.print_ok("KlipperScreen environment successfully removed!")
        else:
            Logger.print_warn("KlipperScreen environment not found!")

        if KLIPPERSCREEN_SERVICE_FILE.exists():
            remove_system_service(KLIPPERSCREEN_SERVICE_NAME)

        logfile = Path(f"/tmp/{KLIPPERSCREEN_LOG_NAME}")
        if logfile.exists():
            Logger.print_status("Removing KlipperScreen log file ...")
            remove_with_sudo(logfile)
            Logger.print_ok("KlipperScreen log file successfully removed!")

        kl_instances: List[Klipper] = get_instances(Klipper)
        for instance in kl_instances:
            logfile = instance.base.log_dir.joinpath(KLIPPERSCREEN_LOG_NAME)
            if logfile.exists():
                Logger.print_status(f"Removing {logfile} ...")
                Path(logfile).unlink()
                Logger.print_ok(f"{logfile} successfully removed!")

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        if mr_instances:
            Logger.print_status("Removing KlipperScreen from update manager ...")
            BackupService().backup_moonraker_conf()
            remove_config_section("update_manager KlipperScreen", mr_instances)
            Logger.print_ok("KlipperScreen successfully removed from update manager!")

        Logger.print_ok("KlipperScreen successfully removed!")

    except Exception as e:
        Logger.print_error(f"Error removing KlipperScreen:\n{e}")


def backup_klipperscreen_dir() -> None:
    svc = BackupService()
    svc.backup_directory(
        source_path=KLIPPERSCREEN_DIR,
        backup_name="KlipperScreen",
        target_path="KlipperScreen",
    )
    svc.backup_directory(
        source_path=KLIPPERSCREEN_ENV_DIR,
        backup_name="KlipperScreen-env",
        target_path="KlipperScreen",
    )
