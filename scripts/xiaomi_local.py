#!/usr/bin/env python3
"""
xiaomi_local.py - 小米设备本地局域网控制

功能:
- 设备发现 (mDNS/UDP 广播)
- miIO/MIOT 本地协议
- 本地加密通信
- 离线控制支持

协议参考: https://github.com/OpenMiHome/mihome-binary-protocol
"""

import socket
import struct
import json
import time
import hashlib
import logging
from typing import Optional, Dict, Tuple
from pathlib import Path

try:
    from Crypto.Cipher import AES
except ImportError:
    try:
        from cryptodome.Cipher import AES
    except ImportError:
        print("[ERROR] 请安装 pycryptodome: pip install pycryptodome")
        exit(1)


logger = logging.getLogger("xiaomi_local")


class MiIOPacket:
    """
    miIO 协议数据包解析与构建

    数据包结构:
    - Header (32 bytes)
        - Magic (2): 0x2131
        - Length (2)
        - Unknown (4): 0x00000000
        - Device ID (4)
        - Timestamp (4)
        - Checksum (16)
    - Payload (variable, encrypted)
    """

    MAGIC = bytes([0x21, 0x31])
    HEADER_LEN = 32

    @classmethod
    def parse(cls, data: bytes, token: bytes) -> Tuple[Dict, Optional[Dict]]:
        """
        解析 miIO 数据包

        Args:
            data: 原始数据
            token: 设备 token (16 bytes)

        Returns:
            (header_dict, payload_dict)
        """
        if len(data) < cls.HEADER_LEN:
            raise ValueError("数据包太短")

        if data[:2] != cls.MAGIC:
            raise ValueError("无效 Magic 标识")

        length = struct.unpack(">H", data[2:4])[0]
        device_id = struct.unpack(">I", data[8:12])[0]
        timestamp = struct.unpack(">I", data[12:16])[0]

        encrypted_payload = data[cls.HEADER_LEN:length]
        checksum = data[16:32]

        # 解密
        if encrypted_payload:
            payload = cls._decrypt(encrypted_payload, token)
            try:
                payload_json = json.loads(payload)
            except json.JSONDecodeError:
                payload_json = {"raw": payload.decode("utf-8", errors="ignore")}
        else:
            payload_json = None

        header = {
            "length": length,
            "device_id": f"{device_id:08x}",
            "timestamp": timestamp,
            "checksum": checksum.hex(),
        }
        return header, payload_json

    @classmethod
    def build(cls, payload: Dict, token: bytes, device_id: int, timestamp: int = None) -> bytes:
        """
        构建 miIO 数据包

        Args:
            payload: JSON 负载
            token: 设备 token (16 bytes)
            device_id: 设备 ID
            timestamp: 时间戳 (可选，默认当前时间)
        """
        if timestamp is None:
            timestamp = int(time.time())

        # 加密 payload
        payload_str = json.dumps(payload)
        encrypted = cls._encrypt(payload_str.encode(), token)

        # 构建头
        length = cls.HEADER_LEN + len(encrypted)
        header = bytearray(cls.HEADER_LEN)
        header[0:2] = cls.MAGIC
        header[2:4] = struct.pack(">H", length)
        header[4:8] = bytes(4)  # unknown
        header[8:12] = struct.pack(">I", device_id)
        header[12:16] = struct.pack(">I", timestamp)

        # 计算校验和: MD5(token + header_without_checksum + encrypted)
        checksum_data = token + bytes(header[:16]) + encrypted
        checksum = hashlib.md5(checksum_data).digest()
        header[16:32] = checksum

        return bytes(header) + encrypted

    @classmethod
    def _encrypt(cls, data: bytes, token: bytes) -> bytes:
        """AES-CBC 加密"""
        key = hashlib.md5(token).digest()
        iv = hashlib.md5(key + token).digest()
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # PKCS7 padding
        padding_len = 16 - (len(data) % 16)
        padded = data + bytes([padding_len] * padding_len)
        return cipher.encrypt(padded)

    @classmethod
    def _decrypt(cls, data: bytes, token: bytes) -> bytes:
        """AES-CBC 解密"""
        key = hashlib.md5(token).digest()
        iv = hashlib.md5(key + token).digest()
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(data)

        # Remove PKCS7 padding
        padding_len = decrypted[-1]
        return decrypted[:-padding_len]


