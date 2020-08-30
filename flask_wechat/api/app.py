#!/usr/bin/env python

import json
from urllib import parse

from .base import BaseApi
from .common import WeChatApiError


class BaseAppApi(BaseApi):
    def decrypt_data(self, encrypt_data, key=None, iv=None):
        result = self._aes_decrypt(encrypt_data, key=key, iv=iv)
        result = json.loads(result)
        watermark = result.pop('watermark')
        if not watermark['appid'] == self.appid:
            return WeChatApiError(400, 'appid does not match')
        return result

    def send_uniform_message(self, access_token, touser, weapp_template_msg=None, mp_template_msg=None):
        params = {
            'access_token': access_token
        }
        data = {
            'touser': touser,
        }
        if weapp_template_msg is not None:
            data['weapp_template_msg'] = weapp_template_msg
        elif mp_template_msg is not None:
            data['mp_template_msg'] = mp_template_msg
        else:
            assert False, 'weapp_template_msg 和 mp_template_msg 不能同时为空'

        return self.post('https://api.weixin.qq.com/cgi-bin/message/wxopen/template/uniform_send', params=params, data=data)

    def get_wxa_code(self, access_token, path, width=None, auto_color=False, line_color=None, is_hyaline=False):
        params = {
            'access_token': access_token
        }
        data = {
            'path': path,
            'auto_color': auto_color,
            'is_hyaline': is_hyaline
        }
        if width is not None:
            data['width'] = width
        if not auto_color:
            data['line_color'] = line_color

        return self.post('https://api.weixin.qq.com/wxa/getwxacode', params=params, data=data)

    def create_wxa_qrcode(self, access_token, path, width=None):
        params = {
            'access_token': access_token
        }
        data = {
            'path': path
        }
        if width is not None:
            data['width'] = width

        return self.post('https://api.weixin.qq.com/cgi-bin/wxaapp/createwxaqrcode', params=params, data=data)


class SecretAppApi(BaseAppApi):
    '''独立的公众号、小程序、第三方（网站、移动应用）'''
    def __init__(self, appid, secret):
        self.appid = appid
        self.secret = secret

    def get_access_token(self, grant_type='client_credential'):
        params = {
            'grant_type': grant_type,
            'appid': self.appid,
            'secret': self.secret
        }
        return self.get('https://api.weixin.qq.com/cgi-bin/token', params=params)

    def get_oauth2_authorize_url(self, redirect_uri, scope, state, response_type='code'):
        params = {
            'appid': self.appid,
            'redirect_uri': parse.quote_plus(redirect_uri),
            'response_type': response_type,
            'scope': scope,
            'state': state
        }
        return 'https://open.weixin.qq.com/connect/oauth2/authorize?appid={appid}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scope}&state={state}#wechat_redirect'.format(**params)

    def get_oauth2_qrconnect_url(self, redirect_uri, scope, state, response_type='code'):
        params = {
            'appid': self.appid,
            'redirect_uri': redirect_uri,
            'response_type': response_type,
            'scope': scope,
            'state': state
        }
        query_string = parse.urlencode(params)
        return 'https://open.weixin.qq.com/connect/qrconnect?{}#wechat_redirect'.format(query_string)

    def query_auth(self, code, grant_type='authorization_code'):
        params = {
            'appid': self.appid,
            'secret': self.secret,
            'code': code,
            'grant_type': grant_type
        }
        return self.get('https://api.weixin.qq.com/sns/oauth2/access_token', params=params)

    def jscode2session(self, js_code, grant_type='authorization_code'):
        params = {
            'appid': self.appid,
            'secret': self.secret,
            'js_code': js_code,
            'grant_type': grant_type
        }
        return self.get('https://api.weixin.qq.com/sns/jscode2session', params=params)


