import importlib
import os
import sys
import textwrap
import time
import traceback
from pathlib import Path

# Standard Archinstall Libs
from archinstall.lib.args import ArchConfigHandler
from archinstall.lib.disk.utils import disk_layouts
from archinstall.lib.hardware import SysInfo
from archinstall.lib.network.wifi_handler import WifiHandler
from archinstall.lib.networking import ping
from archinstall.lib.output import debug, error, info, warn
from archinstall.lib.packages.util import check_version_upgrade
from archinstall.lib.pacman.pacman import Pacman
from archinstall.lib.translationhandler import tr
from archinstall.lib.utils.util import running_from_iso
from archinstall.tui.ui.components import tui

# Your New Hardware Agnostic Libs
from archinstall.lib.hardware import HardwareHelper, BootIntegrityGuard

def _log_sys_info() -> None:
    debug(f'Hardware model detected: {SysInfo.sys_vendor()} {SysInfo.product_name()}; UEFI mode: {SysInfo.has_uefi()}')
    debug(f'Processor model detected: {SysInfo.cpu_model()}')
    debug(f'Memory: {SysInfo.mem_available()} available / {SysInfo.mem_total()} total')
    debug(f'Virtualization: {SysInfo.virtualization()}; is VM: {SysInfo.is_vm()}')
    debug(f'Disk states before installing:\n{disk_layouts()}')

def _check_online(wifi_handler: WifiHandler | None = None) -> bool:
    try:
        ping('1.1.1.1')
    except OSError:
        if wifi_handler is not None:
            return tui.run(wifi_handler)
    return True

def run() -> int:
    arch_config_handler = ArchConfigHandler()

    if '--help' in sys.argv or '-h' in sys.argv:
        arch_config_handler.print_help()
        return 0

    if os.getuid() != 0:
        print(tr('Archinstall requires root privileges to run.'))
        return 1

    _log_sys_info()

    # --- AGNOSTIC MODE DETECTION ---
    # We check if we are running the 'gentoo' or 'pentoo' script
    script = arch_config_handler.get_script()
    is_gentoo_family = script in ['gentoo', 'pentoo']

    if not arch_config_handler.args.offline:
        wifi_handler = WifiHandler() if not arch_config_handler.args.skip_wifi_check else None
        if not _check_online(wifi_handler):
            return 0

        # Only sync Pacman if we are NOT in Gentoo/Pentoo mode
        if not is_gentoo_family:
            info('Fetching Arch Linux package database...')
            if not Pacman.run('-Sy'):
                return 1
        else:
            info("Gentoo/Pentoo Environment detected. Skipping Arch DB sync.")

    # --- HARDWARE ENGINE START ---
    # Initialize the engine early to allow pre_install tweaks (like RPi5 PCIe)
    hw_helper = HardwareHelper(arch_config_handler.args)
    hw_helper.pre_install()

    # --- SCRIPT EXECUTION ---
    mod_name = f'archinstall.scripts.{script}'
    try:
        module = importlib.import_module(mod_name)
        # Pass the hardware helper into the script if needed
        module.main(arch_config_handler)
    except ImportError:
        error(f"Script {script} not found.")
        return 1
    except Exception as e:
        _error_message(e)
        return 1

    # --- FINAL HARDWARE INTEGRITY GUARD ---
    info("Installation complete. Performing final hardware check...")
    guard = BootIntegrityGuard(arch_config_handler.args, hw_helper.hw_def)

    if guard.verify_all():
        info("Ready to reboot!")
        return 0
    else:
        error("Hardware integrity failed. Dropping to emergency shell.")
        os.system("/bin/bash")
        return 1

def _error_message(exc: Exception) -> None:
    err = ''.join(traceback.format_exception(exc))
    error(err)
    warn("Archinstall experienced an error. Check /var/log/archinstall/install.log")

if __name__ == '__main__':
    sys.exit(run())
