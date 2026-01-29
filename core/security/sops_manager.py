"""
SOPS Manager - Secrets Operations

Handles encryption/decryption of secrets using SOPS with GPG backend.
"""

import os
import subprocess
import yaml
from typing import Dict, Optional


class SOPSManager:
    """Manages encrypted secrets using SOPS."""
    
    def __init__(self, data_path: str = "/var/lib/nhi"):
        """
        Initialize SOPS manager.
        
        Args:
            data_path: Base path for NHI data
        """
        self.data_path = data_path
        self.secrets_path = os.path.join(data_path, 'secrets')
        self.sops_config = os.path.join(data_path, '.sops.yaml')
    
    def _check_sops(self) -> bool:
        """Check if SOPS is available."""
        try:
            subprocess.run(['sops', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def encrypt_file(self, input_path: str, output_path: str = None) -> str:
        """
        Encrypt a YAML file using SOPS.
        
        Args:
            input_path: Path to plaintext YAML file
            output_path: Path for encrypted output (default: same with .enc suffix)
        
        Returns:
            Path to encrypted file
        """
        if not self._check_sops():
            raise RuntimeError("SOPS not installed")
        
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}.enc{ext}"
        
        subprocess.run([
            'sops', '--config', self.sops_config,
            '--encrypt', input_path,
            '--output', output_path
        ], check=True)
        
        return output_path
    
    def decrypt_file(self, input_path: str) -> Dict:
        """
        Decrypt a SOPS-encrypted file and return contents.
        
        Args:
            input_path: Path to encrypted YAML file
        
        Returns:
            Decrypted YAML content as dictionary
        """
        if not self._check_sops():
            raise RuntimeError("SOPS not installed")
        
        result = subprocess.run([
            'sops', '--config', self.sops_config,
            '--decrypt', input_path
        ], capture_output=True, text=True, check=True)
        
        return yaml.safe_load(result.stdout)
    
    def get_secret(self, key: str, file: str = "secrets.yaml") -> Optional[str]:
        """
        Get a specific secret value.
        
        Args:
            key: Secret key name
            file: Secrets file name
        
        Returns:
            Decrypted secret value or None
        """
        secrets_file = os.path.join(self.secrets_path, file)
        
        if not os.path.exists(secrets_file):
            return None
        
        try:
            secrets = self.decrypt_file(secrets_file)
            return secrets.get(key)
        except Exception:
            return None
    
    def set_secret(self, key: str, value: str, file: str = "secrets.yaml"):
        """
        Set a secret value (encrypts file).
        
        Args:
            key: Secret key name
            value: Secret value
            file: Secrets file name
        """
        secrets_file = os.path.join(self.secrets_path, file)
        temp_file = os.path.join(self.secrets_path, f".{file}.tmp")
        
        # Load existing or create new
        secrets = {}
        if os.path.exists(secrets_file):
            try:
                secrets = self.decrypt_file(secrets_file)
            except Exception:
                pass
        
        # Update secret
        secrets[key] = value
        
        # Write temp file
        with open(temp_file, 'w') as f:
            yaml.dump(secrets, f)
        
        # Encrypt in place
        self.encrypt_file(temp_file, secrets_file)
        
        # Cleanup
        os.remove(temp_file)
    
    def list_secrets(self, file: str = "secrets.yaml") -> list:
        """
        List secret keys (not values).
        
        Args:
            file: Secrets file name
        
        Returns:
            List of secret key names
        """
        secrets_file = os.path.join(self.secrets_path, file)
        
        if not os.path.exists(secrets_file):
            return []
        
        try:
            secrets = self.decrypt_file(secrets_file)
            return list(secrets.keys())
        except Exception:
            return []
