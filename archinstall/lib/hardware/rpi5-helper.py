import subprocess
from pathlib import Path
import tomllib

def get_pci_ids():
    # Fast PCI probe: returns a list like ['10de:2204', '8086:1234']
    output = subprocess.check_output("lspci -nn | grep -o '\[[0-9a-f]\{4\}:[0-9a-f]\{4\}\]'", shell=True)
    return [id.strip('[]') for id in output.decode().splitlines()]

def find_matching_definition():
    present_ids = get_pci_ids()
    defs_path = Path(__file__).parent / "definitions"
    
    for toml_file in defs_path.glob("*.toml"):
        with open(toml_file, "rb") as f:
            data = tomllib.load(f)
            # Match if any PCI ID in the TOML is found on the system
            if any(p_id in present_ids for p_id in data.get('match', {}).get('pci_ids', [])):
                return data
    return None
