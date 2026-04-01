
import platform
from lib.disk.device_handler import BaseDeviceHandler
from lib.models.device import PartitionTable, FilesystemType, PartitionGUID
from archinstall.lib.hardware import SysInfo

class X86DeviceHandler(BaseDeviceHandler):
	def get_partition_table_type(self) -> PartitionTable:
		"""
		On x86, we decide based on UEFI presence.
		"""
		return PartitionTable.GPT if SysInfo.has_uefi() else PartitionTable.MBR

	def get_root_guid(self) -> str:
		return PartitionGUID.LINUX_ROOT_X86_64.value

	def get_partition_alignment(self, device_type: str) -> int:
		"""
		Standard 1MiB alignment works for most SSDs/HDDs on x86.
		"""
		return 1024  # 1MiB in KiB

	def recommended_fs(self) -> FilesystemType:
		# Default to Ext4 or Btrfs. 
		# NTFS is strictly excluded per #4279.
		return FilesystemType.Ext4
		
	def get_bootloader_data(self) -> dict:
		"""
		x86 typically uses GRUB or systemd-boot.
		"""
		if SysInfo.has_uefi():
			return {'loader': 'systemd-boot', 'efi_mount': '/boot'}
		return {'loader': 'grub', 'install_target': 'mbr'}
