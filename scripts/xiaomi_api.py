#!/usr/bin/env python3
"""
xiaomi_api.py - 小米 IoT 云端 API 封装

功能:
- OAuth2.0 认证与 Token 管理
- 设备列表查询
- 设备状态获取 (MIoT-Spec-V2)
- 设备控制
- 场景执行
- HTTP 请求签名 (Xiaomi Security Chip)
"""

import time
import json
import hmac
import hashlib
import base64
import struct
import logging
from urllib.parse import urlencode
from typing import Optional, Dict, List, Any

try:
    import requests
except ImportError:
    print("[ERROR] 请安装 requests: pip install requests")
    exit(1)

try:
    from Crypto.Cipher import AES
except ImportError:
    try:
        from cryptodome.Cipher import AES
    except ImportError:
        print("[ERROR] 请安装 pycryptodome: pip install pycryptodome")
        exit(1)


logger = logging.getLogger("xiaomi_api")


class XiaomiSecurityChip:
    """
    小米安全芯片 - 用于 HTTP 请求签名
    基于 miio/mitdm 协议的签名算法
    """

    def __init__(self, secret: str):
        self._secret = secret.encode() if isinstance(secret, str) else secret

    def _encrypt(self, data: bytes) -> bytes:
        """AES-ECB 加密"""
        key = self._secret[:16].ljust(16, b'\0')
        cipher = AES.new(key, AES.MODE_ECB)
        return cipher.encrypt(data)

    def sign(self, data: str) -> str:
        """
        生成签名
        data: 请求参数拼接字符串
        """
        # Step 1: SHA256
        h = hashlib.sha256(data.encode()).digest()
        # Step 2: 用 secret 的前16字节作为密钥 AES 加密
        encrypted = self._encrypt(h)
        # Step 3: Base64
        return base64.b64encode(encrypted).decode()


