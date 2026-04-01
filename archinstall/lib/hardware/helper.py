import subprocess

class HardwareHelper:
    # ... previous __init__ ...

    def _probe_pci_ids(self):
        """Returns a list of 'vendor:device' strings from the live system."""
        try:
            output = subprocess.check_output("lspci -nn", shell=True).decode()
            # Extract [xxxx:xxxx] patterns
            import re
            return re.findall(r"\[([0-9a-f]{4}:[0-9a-f]{4})\]", output)
        except Exception:
            return []

    def load_matched_definition(self):
        """Scans the definitions folder for a PCI ID match."""
        pci_list = self._probe_pci_ids()
        def_path = Path(__file__).parent / "definitions"
        
        for toml_file in def_path.glob("*.toml"):
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
                match_ids = data.get('match', {}).get('pci_ids', [])
                
                # If any ID in the TOML matches the hardware, this is our file
                if any(p_id in pci_list for p_id in match_ids):
                    info(f"Hardware Match Found: {toml_file.name}")
                    return data
        return None

    def pre_install(self):
        hw_def = self.load_matched_definition()
        if hw_def:
            # Inject packages into the global config for the main installer to see
            pkgs = hw_def.get('packages', {}).get(self.config.get('distro', 'gentoo'), [])
            self.config['packages'] += pkgs
            info(f"Injected hardware-specific packages: {pkgs}")
