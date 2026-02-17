import socket
import struct

def send_magic_packet(mac_address: str) -> str:
    """
    Sends a Wake-on-LAN magic packet to the specified MAC address.
    MAC address format: "AA:BB:CC:DD:EE:FF" or "AA-BB-..."
    """
    try:
        # Normalize MAC address
        mac_clean = mac_address.replace(":", "").replace("-", "")
        
        if len(mac_clean) != 12:
            return f"Fehler: Ungültiges MAC-Format ({mac_address}). Erwarte 12 Hex-Zeichen."

        # Create Magic Packet
        # 6 bytes of FF followed by 16 repetitions of the MAC address
        data = b'\xFF' * 6 + (bytes.fromhex(mac_clean)) * 16
        
        # Broadcast via UDP
        # Try port 9 (standard) and 7 (echo)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, ("255.255.255.255", 9))
            
        return f"Magic Packet (Wake-on-LAN) an {mac_address} gesendet."
    except Exception as e:
        return f"Fehler beim Senden des Magic Packets: {e}"
