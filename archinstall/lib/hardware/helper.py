import archinstall
from archinstall.lib.command import SysCommand
from archinstall.lib.output import info, warn

class HardwareHelper:
    def __init__(self, config):
        self.config = config
        self.arch = config.get('arch', 'x86_64')

    def pre_install(self):
        """Logic to run BEFORE partitioning (e.g., PCIe Gen 3 toggle)"""
        pass

    def post_install(self, target_mount):
        """Logic to run AFTER rsync (e.g., Bootloader/EEPROM)"""
        pass
