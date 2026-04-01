import os
import subprocess
import requests
import zipfile
import tomllib
from pathlib import Path
from io import BytesIO

from archinstall.lib.command import SysCommand
from archinstall.lib.output import info, warn, error, debug

class HardwareHelper:
    def __init__(self, config: dict):
        self.config = config
        self.target = Path(config.get('installation_path', '/mnt/gentoo'))
        self.arch = config.get('arch', 'x86_64')
        self.distro = config.get('distro', 'pentoo')
        self.hw_def = self._detect_and_load()

    def _detect_and_load(self) -> dict:
        """Probes PCI/USB/CPU and returns the matching TOML definition."""
        pci_ids = self._get_pci_ids()
        cpu_model = self._get_cpu_model()
        
        def_dir = Path(__file__).parent / "definitions"
        for toml_file in def_dir.glob("*.toml"):
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
                match = data.get('match', {})
                # Match by PCI IDs, CPU Model, or Arch
                if any(p_id in pci_ids for p_id in match.get('pci_ids', [])) or \
                   cpu_model in match.get('cpu_models', []) or \
                   self.arch == match.get('arch'):
                    info(f"Hardware Profile Loaded: {toml_file.name}")
                    return data
        return {}

    def _get_pci_ids(self):
        try:
            out = subprocess.check_output("lspci -nn", shell=True).decode()
            import re
            return re.findall(r"\[([0-9a-f]{4}:[0-9a-f]{4})\]", out)
        except: return []

    def _get_cpu_model(self):
        try:
            with open("/proc/device-tree/model", "r") as f:
                return f.read().strip().lower()
        except: return "generic"

    def pre_install(self):
        """Prepare hardware (PCIe Gen3, TPM init, etc.)"""
        if not self.hw_def: return
        
        # Apply Live-environment tweaks (like RPi5 PCIe speed)
        for cmd in self.hw_def.get('scripts', {}).get('pre_install', []):
            try: SysCommand(cmd)
            except: warn(f"Failed pre-install script: {cmd}")

    def post_install(self):
        """The 'Final Scrub' and Hardware Injection."""
        if not self.hw_def: return

        # 1. Inject Distro Packages (Arch or Gentoo)
        pkgs = self.hw_def.get('packages', {}).get(self.distro, [])
        if pkgs:
            info(f"Injecting {self.distro} hardware packages: {pkgs}")
            self.config['packages'].extend(pkgs)

        # 2. Handle Firmware/UEFI fetching (RPi/SBC)
        self._handle_firmware()

        # 3. Poke Bootloader (Grub DTB or Config.txt)
        self._poke_bootloader()

        # 4. Dracut/Initramfs generation
        self._generate_dracut()

    def _handle_firmware(self):
        fw_url = self.hw_def.get('firmware', {}).get('url')
        if fw_url:
            efi_path = self.target / "boot/efi"
            efi_path.mkdir(parents=True, exist_ok=True)
            info(f"Downloading Firmware: {fw_url}")
            r = requests.get(fw_url)
            with zipfile.ZipFile(BytesIO(r.content)) as z:
                z.extractall(efi_path)

    def _poke_bootloader(self):
        boot = self.hw_def.get('boot', {})
        # If UEFI: Poke GRUB_DTB
        if boot.get('method') == 'uefi':
            grub_file = self.target / "etc/default/grub"
            if grub_file.exists():
                dtb_line = boot.get('grub_dtb', '')
                with open(grub_file, "a") as f:
                    f.write(f'\n# Hardware DTB\nGRUB_DTB="{dtb_line}"\n')
        # If Classic: Poke config.txt
        else:
            config_txt = self.target / "boot/efi/config.txt"
            with open(config_txt, "a") as f:
                for line in boot.get('config_pokes', []):
                    f.write(f"{line}\n")

    def _generate_dracut(self):
        """Ensures Initramfs has NVMe/F2FS/Btrfs drivers."""
        dracut_conf = self.target / "etc/dracut.conf.d/10-hardware.conf"
        fs = self.config.get('storage', {}).get('filesystem', 'f2fs')
        with open(dracut_conf, "w") as f:
            f.write(f'add_dracutmodules+=" {fs} rootfs-block "\n')
            f.write('drivers+=" pcie-brcmstb nvme vfat "\n')
