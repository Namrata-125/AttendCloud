import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration for AttendCloud."""
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'attendcloud-lan-saas-secret-key-2026')

    # Storage Paths
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
    DATABASE_PATH = os.path.join(DATA_DIR, 'attendcloud.db')

    # Network / LAN Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')

    # Cloud Controller & HDFS Parameters (Future Phase Integration)
    CLOUD_CONTROLLER_NAME = 'AttendCloud-Primary-Controller'
    CLOUD_CONTROLLER_MODE = 'LAN SaaS Hybrid (Edge + Archival)'
    
    # HDFS settings (Defaults ready for Hadoop cluster connectivity)
    HDFS_ENABLED = os.environ.get('HDFS_ENABLED', 'True').lower() in ('true', '1', 'yes')

    HDFS_NAMENODE_HOST = os.environ.get('HDFS_NAMENODE_HOST', '127.0.0.1')
    HDFS_NAMENODE_PORT = int(os.environ.get('HDFS_NAMENODE_PORT', 9870))  # WebHDFS default HTTP port
    HDFS_USER = os.environ.get('HDFS_USER', 'ndaav')
    HDFS_ARCHIVE_DIR = os.environ.get('HDFS_ARCHIVE_DIR', '/attendcloud/archive')

# Ensure essential directories exist
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(Config.EXPORTS_DIR, exist_ok=True)
