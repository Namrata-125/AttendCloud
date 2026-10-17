import socket
from config import Config
from app import create_app

def get_lan_ip():
    """Discover the local IPv4 address of this machine on the active LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Route discovery without transmitting packets
        s.connect(('10.255.255.255', 1))
        lan_ip = s.getsockname()[0]
    except Exception:
        lan_ip = '127.0.0.1'
    finally:
        s.close()
    return lan_ip

app = create_app()

if __name__ == '__main__':
    lan_ip = get_lan_ip()
    port = Config.PORT

    print("\n" + "=" * 65)
    print("  AttendCloud: LAN-Based SaaS Attendance Management System")
    print("  Powered by Custom Cloud Controller & SQLite (HDFS Ready)")
    print("=" * 65)
    print(f"  [+] Local Access URL   : http://localhost:{port}")
    print(f"  [+] LAN Access URL     : http://{lan_ip}:{port}")
    print(f"  [+] Server Binding     : {Config.HOST}:{port}")
    print(f"  [+] Cloud Controller   : {Config.CLOUD_CONTROLLER_NAME} (Online)")
    hdfs_arch = "Phase 2 (Live Hadoop HDFS Sync Active)" if Config.HDFS_ENABLED else "Phase 1 (Local Cloud Staging Active)"
    print(f"  [+] HDFS Architecture  : {hdfs_arch}")
    print("=" * 65)
    print("  * Devices on the same Wi-Fi / LAN can open the LAN Access URL.")
    print("  * Press CTRL + C to gracefully stop the server.\n")

    # Binds to 0.0.0.0 to allow access from any device on the local network
    app.run(host=Config.HOST, port=port, debug=Config.DEBUG)
