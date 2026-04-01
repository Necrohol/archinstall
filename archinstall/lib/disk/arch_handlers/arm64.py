
import platform
from lib.disk.device_handler import BaseDeviceHandler
from lib.models.device import PartitionTable, FilesystemType, PartitionGUID

class Arm64DeviceHandler(BaseDeviceHandler):
    def get_partition_table_type(self) -> PartitionTable:
        # Most modern ARM64 (SBCs) use GPT, but some legacy U-Boot 
        # setups still prefer MBR. We default to GPT for Arch.
        return PartitionTable.GPT

    def get_root_guid(self) -> str:
        return PartitionGUID.LINUX_ROOT_ARM64.value

    def get_partition_alignment(self, device_type: str) -> int:
        """
        ARM SD cards and eMMC often perform better with 4MiB alignment
        to match the NAND erase block size, preventing "shite" latency.
        """
        if device_type in ['mmcblk', 'sd']:
            return 4096  # 4MiB in KiB
        return 1024      # 1MiB standard

    def recommended_fs(self) -> FilesystemType:
        # For ARM64 SBCs (Flash storage), F2FS is the gold standard.
        # NTFS is strictly excluded per #4279.
        return FilesystemType.F2fs
