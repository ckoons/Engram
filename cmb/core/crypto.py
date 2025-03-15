#!/usr/bin/env python3
"""
Cryptographic utilities for Claude Memory Bridge privacy features.

This module provides encryption, decryption, and key management for
private memory storage. It uses Fernet symmetric encryption with
locally stored keys for protecting private memories.
"""

import os
import base64
import json
import logging
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import InvalidToken

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.core.crypto")

class CryptoManager:
    """
    Manages encryption and decryption for private memories.
    
    This class handles key generation, storage, and the encryption/decryption
    process for private memories in the ClaudeMemoryBridge.
    """
    
    def __init__(self, data_dir: Optional[str] = None, client_id: str = "claude"):
        """
        Initialize the crypto manager.
        
        Args:
            data_dir: Directory to store keys. Defaults to ~/.cmb/keys.
            client_id: Client identifier for key isolation. Defaults to "claude".
        """
        self.client_id = client_id
        
        # Set up data directory
        if data_dir is None:
            data_dir = os.path.expanduser("~/.cmb")
        
        self.data_dir = data_dir
        self.keys_dir = os.path.join(data_dir, "keys")
        
        # Ensure directories exist
        os.makedirs(self.keys_dir, exist_ok=True)
        
        # Set up key paths
        self.primary_key_file = os.path.join(self.keys_dir, f"{client_id}-primary.key")
        self.emergency_key_file = os.path.join(self.keys_dir, f"{client_id}-emergency.key")
        self.keyring_file = os.path.join(self.keys_dir, f"{client_id}-keyring.json")
        
        # Initialize keys
        self.primary_key = None
        self.emergency_key = None
        self.keyring = {}
        
        # Load or generate keys
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self) -> None:
        """Load existing keys or generate new ones if they don't exist."""
        # Primary key
        if os.path.exists(self.primary_key_file):
            try:
                with open(self.primary_key_file, "rb") as f:
                    self.primary_key = f.read().strip()
                logger.info(f"Loaded primary key for {self.client_id}")
            except Exception as e:
                logger.error(f"Error loading primary key: {e}")
                self.primary_key = None
        
        if self.primary_key is None:
            self.primary_key = Fernet.generate_key()
            try:
                with open(self.primary_key_file, "wb") as f:
                    f.write(self.primary_key)
                os.chmod(self.primary_key_file, 0o600)  # Restrictive permissions
                logger.info(f"Generated new primary key for {self.client_id}")
            except Exception as e:
                logger.error(f"Error saving primary key: {e}")
        
        # Emergency key
        if os.path.exists(self.emergency_key_file):
            try:
                with open(self.emergency_key_file, "rb") as f:
                    self.emergency_key = f.read().strip()
                logger.info(f"Loaded emergency key for {self.client_id}")
            except Exception as e:
                logger.error(f"Error loading emergency key: {e}")
                self.emergency_key = None
        
        if self.emergency_key is None:
            self.emergency_key = Fernet.generate_key()
            try:
                with open(self.emergency_key_file, "wb") as f:
                    f.write(self.emergency_key)
                os.chmod(self.emergency_key_file, 0o600)  # Restrictive permissions
                logger.info(f"Generated new emergency key for {self.client_id}")
            except Exception as e:
                logger.error(f"Error saving emergency key: {e}")
        
        # Keyring
        if os.path.exists(self.keyring_file):
            try:
                with open(self.keyring_file, "r") as f:
                    self.keyring = json.load(f)
                logger.info(f"Loaded keyring for {self.client_id}")
            except Exception as e:
                logger.error(f"Error loading keyring: {e}")
                self.keyring = {}
        
        if not self.keyring:
            self.keyring = {"keys": {}, "metadata": {"version": "1.0"}}
            self._save_keyring()
            logger.info(f"Initialized new keyring for {self.client_id}")
    
    def _save_keyring(self) -> bool:
        """Save the keyring to disk."""
        try:
            with open(self.keyring_file, "w") as f:
                json.dump(self.keyring, f, indent=2)
            os.chmod(self.keyring_file, 0o600)  # Restrictive permissions
            return True
        except Exception as e:
            logger.error(f"Error saving keyring: {e}")
            return False
    
    def encrypt(self, data: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Encrypt data with a new memory-specific key.
        
        Args:
            data: The string data to encrypt
            context: Optional contextual metadata about the data
            
        Returns:
            Tuple of (key_id, encrypted_data)
        """
        # Generate a new key for this memory
        memory_key = Fernet.generate_key()
        cipher = Fernet(memory_key)
        
        # Encrypt the data
        encrypted_data = cipher.encrypt(data.encode()).decode()
        
        # Generate a key ID
        key_id = base64.urlsafe_b64encode(secrets.token_bytes(12)).decode().strip("=")
        
        # Store the memory key, encrypted with both primary and emergency keys
        primary_cipher = Fernet(self.primary_key)
        emergency_cipher = Fernet(self.emergency_key)
        
        encrypted_memory_key = {
            "primary": primary_cipher.encrypt(memory_key).decode(),
            "emergency": emergency_cipher.encrypt(memory_key).decode()
        }
        
        # Add to keyring
        self.keyring["keys"][key_id] = {
            "encrypted_key": encrypted_memory_key,
            "created": self._timestamp(),
            "context": context or {}
        }
        
        # Save updated keyring
        self._save_keyring()
        
        return key_id, encrypted_data
    
    def decrypt(self, key_id: str, encrypted_data: str, use_emergency: bool = False) -> Optional[str]:
        """
        Decrypt data using the specified key ID.
        
        Args:
            key_id: The identifier for the memory key
            encrypted_data: The encrypted data string
            use_emergency: Whether to use the emergency key for recovery
            
        Returns:
            Decrypted string or None if decryption fails
        """
        # Get the encrypted memory key
        if key_id not in self.keyring["keys"]:
            logger.error(f"Key ID {key_id} not found in keyring")
            return None
        
        encrypted_key_data = self.keyring["keys"][key_id]["encrypted_key"]
        
        # Choose primary or emergency path
        key_type = "emergency" if use_emergency else "primary"
        main_key = self.emergency_key if use_emergency else self.primary_key
        
        if key_type not in encrypted_key_data:
            logger.error(f"{key_type.capitalize()} key data not found for {key_id}")
            return None
        
        encrypted_memory_key = encrypted_key_data[key_type]
        
        try:
            # Decrypt the memory key
            cipher = Fernet(main_key)
            memory_key = cipher.decrypt(encrypted_memory_key.encode())
            
            # Use the memory key to decrypt the data
            memory_cipher = Fernet(memory_key)
            decrypted_data = memory_cipher.decrypt(encrypted_data.encode()).decode()
            
            return decrypted_data
        except InvalidToken:
            logger.error(f"Invalid token during decryption with {key_type} key")
            return None
        except Exception as e:
            logger.error(f"Error during decryption: {e}")
            return None
    
    def _timestamp(self) -> str:
        """Generate an ISO format timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def generate_access_token(self, expiry_seconds: int = 300) -> str:
        """
        Generate a temporary access token for emergency access.
        
        Args:
            expiry_seconds: How long the token should be valid, in seconds
            
        Returns:
            A temporary access token
        """
        # Implementation for emergency access would go here
        # This is a placeholder for future functionality
        return "emergency-access-not-implemented"
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """
        List all keys in the keyring with their metadata.
        
        Returns:
            List of key metadata dictionaries
        """
        result = []
        for key_id, data in self.keyring["keys"].items():
            result.append({
                "key_id": key_id,
                "created": data["created"],
                "context": data.get("context", {})
            })
        return result
    
    def rotate_primary_key(self) -> bool:
        """
        Rotate the primary encryption key and re-encrypt all memory keys.
        
        Returns:
            True if successful, False otherwise
        """
        # Generate a new primary key
        new_primary_key = Fernet.generate_key()
        new_cipher = Fernet(new_primary_key)
        old_cipher = Fernet(self.primary_key)
        
        # Re-encrypt all memory keys with the new primary key
        for key_id, data in self.keyring["keys"].items():
            try:
                encrypted_key_data = data["encrypted_key"]
                
                # Decrypt with old key and re-encrypt with new key
                memory_key = old_cipher.decrypt(encrypted_key_data["primary"].encode())
                encrypted_key_data["primary"] = new_cipher.encrypt(memory_key).decode()
                
                # Update the keyring
                self.keyring["keys"][key_id]["encrypted_key"] = encrypted_key_data
            except Exception as e:
                logger.error(f"Error rotating key {key_id}: {e}")
                return False
        
        # Save the updated keyring
        if not self._save_keyring():
            return False
        
        # Save the new primary key
        try:
            with open(self.primary_key_file, "wb") as f:
                f.write(new_primary_key)
            os.chmod(self.primary_key_file, 0o600)  # Restrictive permissions
        except Exception as e:
            logger.error(f"Error saving new primary key: {e}")
            return False
        
        # Update the instance
        self.primary_key = new_primary_key
        logger.info(f"Successfully rotated primary key for {self.client_id}")
        
        return True
    
    def delete_key(self, key_id: str) -> bool:
        """
        Delete a key from the keyring.
        
        Args:
            key_id: The ID of the key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if key_id in self.keyring["keys"]:
            del self.keyring["keys"][key_id]
            return self._save_keyring()
        return False