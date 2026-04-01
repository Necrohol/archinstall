from archinstall.lib.output import info, warn, error
from archinstall.lib.command import SysCommand

class PackageValidator:
    def __init__(self, hw_def, distro="pentoo"):
        self.hw_def = hw_def
        self.distro = distro
        self.final_pkgs = []

    def validate_and_map(self, user_pkgs):
        """
        Cross-references user-picked packages with TOML requirements.
        If Arch is detected, it sends to the pacman list.
        If Gentoo is detected, it prepares for emerge.
        """
        # 1. Get HW-specific packages
        hw_pkgs = self.hw_def.get('packages', {}).get(self.distro, [])
        
        # 2. Merge with User picks
        self.final_pkgs = list(set(user_pkgs + hw_pkgs))

        # 3. Validation: Does the package actually exist in the repos?
        validated_list = []
        for pkg in self.final_pkgs:
            if self._exists_in_repo(pkg):
                validated_list.append(pkg)
            else:
                warn(f"Package {pkg} not found in {self.distro} repos. Skipping.")
        
        return validated_list

    def _exists_in_repo(self, pkg):
        """Simulates a repo check (e.g., 'pacman -Ss' or 'equery')"""
        try:
            if self.distro == "arch":
                # Check Arch repos
                SysCommand(f"pacman -Sp {pkg} --noconfirmed")
            else:
                # Check Gentoo/Pentoo overlays
                SysCommand(f"emerge -pv --pretend {pkg}")
            return True
        except:
            return False
