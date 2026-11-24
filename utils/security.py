# -*- coding: utf-8 -*-
"""
密码加密工具
采用 SHA-256 + 固定盐值进行单向哈希，避免明文存储密码。
（本科毕业设计采用简单可靠方案，实际生产环境建议使用 bcrypt 等更安全算法。）
"""
import hashlib

# 固定盐值，增加哈希强度
_SALT = "recomind#2024#salt"


def hash_password(password: str) -> str:
    """对明文密码进行哈希，返回十六进制字符串。"""
    data = (_SALT + password).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """校验明文密码是否与已存储的哈希一致。"""
    return hash_password(password) == hashed
