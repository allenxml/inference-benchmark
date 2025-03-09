# -*- coding: utf-8 -*-
"""
安全工具模块，提供加密存储等安全相关功能。
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureStorage:
    """安全存储类，提供加密和解密功能"""
    
    def __init__(self, key_file: str = "config/secret.key"):
        """
        初始化安全存储
        
        Args:
            key_file: 密钥文件路径
        """
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_generate_key(self) -> bytes:
        """加载或生成密钥"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key
    
    def encrypt(self, data: str) -> str:
        """
        加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            加密后的数据（Base64编码的字符串）
        """
        if not data:
            return ""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的数据（Base64编码的字符串）
            
        Returns:
            解密后的数据
        """
        if not encrypted_data:
            return ""
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            # 解密失败，返回空字符串
            return ""


class PasswordManager:
    """密码管理器，提供密码派生和验证功能"""
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> tuple:
        """
        从密码派生密钥
        
        Args:
            password: 密码
            salt: 盐值，如果为None则生成新的盐值
            
        Returns:
            (密钥, 盐值) 元组
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def verify_password(password: str, key: bytes, salt: bytes) -> bool:
        """
        验证密码
        
        Args:
            password: 要验证的密码
            key: 存储的密钥
            salt: 盐值
            
        Returns:
            密码是否正确
        """
        derived_key, _ = PasswordManager.derive_key(password, salt)
        return derived_key == key


def mask_sensitive_data(data: str, visible_prefix: int = 4, visible_suffix: int = 4) -> str:
    """
    掩码敏感数据，只显示前几位和后几位
    
    Args:
        data: 敏感数据
        visible_prefix: 显示的前缀长度
        visible_suffix: 显示的后缀长度
        
    Returns:
        掩码后的数据
    """
    if not data:
        return ""
    
    if len(data) <= visible_prefix + visible_suffix:
        return "*" * len(data)
    
    return data[:visible_prefix] + "*" * (len(data) - visible_prefix - visible_suffix) + data[-visible_suffix:] 