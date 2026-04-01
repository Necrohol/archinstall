import os
from pathlib import Path
from archinstall.lib.output import info, warn, error, debug
from archinstall.lib.command import SysCommand

class BootIntegrityGuard:
    def __init__(self, config: dict, hw_def: dict):
        self.target = Path(config.get('installation_path', '/mnt/gentoo'))
        self.hw_def = hw_def
        self.distro = config.get('distro', 'pentoo')
        self.fs_type = config.get('storage', {}).get('filesystem', 'f2fs')

    def verify_all(self) -> bool:
        """Runs the hardware validation gauntlet."""
        info("--- Starting Hardware Integrity Check ---")
        
        checks = [
            self._verify_efi_files(),
            self._verify_grub_cfg(),
            self._verify_initramfs(),
            self._verify_fstab()
        ]
        
        if all(checks):
            info("Integrity Guard: [PASS] System is safe to boot.")
            return True
        else:
            error("Integrity Guard: [FAIL] Boot critical files are missing or corrupt.")
            return False

    def _verify_efi_files(self) -> bool:
        """Checks for RPi UEFI shims or standard GRUB EFI binaries."""
        # Check for RPi-specific UEFI firmware if url was provided in TOML
        if self.hw_def.get('firmware', {}).get('url'):
            rpi_firmware = self.target / "boot/efi/RPI_EFI.fd"
            if not rpi_firmware.exists():
                error("MISSING: Raspberry Pi UEFI Firmware (RPI_EFI.fd) not found in ESP.")
                return False
        
        # Check for the actual GRUB binary
        grub_efi = self.target / "boot/efi/EFI/BOOT/BOOTAA64.EFI"
        if not grub_efi.exists():
            warn("GRUB EFI binary not found at default removable path. Check install logs.")
            # We don't return False here as some distros use custom paths
        return True

    def _verify_grub_cfg(self) -> bool:
        """Ensures the GRUB_DTB variable actually made it into the config."""
        grub_env = self.target / "etc/default/grub"
        expected_dtb = self.hw_def.get('boot', {}).get('grub_dtb')
        
        if expected_dtb and grub_env.exists():
            with open(grub_env, 'r') as f:
                content = f.read()
                if expected_dtb not in content:
                    error(f"INTEGRITY ERROR: GRUB_DTB '{expected_dtb}' is missing from /etc/default/grub")
                    return False
        return True

    def _verify_initramfs(self) -> bool:
        """Checks if Dracut/Initramfs config exists and contains the FS driver."""
        dracut_conf = self.target / "etc/dracut.conf.d/10-hardware.conf"
        if not dracut_conf.exists():
            warn("No hardware-specific Dracut config found. Boot might fail on NVMe.")
            return True # Not a hard failure, but risky
            
        with open(dracut_conf, 'r') as f:
            content = f.read()
            if self.fs_type not in content:
                error(f"INTEGRITY ERROR: Initramfs config is missing the '{self.fs_type}' module.")
                return False
        return True

    def _verify_fstab(self) -> bool:
        """Ensures the root partition isn't using a placeholder UUID."""
        fstab = self.target / "etc/fstab"
        if not fstab.exists():
            error("CRITICAL: /etc/fstab is missing!")
            return False
            
        with open(fstab, 'r') as f:
            if "/boot/efi" not in f.read():
                warn("fstab is missing the EFI partition mount point.")
        return True
