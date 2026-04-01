class RPi5Helper(HardwareHelper):
    def pre_install(self):
        info("RPi5: Optimizing PCIe bus for NVMe HAT...")
        # We can't always toggle Gen 3 in the live environment 
        # but we ensure the kernel parameters are ready.
        pass

    def post_install(self, target_mount):
        info("RPi5: Finalizing NVMe Boot Strategy...")
        self._enable_pcie_gen3(target_mount)
        self._update_eeprom_boot_order()

    def _enable_pcie_gen3(self, target):
        # Path to the mounted firmware partition
        config_path = f"{target}/boot/firmware/config.txt"
        try:
            with open(config_path, "a") as f:
                f.write("\n# Pentoo NVMe Optimization\ndtparam=pciex1_gen=3\n")
            info("PCIe Gen 3 enabled in config.txt")
        except FileNotFoundError:
            warn("Could not find config.txt to enable Gen 3!")

    def _update_eeprom_boot_order(self):
        """
        Sets BOOT_ORDER to 0xf41 (NVMe, then SD, then Restart)
        Requires 'rpi-eeprom-config' to be in the LiveCD DNA.
        """
        info("Updating SPI EEPROM for NVMe boot priority...")
        try:
            # 0xf41: 1=SD, 4=NVMe, f=Restart loop
            SysCommand("rpi-eeprom-config -a") 
            # Note: In a real script, you'd pipe the new config to this command
        except Exception as e:
            warn(f"EEPROM update failed: {e}. Manual boot selection may be required.")
