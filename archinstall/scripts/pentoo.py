import os
from pathlib import Path
from archinstall.lib.command import SysCommand
from archinstall.lib.output import info, error
from archinstall.lib.hardware import HardwareHelper, BootIntegrityGuard
from archinstall.lib.pentoo_deploy import deploy_pentoo_iso

def main(config_handler):
    """
    The Easy Button: Deploy Pentoo SquashFS -> Poke Hardware -> Done.
    """
    # 1. Setup paths
    target = Path(config_handler.args.get('installation_path', '/mnt/gentoo'))
    
    # 2. Hardware 'Brain' Initialization
    # This automatically finds the right TOML in definitions/
    hw = HardwareHelper(config_handler.args)
    
    # Pre-Install: e.g., Set RPi5 PCIe to Gen 3 for faster rsync
    hw.pre_install()

    # 3. The 'Live-to-Disk' Copy
    # This is your existing pentoo_deploy logic (rsync -aAX)
    source_sqfs = _find_sqfs()
    if source_sqfs:
        deploy_pentoo_iso(str(target), str(source_sqfs))
    else:
        error("Source SquashFS not found! Check ISO mount.")
        return

    # 4. THE EASY BUTTON: Hardware Injection
    # This handles ARM64 kernels, RPi UEFI, Broadcom drivers, or Intel Microcode
    # It reads the TOML and 'pokes' the target disk automatically.
    info("Applying hardware-specific 'Pokes'...")
    hw.post_install()

    # 5. Finalize (User/Pass/Hostname)
    _finalize_pentoo(target, config_handler)

    # 6. Integrity Guard
    # Verification to ensure we don't reboot into a black screen
    guard = BootIntegrityGuard(config_handler.args, hw.hw_def)
    if guard.verify_all():
        info("Pentoo Deployment Successful. Hardware verified.")
    else:
        error("Hardware verification failed! Check /var/log/archinstall/install.log")

def _finalize_pentoo(target, config):
    # Standard Gentoo/Pentoo house-keeping
    hostname = config.args.get('hostname', 'pentoo-box')
    info(f"Setting hostname: {hostname}")
    (target / "etc/hostname").write_text(f"{hostname}\n")
    
    # Set root password using chroot
    root_pw = config.args.get('!root_password', 'pentoo')
    SysCommand(f"echo 'root:{root_pw}' | arch-chroot {target} chpasswd")

def _find_sqfs():
    for p in ["/mnt/cdrom/image.squashfs", "/run/archiso/bootmnt/pentoo.sqfs"]:
        if Path(p).exists(): return p
    return None
