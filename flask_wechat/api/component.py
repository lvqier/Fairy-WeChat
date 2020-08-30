#!/usr/bin/env python

from urllib import parse

from .base import BaseApi
from .common import WeChatMessage, WeChatEncryptError
from .enc import WXBizMsgCrypt


class ComponentAppApi(BaseApi):
    def __init__(self, appid, secret, token, enc_key):
        self.appid = appid
        self.secret = secret
        self.msg_crypt = WXBizMsgCrypt(token, enc_key, appid)

    def token_post(self, url, access_token, data=None, params=None):
        data = {} if data is None else data
        params = {} if params is None else params
        data['component_appid'] = self.appid
        params['component_access_token'] = access_token
        response = self.post(url, params=params, data=data)
        return response

    def callback(self, message, timestamp, nonce, signature):
        ret, decrypted_xml = self.msg_crypt.DecryptMsg(message, signature, timestamp, nonce)
        if not ret == 0:
            print('>>>', message, timestamp, nonce, signature, ret)
            raise WeChatEncryptError(ret)
        return WeChatMessage(decrypted_xml)

    def get_access_token(self, verify_ticket):
        data = {
            'component_appid': self.appid,
            'component_appsecret': self.secret,
            'component_verify_ticket': verify_ticket
        }
        return self.post('https://api.weixin.qq.com/cgi-bin/component/api_component_token', data=data)

    def create_pre_auth_code(self, access_token):
        return self.token_post('https://api.weixin.qq.com/cgi-bin/component/api_create_preauthcode', access_token)

    def get_app_authorize_url(self, pre_auth_code, auth_type, redirect_uri, biz_appid=None, state=None):
        url = 'https://mp.weixin.qq.com/cgi-bin/componentloginpage'
        params = {
            'component_appid': self.appid,
            'pre_auth_code': pre_auth_code,
            'redirect_uri': redirect_uri,
            'auth_type': auth_type,
        }

        if state:
            params.update({'state': state})

        if biz_appid:
            params['biz_appid'] = biz_appid
            params.pop('auth_type')
        query_string = parse.urlencode(params)
        return '{}?{}'.format(url, query_string)

    def query_auth(self, access_token, authorization_code):
        data = {
            'authorization_code': authorization_code
        }
        return self.token_post('https://api.weixin.qq.com/cgi-bin/component/api_query_auth', access_token, data=data)

    def refresh_authorizer_token(self, access_token, authorizer_appid, authorizer_refresh_token):
        data = {
            'authorizer_appid': authorizer_appid,
            'authorizer_refresh_token': authorizer_refresh_token
        }
        return self.token_post('https://api.weixin.qq.com/cgi-bin/component/api_authorizer_token', access_token, data=data)

    def get_authorizer_info(self, access_token, authorizer_appid):
        data = {
            'authorizer_appid': authorizer_appid
        }
        return self.token_post('https://api.weixin.qq.com/cgi-bin/component/api_get_authorizer_info', access_token, data=data)

    def set_authorizer_option(self, access_token, authorizer_appid, option_name, option_value):
        data = {
            'authorizer_appid': authorizer_appid,
            'option_name': option_name,
            'option_value': option_value
        }
        return self.token_post('https://api.weixin.qq.com/cgi-bin/component/api_set_authorizer_option', access_token, data=data)

    def get_authorizer_option(self, access_token, authorizer_appid, option_name):
        data = {
            'authorizer_appid': authorizer_appid,
            'option_name': option_name
        }
        return self.token_post('https://api.weixin.qq.com/cgi-bin/component/api_get_authorizer_option', access_token, data=data)

    def jscode2session(self, access_token, appid, js_code, grant_type='authorization_code'):
        params = {
            'appid': appid,
            'js_code': js_code,
            'grant_type': grant_type,
            'component_appid': self.appid,
            'component_access_token': access_token
        }
        return self.post('https://api.weixin.qq.com/sns/component/jscode2session', params=params, content_type='application/json')

    def get_user_authorize_url(self, appid, redirect_uri, scope, state, response_type='code'):
        params = {
            'component_appid': self.appid,
            'appid': appid,
            'redirect_uri': redirect_uri,
            'response_type': response_type,
            'scope': scope,
            'state': state
        }
        query_string = parse.urlencode(params)
        return 'https://open.weixin.qq.com/connect/oauth2/authorize?{}'.format(query_string)

    def get_user_access_token(self, access_token, appid, code, grant_type='authorization_code'):
        params = {
            'component_appid': self.appid,
            'component_access_token': access_token,
            'appid': appid,
            'code': code,
            'grant_type': grant_type
        }
        return self.get('https://api.weixin.qq.com/sns/oauth2/component/access_token', params=params)

    def user_refresh_token(self, access_token, appid, refresh_token, grant_type='refresh_token'):
        params = {
            'component_appid': self.appid,
            'component_access_token': access_token,
            'appid': appid,
            'grant_type': grant_type,
            'refresh_token': refresh_token
        }
        return self.get('https://api.weixin.qq.com/sns/oauth2/component/refresh_token', params=params)

    def get_draft_templates(self, access_token):
        url = 'https://api.weixin.qq.com/wxa/gettemplatedraftlist'
        params = {'access_token': access_token}
        return self.post(url, params=params)

    def add_template(self, access_token, draft_id):
        url = 'https://api.weixin.qq.com/wxa/addtotemplate'
        params = {'access_token': access_token}
        data = {'draft_id': draft_id}
        return self.post(url, params=params, data=data)

    def get_templates(self, access_token):
        url = 'https://api.weixin.qq.com/wxa/gettemplatelist'
        params = {'access_token': access_token}
        return self.post(url, params=params)
