from archinstall.lib.hardware import SysInfo
from archinstall.lib.models.device import FilesystemType, PartitionTable, PartitionGUID
from .base import BaseArchHandler

class X86_64Handler(BaseArchHandler):
    def get_root_guid(self) -> bytes:
        """
        Returns the UAPI standard GUID for x86-64 root partitions.
        Used by systemd-gpt-auto-generator to find / without fstab.
        """
        return PartitionGUID.LINUX_ROOT_X86_64.bytes

    def get_default_partition_table(self) -> PartitionTable:
        """
        Logic for BIOS vs UEFI.
        """
        return PartitionTable.GPT if SysInfo.has_uefi() else PartitionTable.MBR

    def get_format_options(self, fs_type: FilesystemType) -> list[str]:
        """
        Standard x86 performance tweaks. 
        Note: NTFS is blocked by the BaseArchHandler.validate_filesystem()
        """
        options = ['-f']
        if fs_type == FilesystemType.Ext4:
            # Enable 64bit and metadata_csum for modern x86 drives
            options.extend(['-O', '64bit,metadata_csum'])
        elif fs_type == FilesystemType.Btrfs:
            options.append('-m single') # Often preferred for single-SSD laptops
        return options

    def get_bootloader_hints(self) -> dict:
        return {
            "loader": "systemd-boot" if SysInfo.has_uefi() else "grub",
            "secure_boot_capable": True
        }