class XiaomiAPI:
    """
    小米 IoT 云端 API 客户端

    API 文档: https://iot.mi.com/api
    """

    def __init__(
        self,
        app_key: str = "",
        app_secret: str = "",
        access_token: str = "",
        user_id: str = "",
        api_base: str = "https://api.io.mi.com/app",
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.user_id = user_id
        self.api_base = api_base.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Android-FFFFFFFFFFFFFFFF-SDK-31-27-28-28-xiaomi%20MI%204-5.0-API-21",
            "Accept-Encoding": "identity",
        })

    def _sign_request(self, params: Dict) -> str:
        """对请求参数进行签名"""
        chip = XiaomiSecurityChip(self.app_secret)
        # 按 key 排序后拼接
        sorted_params = sorted(params.items())
        data = "&".join(f"{k}={v}" for k, v in sorted_params)
        return chip.sign(data)

    def _build_cookie(self, nonce: Optional[str] = None) -> str:
        """
        构建请求 Cookie
        包含签名信息
        """
        if nonce is None:
            nonce = self._generate_nonce()
        current = int(time.time())
        signed = self._sign_request({
            "appId": self.app_key,
            "nonce": nonce,
            "timestamp": str(current),
            "accessToken": self.access_token,
        })
        return f"1;{signed};{nonce};{current}"

    def _generate_nonce(self) -> str:
        """生成随机 nonce (16字节)"""
        import random
        return "".join(f"{random.randint(0, 255):02x}" for _ in range(16))

    def _post(self, path: str, data: Dict, signed: bool = True) -> Dict:
        """
        发送 POST 请求

        Args:
            path: API 路径，如 /home/device_list
            data: 请求数据
            signed: 是否使用安全芯片签名
        """
        url = f"{self.api_base}{path}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        payload = data.copy()

        if signed:
            cookie = self._build_cookie()
            nonce = cookie.split(";")[2]
            timestamp = cookie.split(";")[3]
            signed_val = cookie.split(";")[1]

            payload.update({
                "appId": self.app_key,
                "nonce": nonce,
                "signature": signed_val,
                "timestamp": int(timestamp),
                "accessToken": self.access_token,
            })

        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") != 0:
                logger.warning(f"API 返回错误: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            return {"code": -1, "message": str(e)}

    # ─────────────────────────────────────────
    # 设备管理
    # ─────────────────────────────────────────

    def list_devices(self) -> List[Dict]:
        """获取设备列表"""
        result = self._post("/v2/home/device_list", {
            "uid": self.user_id,
            "limit": 200,
            "page": 1,
        })
        if result.get("code") == 0:
            return result.get("result", {}).get("list", [])
        return []

    def get_device_info(self, did: str) -> Dict:
        """获取单个设备信息"""
        result = self._post("/home/device", {
            "did": did,
            "uid": self.user_id,
        })
        return result.get("result", {})

    def get_device_status(self, did: str) -> Dict:
        """
        获取设备状态 (MIoT-Spec-V2)
        通过 properties/get 接口获取属性
        """
        result = self._post("/miotspecv2/property/get", {
            "did": did,
            "params": ["*"],  # * 表示所有属性
            "type": "query",
        })
        if result.get("code") == 0:
            return result.get("result", {})
        return result

    def get_properties(self, did: str, siids: List[int], piids: List[int]) -> List[Dict]:
        """
        获取指定 SIID/PIID 的属性值

        Args:
            did: 设备 DID
            siids: SIID 列表
            piids: 对应 PIID 列表 (与 siids 长度相同)
        """
        params = []
        for siid, piid in zip(siids, piids):
            params.append({"siid": siid, "piid": piid})

        result = self._post("/miotspecv2/property/get", {
            "did": did,
            "params": params,
            "type": "query",
        })
        if result.get("code") == 0:
            return result.get("result", {}).get("values", [])
        return []

    # ─────────────────────────────────────────
    # 设备控制
    # ─────────────────────────────────────────

    def control_device(self, did: str, controls: List[Dict]) -> Dict:
        """
        控制设备 (MIoT-Spec-V2)

        Args:
            did: 设备 DID
            controls: 控制参数列表
                [{"siid": 2, "piid": 1, "value": True}, ...]

        Returns:
            {"code": 0, "result": {...}}
        """
        result = self._post("/miotspecv2/property/set", {
            "did": did,
            "params": controls,
            "type": "set",
        })
        return result

    def send_action(self, did: str, siid: int, aiid: int, args: Dict = None) -> Dict:
        """
        发送动作 (MIoT-Spec-V2 action)

        Args:
            did: 设备 DID
            siid: Service Instance ID
            aiid: Action ID
            args: 动作参数
        """
        result = self._post("/miotspecv2/action/execute", {
            "did": did,
            "siid": siid,
            "aiid": aiid,
            "args": args or {},
        })
        return result

    # ─────────────────────────────────────────
    # 场景 / 自动化
    # ─────────────────────────────────────────

    def list_scenes(self) -> List[Dict]:
        """获取场景列表"""
        result = self._post("/scene/list", {
            "type": 0,  # 0=手动场景, 1=自动场景
        })
        if result.get("code") == 0:
            return result.get("result", {}).get("list", [])
        return []

    def execute_scene(self, scene_id: str) -> Dict:
        """
        执行场景

        Args:
            scene_id: 场景 ID 或名称
        """
        result = self._post("/scene/trigger", {
            "sceneId": scene_id,
        })
        return result

    # ─────────────────────────────────────────
    # Token 管理
    # ─────────────────────────────────────────

    def refresh_token(self, refresh_token: str) -> Dict:
        """刷新 Access Token"""
        result = self._post("/user/tokenRefresh", {
            "refreshToken": refresh_token,
        }, signed=False)
        return result

    def verify_token(self) -> bool:
        """验证 Token 是否有效"""
        result = self._post("/user/tokenVerify", {
            "accessToken": self.access_token,
        })
        return result.get("code") == 0


# ─────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────

if __name__ == "__main__":
    # 简单测试
    import sys
    from pathlib import Path

    config_path = Path.home() / ".qclaw" / "skills" / "xiaomi-home-config.yaml"
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config.yaml"

    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        xiaomi_cfg = config.get("xiaomi", {})
        cloud_cfg = config.get("cloud", {})
        api = XiaomiAPI(
            app_key=xiaomi_cfg.get("app_key", ""),
            app_secret=xiaomi_cfg.get("app_secret", ""),
            access_token=xiaomi_cfg.get("access_token", ""),
            user_id=xiaomi_cfg.get("user_id", ""),
            api_base=cloud_cfg.get("api_base", "https://api.io.mi.com/app"),
        )
        print("Token 验证:", api.verify_token())
        print("设备数量:", len(api.list_devices()))
    else:
        print(f"[ERROR] 配置文件不存在: {config_path}")
        sys.exit(1)
