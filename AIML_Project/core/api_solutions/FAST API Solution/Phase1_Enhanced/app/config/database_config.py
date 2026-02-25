"""
Database Configuration Manager
Handles configuration for all 8 Oracle databases
CQE_NFT: Direct auth (no CyberArk)
All WRITE databases: CyberArk
All READ databases: Direct auth
"""
from typing import Dict
import os


def get_databases_config() -> Dict:
    """
    Generate database configurations for all 8 databases
    Reads from environment variables
    
    Database Access Matrix:
    - CQE_NFT: Read/Write (DQL + DML) - Direct Auth
    - CD_PTE_READ: Read-only (DQL) - Direct Auth
    - CD_PTE_WRITE: Write (DML) - CyberArk
    - CAS_PTE_READ: Read-only (DQL) - Direct Auth
    - CAS_PTE_WRITE: Write (DML) - CyberArk
    - PORTAL_PTE_READ: Read-only (DQL) - Direct Auth
    - PORTAL_PTE_WRITE: Write (DML) - CyberArk
    """
    
    databases = {}
    
    # ========================================
    # Database 1: CQE_NFT (DQL + DML, Direct Auth)
    # ========================================
    databases["CQE_NFT"] = {
        "host": os.getenv("CQE_NFT_HOST"),
        "port": int(os.getenv("CQE_NFT_PORT", "1521")),
        "service_name": os.getenv("CQE_NFT_SERVICE_NAME"),
        "username": os.getenv("CQE_NFT_USERNAME"),
        "password": os.getenv("CQE_NFT_PASSWORD"),
        "use_cyberark": False,  # Direct auth
        "allowed_operations": ["DQL", "DML"],
        "secret_key": os.getenv("CQE_NFT_SECRET_KEY"),
        "api_keys": os.getenv("CQE_NFT_API_KEYS"),
        "pool_min": int(os.getenv("CQE_NFT_POOL_MIN", "2")),
        "pool_max": int(os.getenv("CQE_NFT_POOL_MAX", "10")),
        "pool_increment": int(os.getenv("CQE_NFT_POOL_INCREMENT", "1")),
    }
    
    # ========================================
    # Database 2: CD_PTE_READ (DQL only, Direct Auth)
    # ========================================
    databases["CD_PTE_READ"] = {
        "host": os.getenv("CD_PTE_READ_HOST"),
        "port": int(os.getenv("CD_PTE_READ_PORT", "1521")),
        "service_name": os.getenv("CD_PTE_READ_SERVICE_NAME"),
        "username": os.getenv("CD_PTE_READ_USERNAME"),
        "password": os.getenv("CD_PTE_READ_PASSWORD"),
        "use_cyberark": False,
        "allowed_operations": ["DQL"],
        "secret_key": os.getenv("CD_PTE_READ_SECRET_KEY"),
        "api_keys": os.getenv("CD_PTE_READ_API_KEYS"),
        "pool_min": int(os.getenv("CD_PTE_READ_POOL_MIN", "2")),
        "pool_max": int(os.getenv("CD_PTE_READ_POOL_MAX", "10")),
        "pool_increment": int(os.getenv("CD_PTE_READ_POOL_INCREMENT", "1")),
    }
    
    # ========================================
    # Database 3: CD_PTE_WRITE (DML only, CyberArk)
    # ========================================
    databases["CD_PTE_WRITE"] = {
        "host": os.getenv("CD_PTE_WRITE_HOST"),
        "port": int(os.getenv("CD_PTE_WRITE_PORT", "1521")),
        "service_name": os.getenv("CD_PTE_WRITE_SERVICE_NAME"),
        "username": os.getenv("CD_PTE_WRITE_USERNAME"),
        "password": os.getenv("CD_PTE_WRITE_PASSWORD"),
        "use_cyberark": os.getenv("CYBERARK_ENABLED", "false").lower() == "true",
        "allowed_operations": ["DML"],
        "secret_key": os.getenv("CD_PTE_WRITE_SECRET_KEY"),
        "api_keys": os.getenv("CD_PTE_WRITE_API_KEYS"),
        "pool_min": int(os.getenv("CD_PTE_WRITE_POOL_MIN", "2")),
        "pool_max": int(os.getenv("CD_PTE_WRITE_POOL_MAX", "10")),
        "pool_increment": int(os.getenv("CD_PTE_WRITE_POOL_INCREMENT", "1")),
        "cyberark_safe": os.getenv("CD_PTE_WRITE_CYBERARK_SAFE"),
        "cyberark_object": os.getenv("CD_PTE_WRITE_CYBERARK_OBJECT"),
    }
    
    # ========================================
    # Database 4: CAS_PTE_READ (DQL only, Direct Auth)
    # ========================================
    databases["CAS_PTE_READ"] = {
        "host": os.getenv("CAS_PTE_READ_HOST"),
        "port": int(os.getenv("CAS_PTE_READ_PORT", "1521")),
        "service_name": os.getenv("CAS_PTE_READ_SERVICE_NAME"),
        "username": os.getenv("CAS_PTE_READ_USERNAME"),
        "password": os.getenv("CAS_PTE_READ_PASSWORD"),
        "use_cyberark": False,
        "allowed_operations": ["DQL"],
        "secret_key": os.getenv("CAS_PTE_READ_SECRET_KEY"),
        "api_keys": os.getenv("CAS_PTE_READ_API_KEYS"),
        "pool_min": int(os.getenv("CAS_PTE_READ_POOL_MIN", "2")),
        "pool_max": int(os.getenv("CAS_PTE_READ_POOL_MAX", "10")),
        "pool_increment": int(os.getenv("CAS_PTE_READ_POOL_INCREMENT", "1")),
    }
    
    # ========================================
    # Database 5: CAS_PTE_WRITE (DML only, CyberArk)
    # ========================================
    databases["CAS_PTE_WRITE"] = {
        "host": os.getenv("CAS_PTE_WRITE_HOST"),
        "port": int(os.getenv("CAS_PTE_WRITE_PORT", "1521")),
        "service_name": os.getenv("CAS_PTE_WRITE_SERVICE_NAME"),
        "username": os.getenv("CAS_PTE_WRITE_USERNAME"),
        "password": os.getenv("CAS_PTE_WRITE_PASSWORD"),
        "use_cyberark": os.getenv("CYBERARK_ENABLED", "false").lower() == "true",
        "allowed_operations": ["DML"],
        "secret_key": os.getenv("CAS_PTE_WRITE_SECRET_KEY"),
        "api_keys": os.getenv("CAS_PTE_WRITE_API_KEYS"),
        "pool_min": int(os.getenv("CAS_PTE_WRITE_POOL_MIN", "2")),
        "pool_max": int(os.getenv("CAS_PTE_WRITE_POOL_MAX", "10")),
        "pool_increment": int(os.getenv("CAS_PTE_WRITE_POOL_INCREMENT", "1")),
        "cyberark_safe": os.getenv("CAS_PTE_WRITE_CYBERARK_SAFE"),
        "cyberark_object": os.getenv("CAS_PTE_WRITE_CYBERARK_OBJECT"),
    }
    
    # ========================================
    # Database 6: PORTAL_PTE_READ (DQL only, Direct Auth)
    # ========================================
    databases["PORTAL_PTE_READ"] = {
        "host": os.getenv("PORTAL_PTE_READ_HOST"),
        "port": int(os.getenv("PORTAL_PTE_READ_PORT", "1521")),
        "service_name": os.getenv("PORTAL_PTE_READ_SERVICE_NAME"),
        "username": os.getenv("PORTAL_PTE_READ_USERNAME"),
        "password": os.getenv("PORTAL_PTE_READ_PASSWORD"),
        "use_cyberark": False,
        "allowed_operations": ["DQL"],
        "secret_key": os.getenv("PORTAL_PTE_READ_SECRET_KEY"),
        "api_keys": os.getenv("PORTAL_PTE_READ_API_KEYS"),
        "pool_min": int(os.getenv("PORTAL_PTE_READ_POOL_MIN", "2")),
        "pool_max": int(os.getenv("PORTAL_PTE_READ_POOL_MAX", "10")),
        "pool_increment": int(os.getenv("PORTAL_PTE_READ_POOL_INCREMENT", "1")),
    }
    
    # ========================================
    # Database 7: PORTAL_PTE_WRITE (DML only, CyberArk)
    # ========================================
    databases["PORTAL_PTE_WRITE"] = {
        "host": os.getenv("PORTAL_PTE_WRITE_HOST"),
        "port": int(os.getenv("PORTAL_PTE_WRITE_PORT", "1521")),
        "service_name": os.getenv("PORTAL_PTE_WRITE_SERVICE_NAME"),
        "username": os.getenv("PORTAL_PTE_WRITE_USERNAME"),
        "password": os.getenv("PORTAL_PTE_WRITE_PASSWORD"),
        "use_cyberark": os.getenv("CYBERARK_ENABLED", "false").lower() == "true",
        "allowed_operations": ["DML"],
        "secret_key": os.getenv("PORTAL_PTE_WRITE_SECRET_KEY"),
        "api_keys": os.getenv("PORTAL_PTE_WRITE_API_KEYS"),
        "pool_min": int(os.getenv("PORTAL_PTE_WRITE_POOL_MIN", "2")),
        "pool_max": int(os.getenv("PORTAL_PTE_WRITE_POOL_MAX", "10")),
        "pool_increment": int(os.getenv("PORTAL_PTE_WRITE_POOL_INCREMENT", "1")),
        "cyberark_safe": os.getenv("PORTAL_PTE_WRITE_CYBERARK_SAFE"),
        "cyberark_object": os.getenv("PORTAL_PTE_WRITE_CYBERARK_OBJECT"),
    }
    
    return databases


def get_database_names() -> list:
    """Get list of all database names"""
    return [
        "CQE_NFT",
        "CD_PTE_READ",
        "CD_PTE_WRITE",
        "CAS_PTE_READ",
        "CAS_PTE_WRITE",
        "PORTAL_PTE_READ",
        "PORTAL_PTE_WRITE"
    ]


def is_write_database(db_name: str) -> bool:
    """Check if database is a write database"""
    return "WRITE" in db_name.upper()


def is_read_database(db_name: str) -> bool:
    """Check if database is a read database"""
    return "READ" in db_name.upper()


def uses_cyberark(db_name: str) -> bool:
    """Check if database uses CyberArk authentication"""
    # Only WRITE databases use CyberArk (except CQE_NFT)
    return is_write_database(db_name) and db_name.upper() != "CQE_NFT"