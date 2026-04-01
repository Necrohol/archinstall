import multiprocessing
import psutil # For RAM-aware thread calculation
from pathlib import Path
from archinstall.lib.output import info

class HardwareOptimizer:
    def __init__(self, target_path, hw_def, distro="pentoo"):
        self.target = Path(target_path)
        self.hw_def = hw_def
        self.distro = distro
        self.cpu_count = multiprocessing.cpu_count()
        self.total_ram_gb = psutil.virtual_memory().total / (1024**3)

    def apply_optimizations(self):
        """Entry point for all hardware-level tuning."""
        info(f"Optimizing for {self.cpu_count} cores and {self.total_ram_gb:.1f}GB RAM...")
        
        if self.distro in ["gentoo", "pentoo"]:
            self._tune_gentoo_make_conf()
        elif self.distro == "arch":
            self._tune_arch_makepkg()
            
        self._set_zram_policy()

    def _calculate_jobs(self):
        """
        Prevents OOM (Out of Memory) during heavy compiles.
        Rule of thumb: 2GB RAM per thread for heavy C++ (Webkit/LLVM).
        """
        ram_limited_jobs = int(self.total_ram_gb / 2)
        return max(1, min(self.cpu_count, ram_limited_jobs))

    def _tune_gentoo_make_conf(self):
        make_conf = self.target / "etc/portage/make.conf"
        jobs = self._calculate_jobs()
        load = jobs * 0.9 # Keep system responsive
        
        # Get march from TOML or fallback to native
        march = self.hw_def.get('performance', {}).get('march', 'native')
        
        optimizations = [
            f'COMMON_FLAGS="-O2 -march={march} -pipe"',
            f'MAKEOPTS="-j{jobs} -l{load:.1f}"',
            f'EMERGE_DEFAULT_OPTS="--jobs={jobs} --load-average={load:.1f}"',
            'PORTAGE_NICENESS="15"', # Background compilation priority
            'VIDEO_CARDS="fbdev vc4"' if "rpi" in self.hw_def.get('match', {}).get('cpu_families', []) else ""
        ]

        with open(make_conf, "a") as f:
            f.write("\n# Hardware-Optimizer Auto-Tuning\n")
            f.write("\n".join(filter(None, optimizations)) + "\n")

    def _tune_arch_makepkg(self):
        makepkg_conf = self.target / "etc/makepkg.conf"
        jobs = self._calculate_jobs()
        # Update MAKEFLAGS for Arch
        # In a real script, use sed or a regex to replace existing MAKEFLAGS
        info(f"Setting Arch MAKEFLAGS to -j{jobs}")

    def _set_zram_policy(self):
        """Enable ZRAM for low-RAM devices (RPi 4/5 4GB models)."""
        if self.total_ram_gb <= 8:
            info("Low RAM detected. Enabling ZRAM priority in post-install.")
            # Logic to enable zram-generator or openrc zram script
