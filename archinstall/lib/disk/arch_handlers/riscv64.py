
class Riscv64DeviceHandler(BaseDeviceHandler):
    def get_partition_table_type(self) -> PartitionTable:
        return PartitionTable.GPT  # RISC-V almost always wants GPT/UEFI

    def get_root_guid(self) -> str:
        return "5BE22121-1D04-4143-9E04-511B6195E68C"

    def get_boot_args(self) -> str:
        # Specific to Milk-V / Banana Pi F3 serial consoles
        return "console=ttyS0,115200 rootwait"
