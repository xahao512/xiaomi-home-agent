#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成小米 OAuth2.0 登录二维码
"""

import qrcode
import os
import sys

# OAuth2.0 配置
OAUTH2_CLIENT_ID = '2882303761517852428'
OAUTH2_REDIRECT_URL = 'https://home.mi.com/ha_callback'
OAUTH2_AUTHORIZE_URL = 'https://account.xiaomi.com/oauth2/authorize'

def generate_qr():
    import secrets
    state = secrets.token_urlsafe(32)
    
    from urllib.parse import urlencode
    params = {
        'client_id': OAUTH2_CLIENT_ID,
        'redirect_uri': OAUTH2_REDIRECT_URL,
        'response_type': 'code',
        'scope': '1 3 6000 16001',
        'state': state,
        'skip_confirm': 'false',
        'url': 'https://home.mi.com/ha_login',
    }
    
    auth_url = f"{OAUTH2_AUTHORIZE_URL}?{urlencode(params)}"
    
    # 生成二维码
    qr = qrcode.QRCode(version=5, box_size=10, border=4)
    qr.add_data(auth_url)
    qr.make(fit=True)
    
    # 保存图片
    config_dir = os.path.dirname(os.path.abspath(__file__))
    qr_file = os.path.join(config_dir, '..', 'config', 'oauth_qr.png')
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_file)
    
    print(f"✅ 二维码已生成: {qr_file}")
    print(f"\n📱 请使用微信扫描上方的二维码图片")
    print(f"\n🔗 或直接访问链接:")
    print(auth_url)
    
    # 显示 ASCII 二维码
    print("\n" + "="*60)
    qr.print_ascii(invert=True)
    print("="*60)
    
    return qr_file, auth_url, state

if __name__ == '__main__':
    generate_qr()
