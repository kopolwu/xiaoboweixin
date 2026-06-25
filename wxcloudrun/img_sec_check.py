"""
图片内容安全检测 - 调用微信 imgSecCheck API（HTTP 版本）
通过 access_token 调用微信开放平台接口，检测图片是否含有违规内容
"""
import base64
import os
import time
import requests

# 模块级 access_token 缓存
_token_cache = {
    'token': None,
    'expires_at': 0,
}


def _get_access_token() -> str:
    """
    获取微信 access_token，使用内存缓存避免频繁请求
    默认提前 5 分钟刷新，确保不会用过期的 token
    """
    now = time.time()
    if _token_cache['token'] and _token_cache['expires_at'] > now + 60:
        return _token_cache['token']

    appid = os.environ.get('WX_APPID', '')
    secret = os.environ.get('WX_APPSECRET', '')

    if not appid or not secret:
        raise Exception('云托管未配置 WX_APPID / WX_APPSECRET 环境变量')

    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
    resp = requests.get(url, timeout=10)
    data = resp.json()

    if 'access_token' not in data:
        raise Exception('获取 access_token 失败: {}'.format(data))

    _token_cache['token'] = data['access_token']
    _token_cache['expires_at'] = now + data.get('expires_in', 7200) - 300
    return _token_cache['token']


def img_sec_check(img_base64: str) -> dict:
    """
    调用微信图片内容安全检测 API

    Args:
        img_base64: 图片的 base64 编码字符串（已压缩至 750×1334 以内）

    Returns:
        dict: 微信 API 原始响应
              {'errcode': 0, 'errmsg': 'ok'} — 内容安全
              {'errcode': 87014, 'errmsg': '...'} — 内容违规
    """
    try:
        access_token = _get_access_token()
    except Exception as e:
        return {'errcode': -1, 'errmsg': str(e)}

    # 将 base64 解码为二进制
    try:
        img_bytes = base64.b64decode(img_base64)
    except Exception:
        return {'errcode': -1, 'errmsg': '图片 base64 解码失败'}

    url = f'https://api.weixin.qq.com/wxa/img_sec_check?access_token={access_token}'

    try:
        resp = requests.post(
            url,
            files={'media': ('image.jpg', img_bytes, 'image/jpeg')},
            timeout=15,
        )
        return resp.json()
    except requests.exceptions.Timeout:
        return {'errcode': -1, 'errmsg': '检测接口超时'}
    except requests.exceptions.ConnectionError:
        return {'errcode': -1, 'errmsg': '检测接口网络异常'}
    except Exception as e:
        return {'errcode': -1, 'errmsg': str(e)}
