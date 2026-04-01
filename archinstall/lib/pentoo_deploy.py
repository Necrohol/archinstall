import os
from archinstall.lib.gentoo_deploy import GentooDeployer
from archinstall.lib.output import info, warn

class PentooDeployer(GentooDeployer):
    def __init__(self, target="/mnt/gentoo", source="/mnt/live/sqfs"):
        super().__init__(target=target, source=source)

    def rsync_pentoo_live(self):
        """
        Specialized rsync for Pentoo SquashFS.
        Preserves the Pentoo 'Identity' while removing Live-only bloat.
        """
        info(f"Expanding 5-6GB SquashFS to {self.target}...")
        
        # Pentoo-specific exclusions: 
        # We don't want the live user's history or temporary hardware rules
        pentoo_excludes = [
            '--exclude=/home/pentoo/.bash_history',
            '--exclude=/etc/udev/rules.d/70-persistent-net.rules',
            '--exclude=/var/log/pentoo-live.log',
            '--exclude=/etc/X11/xorg.conf.d/00-keyboard.conf' # Let target regenerate
        ]

        # Use the base rsync command but inject Pentoo-specific filters
        cmd = ['rsync', '-aAXv', '--delete'] # --delete ensures a clean target
        cmd.extend(pentoo_excludes)
        # Inherit base excludes (dev, proc, sys)
        base_excludes = ['/dev/*', '/proc/*', '/sys/*', '/mnt/*', '/run/*']
        for exc in base_excludes:
            cmd.append(f'--exclude={exc}')
            
        cmd.extend([self.source + '/', self.target])
        self._execute_spawn(cmd)





clean_list = [
    '/usr/bin/pentoo-installer', 
    '/usr/bin/pwgen', 
    '/root/.ssh/authorized_keys', # Safety first
    '/etc/udev/rules.d/70-persistent-net.rules'
]

for path in clean_list:
    target_path = os.path.join(self.target, path.lstrip('/'))
    if os.path.exists(target_path):
        os.remove(target_path)