class XiaomiLocal:
    """
    小米设备本地控制客户端

    使用 miIO/MIOT 协议通过局域网直连设备
    """

    DEFAULT_PORT = 54321
    TIMEOUT = 5

    def __init__(self, ip: str, token: str = "", port: int = None):
        """
        初始化本地客户端

        Args:
            ip: 设备 IP 地址
            token: 设备 token (16 字节 hex 或 base64)
            port: 设备端口 (默认 54321)
        """
        self.ip = ip
        self.port = port or self.DEFAULT_PORT
        self.token = self._parse_token(token)
        self.device_id = 0
        self._socket = None

    def _parse_token(self, token: str) -> bytes:
        """解析 token (支持 hex 或 base64 格式)"""
        if not token:
            return bytes(16)  # 空token，用于发现设备

        if len(token) == 32:
            # hex 格式
            return bytes.fromhex(token)
        elif len(token) == 24:
            # base64 格式
            import base64
            return base64.b64decode(token)
        else:
            raise ValueError(f"无效 token 长度: {len(token)}")

    def connect(self) -> bool:
        """连接设备并获取 device_id"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(self.TIMEOUT)

            # 发送 hello 包获取设备信息
            resp = self.send_raw(bytes([0x21, 0x31, 0x00, 0x20] + [0] * 28))
            if resp and len(resp) >= 32:
                self.device_id = struct.unpack(">I", resp[8:12])[0]
                logger.info(f"已连接设备 {self.ip}, device_id={self.device_id:08x}")
                return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
        return False

    def send_raw(self, data: bytes) -> Optional[bytes]:
        """发送原始数据"""
        if self._socket is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(self.TIMEOUT)

        try:
            self._socket.sendto(data, (self.ip, self.port))
            resp, _ = self._socket.recvfrom(2048)
            return resp
        except socket.timeout:
            logger.warning(f"设备 {self.ip} 无响应")
            return None
        except Exception as e:
            logger.error(f"发送失败: {e}")
            return None

    def send_command(self, method: str, params: dict = None) -> Dict:
        """
        发送 miIO 命令

        Args:
            method: 命令方法，如 "get_prop", "set_power"
            params: 参数

        Returns:
            {"ok": True, "result": ...} 或 {"ok": False, "error": ...}
        """
        if self.device_id == 0 and not self.connect():
            return {"ok": False, "error": "无法连接设备"}

        payload = {
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or [],
        }

        packet = MiIOPacket.build(payload, self.token, self.device_id)
        resp = self.send_raw(packet)

        if resp:
            try:
                header, result = MiIOPacket.parse(resp, self.token)
                if result:
                    return {"ok": True, "result": result}
                else:
                    return {"ok": True, "result": header}
            except Exception as e:
                return {"ok": False, "error": f"解析响应失败: {e}"}

        return {"ok": False, "error": "设备无响应"}

    # ─────────────────────────────────────────
    # 高级控制方法
    # ─────────────────────────────────────────

    def get_properties(self, properties: list) -> Dict:
        """
        获取设备属性

        Args:
            properties: 属性列表，如 ["power", "brightness"]
        """
        return self.send_command("get_prop", properties)

    def set_property(self, property: str, value) -> Dict:
        """设置设备属性"""
        return self.send_command(f"set_{property}", [value])

    def power_on(self) -> Dict:
        """打开电源"""
        return self.send_command("set_power", ["on"])

    def power_off(self) -> Dict:
        """关闭电源"""
        return self.send_command("set_power", ["off"])

    def toggle(self) -> Dict:
        """切换电源状态"""
        return self.send_command("toggle", [])

    def set_brightness(self, brightness: int) -> Dict:
        """
        设置亮度 (0-100)

        Args:
            brightness: 亮度百分比
        """
        return self.send_command("set_bright", [brightness])

    def set_color_temp(self, temp: int) -> Dict:
        """
        设置色温

        Args:
            temp: 色温值 (K)
        """
        return self.send_command("set_ct_abx", [temp])

    def close(self):
        """关闭连接"""
        if self._socket:
            self._socket.close()
            self._socket = None


# ─────────────────────────────────────────
# 设备发现
# ─────────────────────────────────────────

def discover_devices(timeout: int = 10, bind_ip: str = "0.0.0.0") -> list:
    """
    发现局域网内的小米设备

    Args:
        timeout: 发现超时 (秒)
        bind_ip: 绑定 IP

    Returns:
        设备列表 [{"ip": ..., "model": ..., "deviceId": ...}, ...]
    """
    devices = []
    broadcast_addr = "255.255.255.255"
    port = 54321

    # 创建 UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    sock.bind((bind_ip, port))

    # 发送发现包 (hello)
    hello_packet = bytes([0x21, 0x31, 0x00, 0x20] + [0] * 28)

    logger.info(f"开始发现设备，超时 {timeout} 秒...")
    sock.sendto(hello_packet, (broadcast_addr, port))

    start_time = time.time()
    seen = set()

    while time.time() - start_time < timeout:
        try:
            data, addr = sock.recvfrom(2048)
            if len(data) >= 32 and addr[0] not in seen:
                seen.add(addr[0])
                device_id = struct.unpack(">I", data[8:12])[0]
                devices.append({
                    "ip": addr[0],
                    "port": addr[1],
                    "deviceId": f"{device_id:08x}",
                })
                logger.info(f"发现设备: {addr[0]} (ID: {device_id:08x})")
        except socket.timeout:
            break
        except Exception as e:
            logger.debug(f"接收数据错误: {e}")

    sock.close()
    return devices


# ─────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小米设备本地控制")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # discovery
    p_disc = sub.add_parser("discovery", help="发现局域网设备")
    p_disc.add_argument("--timeout", type=int, default=10)

    # control
    p_ctrl = sub.add_parser("control", help="控制设备")
    p_ctrl.add_argument("ip", help="设备 IP")
    p_ctrl.add_argument("method", help="命令方法")
    p_ctrl.add_argument("--token", default="", help="设备 token")
    p_ctrl.add_argument("--params", type=json.loads, default=None, help="参数 (JSON)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.cmd == "discovery":
        devices = discover_devices(args.timeout)
        print(f"\n发现 {len(devices)} 个设备:")
        for d in devices:
            print(f"  {d['ip']:<16} ID: {d['deviceId']}")
    elif args.cmd == "control":
        client = XiaomiLocal(args.ip, args.token)
        result = client.send_command(args.method, args.params)
        print(json.dumps(result, indent=2, ensure_ascii=False))
