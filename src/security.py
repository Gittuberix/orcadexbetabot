import os
import base64
from cryptography.fernet import Fernet
import secrets
import logging
import platform
import hashlib
import json
from typing import Optional, Dict
import psutil
import uuid

class SecurityManager:
    def __init__(self, storage_dir: str = ".secure"):
        self.storage_dir = storage_dir
        self.machine_id = self._get_machine_id()
        self.encryption_key = None
        self.secure_storage = {}
        self._initialize_security()
        
    def _get_machine_id(self) -> str:
        """Generiert eine einzigartige Maschinen-ID basierend auf Hardware"""
        try:
            # Hardware-Informationen sammeln
            system_info = {
                'machine': platform.machine(),
                'processor': platform.processor(),
                'node': platform.node(),
                'mac': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                               for elements in range(0,2*6,2)][::-1]),
                'disk_id': self._get_disk_id()
            }
            
            # Hash aus Hardware-Informationen erstellen
            return hashlib.sha256(json.dumps(system_info, sort_keys=True).encode()).hexdigest()
            
        except Exception as e:
            logging.error(f"Fehler bei der Maschinen-ID-Generierung: {e}")
            return secrets.token_hex(32)
            
    def _get_disk_id(self) -> str:
        """Holt die Festplatten-Seriennummer"""
        try:
            if platform.system() == 'Windows':
                import wmi
                c = wmi.WMI()
                for disk in c.Win32_DiskDrive():
                    return disk.SerialNumber
            else:
                # Linux Disk ID
                with open('/etc/machine-id', 'r') as f:
                    return f.read().strip()
        except:
            return "unknown"
            
    def _initialize_security(self):
        """Initialisiert das Sicherheitssystem"""
        try:
            # Sicheres Verzeichnis erstellen
            os.makedirs(self.storage_dir, exist_ok=True)
            os.chmod(self.storage_dir, 0o700)  # Nur Besitzer hat Zugriff
            
            key_file = os.path.join(self.storage_dir, 'keyfile')
            if os.path.exists(key_file):
                # Schlüssel aus Datei laden und mit Maschinen-ID entschlüsseln
                with open(key_file, 'rb') as f:
                    encrypted_key = f.read()
                self.encryption_key = self._decrypt_with_machine_id(encrypted_key)
            else:
                # Neuen Schlüssel generieren
                self.encryption_key = Fernet.generate_key()
                # Schlüssel mit Maschinen-ID verschlüsseln und speichern
                encrypted_key = self._encrypt_with_machine_id(self.encryption_key)
                with open(key_file, 'wb') as f:
                    f.write(encrypted_key)
                os.chmod(key_file, 0o600)
                
        except Exception as e:
            logging.error(f"Fehler bei der Sicherheits-Initialisierung: {e}")
            raise
            
    def _encrypt_with_machine_id(self, data: bytes) -> bytes:
        """Verschlüsselt Daten mit der Maschinen-ID"""
        key = hashlib.sha256(self.machine_id.encode()).digest()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.encrypt(data)
        
    def _decrypt_with_machine_id(self, encrypted_data: bytes) -> bytes:
        """Entschlüsselt Daten mit der Maschinen-ID"""
        key = hashlib.sha256(self.machine_id.encode()).digest()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.decrypt(encrypted_data)
        
    def secure_store(self, key: str, value: str):
        """Speichert Daten sicher verschlüsselt"""
        try:
            f = Fernet(self.encryption_key)
            encrypted_value = f.encrypt(value.encode())
            
            # In Datei speichern
            file_path = os.path.join(self.storage_dir, hashlib.sha256(key.encode()).hexdigest())
            with open(file_path, 'wb') as f:
                f.write(encrypted_value)
            os.chmod(file_path, 0o600)
            
            self.secure_storage[key] = encrypted_value
            
        except Exception as e:
            logging.error(f"Fehler beim sicheren Speichern: {e}")
            
    def secure_retrieve(self, key: str) -> Optional[str]:
        """Holt verschlüsselte Daten"""
        try:
            # Aus Datei laden wenn nicht im Speicher
            if key not in self.secure_storage:
                file_path = os.path.join(self.storage_dir, hashlib.sha256(key.encode()).hexdigest())
                if not os.path.exists(file_path):
                    return None
                with open(file_path, 'rb') as f:
                    self.secure_storage[key] = f.read()
                    
            f = Fernet(self.encryption_key)
            decrypted_value = f.decrypt(self.secure_storage[key])
            return decrypted_value.decode()
            
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Daten: {e}")
            return None

    def secure_delete(self, key: str):
        """Löscht Daten sicher"""
        try:
            # Aus Speicher entfernen
            if key in self.secure_storage:
                del self.secure_storage[key]
                
            # Datei sicher löschen
            file_path = os.path.join(self.storage_dir, hashlib.sha256(key.encode()).hexdigest())
            if os.path.exists(file_path):
                # Überschreiben mit Zufallsdaten
                with open(file_path, 'wb') as f:
                    f.write(secrets.token_bytes(1024))
                # Datei löschen
                os.remove(file_path)
                
        except Exception as e:
            logging.error(f"Fehler beim sicheren Löschen: {e}") 