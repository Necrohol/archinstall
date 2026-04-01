import os
import multiprocessing
from archinstall.lib.output import info, debug
from archinstall.lib.utils.util import spawn

class GentooDeployer:
    def __init__(self, target="/mnt/gentoo", source="/mnt/live/sqfs"):
        self.target = target
        self.source = source
        self.cores = multiprocessing.cpu_count()

    def rsync_rootfs(self):
        """
        Clones the Live environment to the target disk.
        Excludes volatile and temporary directories.
        """
        info(f"Cloning system to {self.target}...")
        excludes = [
            '/dev/*', '/proc/*', '/sys/*', '/tmp/*', '/run/*', 
            '/mnt/*', '/media/*', '/var/lib/portage/world.old',
            '/var/cache/distfiles/*', '/var/cache/binpkgs/*'
        ]
        
        cmd = ['rsync', '-aAXv']
        for exc in excludes:
            cmd.append(f'--exclude={exc}')
        
        cmd.extend([self.source + '/', self.target])
        spawn(cmd)

    def inject_power_configs(self):
        """
        Applies CPU-specific optimizations and scheduling policies.
        """
        info("Injecting Gentoo Power-Abuser configurations...")
        conf_d = os.path.join(self.target, "etc/portage/make.conf.d")
        os.makedirs(conf_d, exist_ok=True)

        # 1. Scheduling (Idle priority for background builds)
        with open(os.path.join(conf_d, "01-scheduling.conf"), "w") as f:
            f.write(f'PORTAGE_SCHEDULING_POLICY="idle"\n')
            f.write(f'PORTAGE_NICENESS="19"\n')
            f.write(f'MAKEOPTS="-j{self.cores + 1}"\n')
            f.write(f'EMERGE_DEFAULT_OPTS="--jobs {self.cores} --load-average {float(self.cores)}"\n')

        # 2. CPU Flags (cpuid2cpuflags)
        try:
            flags = spawn(['cpuid2cpuflags']).get_output().strip()
            use_path = os.path.join(self.target, "etc/portage/package.use/00-cpu-flags")
            os.makedirs(os.path.dirname(use_path), exist_ok=True)
            with open(use_path, "w") as f:
                f.write(f"*/* {flags}\n")
        except:
            debug("Could not run cpuid2cpuflags, skipping.")

    def finalize_base(self):
        """Standard Gentoo post-rsync cleanup"""
        # Kill pwgen as requested
        spawn(['chroot', self.target, 'emerge', '--unmerge', 'app-admin/pwgen'])
        # Shallow git sync placeholder
        spawn(['chroot', self.target, 'eselect', 'repository', 'add', 'gentoo', 'git', 'https://github.com/gentoo-mirror/gentoo'])
