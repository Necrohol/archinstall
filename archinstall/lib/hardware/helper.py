import os
import subprocess
import requests
import zipfile
import tomllib
import re
import multiprocessing
from pathlib import Path
from io import BytesIO

from archinstall.lib.command import SysCommand
from archinstall.lib.output import info, warn, error, debug

class HardwareHelper:
    def __init__(self, config: dict):
        self.config = config
        # Target is usually /mnt/arch or /mnt/gentoo
        self.target = Path(config.get('installation_path', '/mnt/gentoo'))
        self.arch = config.get('arch', 'x86_64')
        self.distro = config.get('distro', 'pentoo')
        
        # Internal Library Path
        self.def_dir = Path(__file__).parent / "definitions"
        self.hw_def = self._detect_and_load()

    # --- DETECTION ENGINE ---
    def _detect_and_load(self) -> dict:
        """Probes hardware and matches against TOML definitions."""
        pci_ids = self._get_pci_ids()
        cpu_model = self._get_cpu_model()
        
        if not self.def_dir.exists():
            warn(f"Hardware definition directory missing: {self.def_dir}")
            return {}

        for toml_file in self.def_dir.glob("*.toml"):
            try:
                with open(toml_file, "rb") as f:
                    data = tomllib.load(f)
                    match = data.get('match', {})
                    
                    # Check PCI IDs, CPU strings, or Arch-specific files
                    if any(p_id in pci_ids for p_id in match.get('pci_ids', [])) or \
                       cpu_model in match.get('cpu_models', []) or \
                       self.arch == match.get('arch'):
                        info(f"Hardware Profile Matched: {toml_file.name}")
                        return data
            except Exception as e:
                error(f"Error loading {toml_file.name}: {e}")
def _apply_usb_quirks(self):
    """
    Prevents HID-induced login loops and 'strobe' crashes.
    """
    quirks = self.hw_def.get('usb_quirks', {})
    if not quirks:
        return

    # 1. Kernel Quirks (usbhid.quirks)
    # Format: 0xVENDOR:0xPRODUCT:0xQUIRK_FLAGS
    # 0x0004 = HID_QUIRK_IGNORE (Prevents ghost inputs)
    # 0x0400 = HID_QUIRK_ALWAYS_POLL (Fixes laggy/strobe wakeups)
    vendor_id = quirks.get('vendor_id')
    product_id = quirks.get('product_id')
    flags = quirks.get('flags', '0x0004')

    if vendor_id and product_id:
        info(f"Injecting USB HID Quirk for {vendor_id}:{product_id}")
        self._append_boot_param(f"usbhid.quirks={vendor_id}:{product_id}:{flags}")

    # 2. Udev Rule (Power Management)
    # Disabling autosuspend often stops the 'strobe' disconnect loop
    if quirks.get('disable_autosuspend'):
        rule = f'ACTION=="add", SUBSYSTEM=="usb", ATTR{{idVendor}}=="{vendor_id[2:]}", ATTR{{idProduct}}=="{product_id[2:]}", ATTR{{power/control}}="on"'
        udev_path = self.target / f"etc/udev/rules.d/99-usb-quirk-{vendor_id}.rules"
        udev_path.parent.mkdir(parents=True, exist_ok=True)
        udev_path.write_text(rule + "\n")
