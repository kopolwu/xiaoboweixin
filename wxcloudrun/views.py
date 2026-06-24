from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.doubao_proxy import parse_doubao_url


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


# ==================== 豆包视频去水印代理 ====================

import re


@app.route('/api/doubao/parse', methods=['POST'])
def doubao_parse():
    """
    解析豆包视频分享链接
    请求体: {"url": "https://..."}
    返回: 上游 API 的原始响应
    """
    params = request.get_json()

    if not params or 'url' not in params:
        return make_err_response('缺少url参数')

    video_url = params['url'].strip()
    if not video_url:
        return make_err_response('url不能为空')

    # 校验 URL 格式
    url_regex = r'(https?://)?[a-zA-Z0-9-]+(\.[a-zA-Z0-9.-]+)+/[\w\-./#?%&=:]+'
    if not re.match(url_regex, video_url):
        return make_err_response('链接格式不正确')

    # 调用代理解析
    result = parse_doubao_url(video_url)

    # 直接返回上游 API 的完整响应给小程序端处理
    from flask import Response
    import json
    return Response(json.dumps(result), mimetype='application/json')
