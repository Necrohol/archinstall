
import archinstall
from archinstall.lib.configuration import Configuration
from archinstall.lib.installer import Installer
from archinstall.lib.output import info, warn
from archinstall.lib.profiles import Profile
from archinstall.lib.utils.util import spawn
from archinstall.lib.gentoo_deploy import GentooDeployer  # The helper we defined

def perform_installation(mountpoint: str):
	"""
	The main Gentoo deployment logic.
	Replaces the standard Arch 'pacstrap' and 'bootloader' steps.
	"""
	# 1. Initialize the Installer object (handles mounts/fstab)
	with Installer(mountpoint, disk_config=archinstall.arguments.get('disk_config')) as installation:
		if installation.mount_ordered_layout():
			
			# --- GENTOO STEP 1: DEPLOY ROOTFS ---
			# We rsync the Live environment (SquashFS) to the Target (NVMe/SD)
			deployer = GentooDeployer(target=mountpoint)
			deployer.rsync_rootfs()

			# --- GENTOO STEP 2: HARDWARE OPTIMIZATION ---
			# Dynamic MAKEOPTS, CPU flags, and scheduling (Idle/Nice)
			deployer.inject_power_configs()

			# --- GENTOO STEP 3: CHROOT OPERATIONS ---
			# eselect-repository, shallow git sync, and eix-update
			info("Finalizing Gentoo configuration inside chroot...")
			installation.run(["eselect", "repository", "add", "gentoo", "git", "https://github.com/gentoo-mirror/gentoo"])
			installation.run(["emaint", "sync", "-r", "gentoo"])
			installation.run(["eix-update"])

			# --- GENTOO STEP 4: CLEANUP ---
			# Remove live-cd artifacts
			info("Cleaning up live-cd artifacts...")
			installation.run(["emerge", "--unmerge", "app-admin/pwgen"])

			# --- GENTOO STEP 5: BOOTLOADER ---
			# Check for RPi and apply UEFI shim if needed
			if archinstall.arguments.get('hardware_model', '').startswith('RPI'):
				from archinstall.lib.hardware.rpi_helper import install_rpi_uefi
				install_rpi_uefi(mountpoint, archinstall.arguments['hardware_model'])
			
			# Standard GRUB install (Gentoo-style)
			installation.run(["grub-install", "--target=arm64-efi", "--efi-directory=/boot/efi", "--removable"])
			installation.run(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])

			info("Installation completed successfully!")

def main():
	"""
	The TUI Guided Setup. 
	Uses archinstall's menu system to gather user intent.
	"""
	# Use archinstall's built-in TUI to get disk, networking, and user info
	# This keeps your code clean and leverages upstream's hard work.
	archinstall.tui.get_config()

	if archinstall.arguments.get('confirm_config'):
		# Start the actual work
		mountpoint = "/mnt/gentoo"
		perform_installation(mountpoint)

if __name__ == 'archinstall.scripts.gentoo':
	main()
