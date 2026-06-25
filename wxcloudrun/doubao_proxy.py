"""
豆包视频去水印 - API 代理
提供签名逻辑并代理请求到上游 API
"""

import hashlib
import json
import random
import string
import time
import requests
from urllib.parse import quote

API_HOST = 'https://qsy.lmengcity.com'
API_PATH = '/mp-6/watermark/dy/v2/'


def _md5(text: str) -> str:
    """计算 MD5 哈希值（小写十六进制）"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def _generate_nonce_str(length: int = 16) -> str:
    """生成指定长度的随机字符串"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def _build_signed_body(target_url: str, url_text: str = None) -> dict:
    """构建签名后的请求体"""
    nonce_str = _generate_nonce_str()
    timestamp = int(time.time())
    sign_str = f'nonceStr={nonce_str}&timestamp={timestamp}&url={quote(target_url, safe="")}'
    sign = _md5(sign_str)

    return {
        'timestamp': timestamp,
        'url': target_url,
        'openid': '',
        'url_text': url_text or target_url,
        'nonceStr': nonce_str,
        'sign': sign,
    }


def parse_doubao_url(video_url: str) -> dict:
    """
    解析豆包视频分享链接，获取无水印视频/图片

    Args:
        video_url: 豆包分享链接

    Returns:
        dict: {
            'code': 0/1 成功, -1 失败,
            'msg': 错误信息,
            'body': { ... }  # 上游返回的视频信息
        }
    """
    try:
        post_data = _build_signed_body(video_url, video_url)

        body = json.dumps(post_data).encode('utf-8')
        response = requests.post(
            API_HOST + API_PATH,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': '',
                'Accept-Encoding': 'identity',
            },
            timeout=30,
            allow_redirects=False,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        return {'code': -1, 'msg': '请求超时，请稍后重试'}
    except requests.exceptions.ConnectionError:
        return {'code': -1, 'msg': '网络连接失败，请检查网络'}
    except requests.exceptions.RequestException as e:
        return {'code': -1, 'msg': f'请求失败: {str(e)}'}
    except ValueError:
        return {'code': -1, 'msg': '解析响应失败'}
    except Exception as e:
        return {'code': -1, 'msg': f'未知错误: {str(e)}'}
