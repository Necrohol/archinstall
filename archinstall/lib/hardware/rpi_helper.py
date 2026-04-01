import os
import zipfile
import requests
from pathlib import Path
from archinstall.lib.command import SysCommand
from archinstall.lib.output import info, warn, error
from archinstall.lib.disk.device_handler import device_handler

class RPiFirmwareHelper:
    FIRMWARE_URLS = {
        "RPI5": "https://github.com/worproject/rpi5-uefi/releases/download/v0.3/RPi5_UEFI_Release_v0.3.zip",
        "RPI4": "https://github.com/pftf/RPi4/releases/download/v1.42/RPi4_UEFI_Firmware_v1.42.zip",
        "RPI3": "https://github.com/pftf/RPi3/releases/download/v1.39/RPi3_UEFI_Firmware_v1.39.zip"
    }

    def __init__(self, board_type: str, target_path: Path = Path("/mnt/gentoo")):
        self.board = board_type.upper()
        self.target = target_path
        # Pentoo/Gentoo standard mount for RPi firmware
        self.efi_path = self.target / "boot/efi"
        self.fw_link = self.target / "boot/firmware"

    def get_esp_partition(self) -> Path:
        """Uses our agnostic device_handler to find where to drop the firmware."""
        for device in device_handler.devices:
            for part in device.partition_infos:
                # Check for EFI GUID or VFAT on small partitions
                if part.partuuid or part.fs_type == 'vfat':
                    if part.mountpoint and "/boot" in str(part.mountpoint):
                        return part.path
        return None

    def deploy_uefi(self):
        """Downloads and extracts UEFI firmware to the ESP."""
        url = self.FIRMWARE_URLS.get(self.board)
        if not url:
            raise ValueError(f"Unsupported board: {self.board}")

        info(f"Probing {self.board}: Downloading UEFI shim...")
        
        # Ensure directory exists
        self.efi_path.mkdir(parents=True, exist_ok=True)
        zip_tmp = Path("/tmp/fw.zip")

        # Pythonic Download
        r = requests.get(url, stream=True)
        with open(zip_tmp, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Pythonic Unzip
        with zipfile.ZipFile(zip_tmp, 'r') as zip_ref:
            zip_ref.extractall(self.efi_path)
        
        info(f"UEFI Firmware extracted to {self.efi_path}")
        self._create_symlinks()
        self._patch_config_txt()

    def _create_symlinks(self):
        """Standardizes the 'Pest' of different mountpoint expectations."""
        if self.fw_link.exists() or self.fw_link.is_symlink():
            os.remove(self.fw_link)
        
        # Relative symlink for portability
        os.symlink("efi", self.fw_link)
        info(f"Symlinked /boot/firmware -> {self.efi_path.name}")

    def _patch_config_txt(self):
        """Ensures the RPi firmware initializes the UEFI image instead of a direct kernel."""
        config_txt = self.efi_path / "config.txt"
        
        # Add PCIe Gen 3 for RPi5 NVMe HAT if applicable
        if self.board == "RPI5":
            with open(config_txt, "a") as f:
                f.write("\n# Pentoo NVMe Speed Patch\ndtparam=pciex1_gen=3\n")
            info("Applied PCIe Gen 3 patch to config.txt")

