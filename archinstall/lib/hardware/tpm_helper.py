def bind_luks_to_tpm(installation, device_path, slot=1):
    """
    Uses Clevis or systemd-enroll-tpm2 to seal the NVMe LUKS key to the hardware.
    Works on amd64 (TPM2) and arm64 (TPM HATs).
    """
    info(f"Sealing LUKS key for {device_path} to TPM2...")
    
    # Check if tpm2-tools is available in the chroot
    installation.run(["emerge", "--getbinpkg", "app-crypt/tpm2-tools", "app-crypt/clevis"])
    
    # The actual binding command
    # This ensures the NVMe HAT only decrypts on THIS RPi5/Threadripper
    installation.run([
        "clevis", "luks", "bind", "-d", device_path, "tpm2", "{}", 
        "-s", str(slot)
    ])
