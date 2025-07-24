from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import secrets
import json
from cryptography.fernet import Fernet
import os

Base = declarative_base()

class User(Base):
    """User model for storing GitHub user information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    github_login = Column(String(255), unique=True, index=True, nullable=False)
    github_name = Column(String(255), nullable=True)
    github_email = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    encrypted_github_token = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class Session(Base):
    """Session model for managing user sessions"""
    __tablename__ = "sessions"
    
    id = Column(String(255), primary_key=True)  # Session token
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    last_accessed = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    is_active = Column(Boolean, default=True)
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate a secure session ID"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_expiry_time(hours: int = 24 * 7) -> datetime:
        """Generate expiry time (default: 7 days)"""
        return datetime.utcnow() + timedelta(hours=hours)

class TokenEncryption:
    """Utility class for encrypting and decrypting GitHub tokens"""
    
    @staticmethod
    def get_encryption_key() -> bytes:
        """Get or generate encryption key"""
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            # Generate a new key - in production, this should be stored securely
            key = Fernet.generate_key()
            print(f"Generated new encryption key: {key.decode()}")
            print("Please add this to your environment variables as ENCRYPTION_KEY")
        else:
            key = key.encode()
        return key
    
    @staticmethod
    def encrypt_token(token: str) -> str:
        """Encrypt a GitHub token"""
        key = TokenEncryption.get_encryption_key()
        f = Fernet(key)
        encrypted_token = f.encrypt(token.encode())
        return encrypted_token.decode()
    
    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """Decrypt a GitHub token"""
        key = TokenEncryption.get_encryption_key()
        f = Fernet(key)
        decrypted_token = f.decrypt(encrypted_token.encode())
        return decrypted_token.decode() 
    