class AuthorizedAppApi(BaseAppApi):
    def __init__(self, appid, access_token, component_app_client):
        self.appid = appid
        self.access_token = access_token
        self.component_app_client = component_app_client

    def get_oauth2_authorize_url(self, redirect_uri, scope, state, response_type='code'):
        return self.component_app_client.get_user_authorize_url(self.appid, redirect_uri, scope, state, response_type=response_type)

    def query_auth(self, code, grant_type='authorization_code'):
        return self.component_app_client.get_user_access_token(self.appid, code, grant_type=grant_type)

    def token_post(self, url, params=None, data=None):
        params = {} if params is None else params
        data = {} if data is None else data
        params['access_token'] = self.access_token
        # print('>>>    url: %s' % url)
        # print('>>>   data: %s' % data)
        # print('>>> params: %s' % params)
        result = self.post(url, params=params, data=data)
        # print('>>> result: %s' % result)
        return result

    def token_get(self, url, params=None):
        params = {} if params is None else params
        params.update(access_token=self.access_token)
        result = self.get(url, params)
        return result

    def token_post_with_appid(self, url, params=None, data=None):
        params = {} if params is None else params
        data = {} if data is None else data
        data['appid'] = self.appid
        params['access_token'] = self.access_token
        result = self.post(url, params=params, data=data)
        return result

    def open_create(self):
        return self.token_post_with_appid('https://api.weixin.qq.com/cgi-bin/open/create')

    def open_bind(self, open_appid):
        data = {
            'open_appid': open_appid
        }
        return self.token_post_with_appid('https://api.weixin.qq.com/cgi-bin/open/bind', data=data)

    def open_unbind(self, open_appid):
        data = {
            'open_appid': open_appid
        }
        return self.token_post_with_appid('https://api.weixin.qq.com/cgi-bin/open/unbind', data=data)

    def open_get(self):
        try:
            return self.token_post_with_appid('https://api.weixin.qq.com/cgi-bin/open/get')
        except WeChatApiError as e:
            if e.code == 89002:
                return {
                    'open_appid': None,
                    'errcode': 0,
                    'errmsg': 'ok'
                }
            raise e

    def jscode2session(self, js_code, grant_type='authorization_code'):
        return self.component_app_client.jscode2session(self.appid, js_code, grant_type=grant_type)

    def modify_domain_use_set(self, request_domain, ws_request_domain, upload_domain, download_domain):
        modify_domain_url = 'https://api.weixin.qq.com/wxa/modify_domain'
        data = {
            'action': 'set',
            'requestdomain': request_domain,
            'wsrequestdomain': ws_request_domain,
            'uploaddomain': upload_domain,
            'downloaddomain': download_domain,
        }

        result = self.token_post(modify_domain_url, data=data)
        return result

    def get_industry(self):
        """
        获取服务号设置的行业信息
        """
        get_industry_url = 'https://api.weixin.qq.com/cgi-bin/template/get_industry'
        result = self.token_get(get_industry_url)
        return result

    def get_all_private_template(self):
        """
        获取服务号消息模板列表
        """
        get_all_private_template_url = 'https://api.weixin.qq.com/cgi-bin/template/get_all_private_template'
        result = self.token_get(get_all_private_template_url)
        return result

    def get_template_library_list(self):
        """
        获取小程序模板库标题列表
        """
        get_template_library_list_url = 'https://api.weixin.qq.com/cgi-bin/wxopen/template/library/list'
        offset = 0
        count = 20
        templates = []
        while True:
            data = {'offset': offset, 'count': count}
            result = self.token_post(get_template_library_list_url, data=data)
            curr_list = result.get('list')
            if curr_list:
                templates.append(curr_list)

            if len(curr_list) < count:
                break

            offset += count

        return templates

    def get_template_library_keywords_by_id(self, template_library_id):
        """
        获取指定小程序消息模板标题下关键词库
        """
        get_template_library_keywords_url = 'https://api.weixin.qq.com/cgi-bin/wxopen/template/library/get'
        data = {'id': template_library_id}
        result = self.token_post(get_template_library_keywords_url, data=data)
        return result

    def add_template_with_keywords(self, template_library_id, keyword_id_list):
        """
        添加指定小程序消息模板
        """
        add_template_url = 'https://api.weixin.qq.com/cgi-bin/wxopen/template/add'
        data = {
            'id': template_library_id,
            'keyword_id_list': keyword_id_list
        }
        result = self.token_post(add_template_url, data=data)
        return result

    def del_template(self, template_id):
        """
        删除指定小程序消息模板
        """
        del_template_url = 'https://api.weixin.qq.com/cgi-bin/wxopen/template/del'
        data = {
            'template_id': template_id,
        }
        result = self.token_post(del_template_url, data=data)
        return result

    def get_template_list(self):
        """
        获取小程序消息模板列表
        """
        get_template_list_url = 'https://api.weixin.qq.com/cgi-bin/wxopen/template/list'
        offset = 0
        count = 20
        templates = []
        while True:
            data = {'offset': offset, 'count': count}
            result = self.token_post(get_template_list_url, data=data)
            curr_list = result.get('list')
            if curr_list:
                templates.extend(curr_list)

            if len(curr_list) < count:
                break

            offset += count

        return templates
