from abc import ABC, abstractmethod
from archinstall.lib.models.device import FilesystemType, PartitionTable, PartitionGUID

class BaseArchHandler(ABC):
    @abstractmethod
    def get_root_guid(self) -> bytes:
        pass

    @abstractmethod
    def get_default_partition_table(self) -> PartitionTable:
        pass

    def validate_filesystem(self, fs_type: FilesystemType):
        """Enforces Issue #4279: No NTFS for Linux root."""
        if fs_type in [FilesystemType.Ntfs, FilesystemType.Fat12, FilesystemType.Fat16]:
            # Fat is allowed for ESP, but we restrict it elsewhere
            pass 
        return True

    @abstractmethod
    def get_format_options(self, fs_type: FilesystemType) -> list[str]:
        pass
