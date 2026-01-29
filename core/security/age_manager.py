"""
Age Key Manager - Hierarchical Age/SOPS Key Management

Manages 3-level key hierarchy:
- Master Key: Disaster recovery (can decrypt everything)
- Host Key: Infrastructure secrets (Proxmox API, SSH)
- Services Key: Application secrets (DB passwords, API tokens)
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AgeKeyManager:
    """Manages Age encryption keys for SOPS integration."""
    
    def __init__(self, base_path: str = "/var/lib/nhi"):
        self.base_path = Path(base_path)
        self.age_path = self.base_path / "age"
        self.sops_config_path = self.base_path / ".sops.yaml"
        
    def setup(self) -> bool:
        """
        Initialize Age key hierarchy.
        
        Returns:
            True if setup completed successfully
        """
        self.age_path.mkdir(parents=True, exist_ok=True)
        
        # Generate keys in order
        master_key, master_pub = self._generate_key("master")
        host_key, host_pub = self._generate_key("host")
        services_key, services_pub = self._generate_key("services")
        
        # Create SOPS config
        self._create_sops_config(master_pub, host_pub, services_pub)
        
        return True
    
    def _generate_key(self, name: str) -> Tuple[Path, str]:
        """
        Generate an Age keypair.
        
        Args:
            name: Key name (master, host, services)
            
        Returns:
            Tuple of (private_key_path, public_key_string)
        """
        private_key_path = self.age_path / f"{name}.key"
        
        if private_key_path.exists():
            logger.info(f"Key {name} already exists, skipping generation")
            public_key = self._get_public_key(private_key_path)
            return private_key_path, public_key
        
        # Generate new key
        result = subprocess.run(
            ["age-keygen", "-o", str(private_key_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to generate {name} key: {result.stderr}")
        
        # Set secure permissions
        os.chmod(private_key_path, 0o600)
        
        # Extract public key
        public_key = self._get_public_key(private_key_path)
        
        # Save public key separately
        pub_key_path = self.age_path / f"{name}.key.pub"
        with open(pub_key_path, 'w') as f:
            f.write(public_key + "\n")
        
        logger.info(f"Generated {name} key: {public_key[:20]}...")
        
        return private_key_path, public_key
    
    def _get_public_key(self, private_key_path: Path) -> str:
        """Extract public key from private key file."""
        result = subprocess.run(
            ["age-keygen", "-y", str(private_key_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to extract public key: {result.stderr}")
        
        return result.stdout.strip()
    
    def _create_sops_config(self, master_pub: str, host_pub: str, services_pub: str):
        """Create SOPS configuration file."""
        config = f"""# SOPS Configuration for NHI-CORE
# Auto-generated - Do not edit manually

creation_rules:
  # Infrastructure secrets (Proxmox API, SSH keys)
  - path_regex: secrets/infrastructure/.*\\.yaml$
    age: >-
      {master_pub},
      {host_pub}

  # Application/Service secrets (DB passwords, API tokens)
  - path_regex: secrets/services/.*\\.yaml$
    age: >-
      {master_pub},
      {services_pub}

  # Default: all secrets encrypted with master + services
  - path_regex: secrets/.*\\.yaml$
    age: >-
      {master_pub},
      {services_pub}
"""
        
        with open(self.sops_config_path, 'w') as f:
            f.write(config)
        
        logger.info(f"Created SOPS config at {self.sops_config_path}")
    
    def get_master_key_content(self) -> Optional[str]:
        """
        Read master key content for backup display.
        
        Returns:
            Master key content or None if not found
        """
        master_key_path = self.age_path / "master.key"
        
        if not master_key_path.exists():
            return None
        
        with open(master_key_path, 'r') as f:
            return f.read()
    
    def verify_backup_confirmation(self, user_input: str) -> bool:
        """
        Verify user has confirmed key backup.
        
        Args:
            user_input: User's confirmation string
            
        Returns:
            True if confirmed correctly
        """
        return user_input.strip() == "I HAVE SAVED THE KEY"


def check_age_installed() -> bool:
    """Check if age is installed on the system."""
    try:
        result = subprocess.run(
            ["age", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_age():
    """Install age encryption tool."""
    logger.info("Installing age...")
    
    # Try apt first (Ubuntu/Debian)
    result = subprocess.run(
        ["apt-get", "install", "-y", "age"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("Age installed via apt")
        return True
    
    # Fallback: download binary
    import urllib.request
    import zipfile
    import tempfile
    
    AGE_VERSION = "1.1.1"
    AGE_URL = f"https://github.com/FiloSottile/age/releases/download/v{AGE_VERSION}/age-v{AGE_VERSION}-linux-amd64.tar.gz"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = os.path.join(tmpdir, "age.tar.gz")
        urllib.request.urlretrieve(AGE_URL, archive_path)
        
        subprocess.run(["tar", "-xzf", archive_path, "-C", tmpdir], check=True)
        
        # Copy binaries
        for binary in ["age", "age-keygen"]:
            src = os.path.join(tmpdir, f"age/{binary}")
            dst = f"/usr/local/bin/{binary}"
            subprocess.run(["cp", src, dst], check=True)
            os.chmod(dst, 0o755)
    
    logger.info("Age installed from GitHub releases")
    return True
