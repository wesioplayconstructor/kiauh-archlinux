# KIAUH-arch: Package Mapping

## GLOBAL_DEPS (constants.py)
| Debian | Arch Linux |
|--------|-----------|
| git | git |
| wget | wget |
| curl | curl |
| unzip | unzip |
| dfu-util | dfu-util |
| python3-virtualenv | python-virtualenv |
| python3-dev | python |
| build-essential | base-devel |
| libffi-dev | libffi |
| libncurses-dev | ncurses |
| avahi-daemon | avahi |

## sys_utils.py command mapping
| Debian command | Arch command |
|---------------|-------------|
| apt-get update | pacman -Sy |
| apt-get install -y | pacman -S --noconfirm |
| apt-get upgrade -y | pacman -Su --noconfirm |
| apt list --upgradable | pacman -Qu |
| dpkg-query | pacman -Qi |
