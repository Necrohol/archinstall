import sys
import json
from .helper import HardwareHelper

def main():
    print("--- Hardware Engine: Discovery Mode ---")
    
    # Mock config for discovery
    mock_config = {
        'installation_path': '/tmp/mock_target',
        'arch': 'arm64' if os.uname().machine == 'aarch64' else 'x86_64',
        'distro': 'pentoo'
    }

    engine = HardwareHelper(mock_config)
    
    if not engine.hw_def:
        print("[-] No hardware match found in definitions/")
        sys.exit(1)

    print(f"[+] Match Found: {engine.hw_def.get('match', {}).get('cpu_families', 'Generic')}")
    print(f"[+] Boot Method: {engine.hw_def.get('boot', {}).get('method')}")
    print(f"[+] Suggested Packages: {engine.hw_def.get('packages', {}).get('pentoo', [])}")
    
    # Print the full matched TOML data for debugging
    print("\n--- Raw Data ---")
    print(json.dumps(engine.hw_def, indent=2))

if __name__ == "__main__":
    main()
