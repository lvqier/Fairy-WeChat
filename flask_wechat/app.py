#!/usr/bin/env python

from abc import ABC, abstractmethod
from urllib import parse

from flask import request, redirect

from .api import SecretAppApi, AuthorizedAppApi


class BaseAppClient(ABC):
    @property
    @abstractmethod
    def access_token(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def app_api(self):
        raise NotImplementedError()

    def authorize(self, redirect_uri, state, scope='snsapi_userinfo'):
        redirect_url = self.app_api.get_oauth2_authorize_url(redirect_uri, scope, state)
        return redirect(redirect_url)

    def authorized_response(self):
        # state = request.args['state']
        if 'code' not in request.args:
            from flask_wechat.website import WeChatAuthError
            raise WeChatAuthError()

        authorization_code = request.args['code']
        return self.app_api.query_auth(authorization_code)

    def refresh_token(self, refresh_token):
        return self.app_api.refresh_token(refresh_token)

    def check_auth(self, openid, access_token):
        return self.app_api.check_auth(openid, access_token)

    def get_userinfo(self, openid, access_token):
        return self.app_api.get_user_info(openid, access_token)

    def jscode2session(self, js_code):
        return self.app_api.jscode2session(js_code)

    def decrypt_data(self, encrypt_data, key=None, iv=None):
        """
        解密小程序消息
        """
        return self.app_api.decrypt_data(encrypt_data, key=key, iv=iv)

    def send_weapp_message(self, touser, template_id, page, form_id, data, emphasis_keyword):
        """
        发送小程序模板消息
        https://developers.weixin.qq.com/miniprogram/dev/api/sendUniformMessage.html
        https://developers.weixin.qq.com/miniprogram/dev/api/sendTemplateMessage.html
        """
        weapp_template_msg = {
            'template_id': template_id,
            'page': page,
            'form_id': form_id,
            'data': data,
            'emphasis_keyword': emphasis_keyword
        }
        return self.app_api.send_uniform_message(self.access_token, touser, weapp_template_msg=weapp_template_msg)

    def send_mp_message(self, touser, template_id, appid, url, miniprogram, data):
        """
        发送公众号模板消息
        """
        mp_template_msg = {
            'appid': appid,
            'url': url,
            'miniprogram': miniprogram,
            'data': data
        }
        return self.app_api.send_uniform_message(self.access_token, touser, mp_template_msg=mp_template_msg)

    def get_wxa_code(self, path, params=None, width=None, auto_color=False, line_color=None, is_hyaline=False):
        """
        生成小程序码
        https://developers.weixin.qq.com/miniprogram/dev/api/getWXACode.html
        """
        if not auto_color:
            line_color = None
        if params is not None:
            path = '{}?{}'.format(path, parse.urlencode(params))
        response = self.app_api.get_wxa_code(self.access_token, path, width=width, auto_color=auto_color, line_color=line_color, is_hyaline=is_hyaline)
        return response.content

    def create_wxa_qrcode(self, path, params=None, width=None):
        """
        生成小程序二维码
        https://developers.weixin.qq.com/miniprogram/dev/api/createWXAQRCode.html
        """
        if params is not None:
            path = '{}?{}'.format(path, parse.urlencode(params))
        response = self.app_api.create_wxa_qrcode(self.access_token, path, width=width)
        return response.content


class SecretAppClient(BaseAppClient):
    def __init__(self, app=None):
        self.appid = None
        self.secret_secret_api = None
        self.cache = None
        self.flask_app = None
        self.cache_key_prefix = None
        if app:
            self.init_app(app)

    def init_app(self, app, appid=None, secret=None, cache=None):
        self.appid = appid
        self.cache = cache
        self.secret_app_api = SecretAppApi(appid, secret)

        self.cache_key_prefix = 'wechat_{}'.format(self.appid)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        wechat = app.extensions.get('wechat', {})
        wechat['app'] = self
        app.extensions['wechat'] = wechat
        self.flask_app = app

    @property
    def access_token(self):
        cache_key = '{}_access_token'.format(self.cache_key_prefix)
        access_token = self.cache.get(cache_key)
        if access_token is None:
            result = self.app_api.get_access_token()
            access_token = result['access_token']
            expires_in = result['expires_in']
            self.cache.set(cache_key, access_token, timeout=expires_in)
        return access_token

    @property
    def app_api(self):
        return self.secret_app_api


class AuthorizedAppClient(BaseAppClient):
    def __init__(self, appid, access_token, component_app_client):
        self.appid = appid
        self._access_token = access_token
        self.authorized_app_api = AuthorizedAppApi(appid, access_token, component_app_client)

    @property
    def access_token(self):
        return self._access_token

    @property
    def app_api(self):
        return self.authorized_app_api

    def open_create(self):
        return self.app_api.open_create()

    def open_bind(self, open_appid):
        return self.app_api.open_bind(open_appid)

    def open_unbind(self, open_appid):
        return self.app_api.open_unbind(open_appid)

    def open_get(self):
        response = self.app_api.open_get()
        return response

    def modify_domain_use_set(self, request_domain, ws_request_domain, upload_domain, download_domain):
        response = self.app_api.modify_domain_use_set(
            request_domain, ws_request_domain, upload_domain, download_domain
        )
        return response

    def get_industry(self):
        response = self.app_api.get_industry()
        return response

    def get_all_private_template(self):
        response = self.app_api.get_all_private_template()
        return response

    def get_template_library_list(self):
        response = self.app_api.get_template_library_list()
        return response

    def get_template_library_keywords_by_id(self, template_library_id):
        response = self.app_api.get_template_library_keywords_by_id(template_library_id)
        return response

    def add_template_with_keywords(self, template_library_id, keywords):
        """
        :param template_library_id:   模板库ID
        :param keywords:    # 关键字ID列表
        :return: template_id
        """
        response = self.app_api.add_template_with_keywords(template_library_id, keywords)
        return response.get('template_id')

    def del_template(self, template_id):
        response = self.app_api.del_template(template_id)
        return response

    def get_template_list(self):
        response = self.app_api.get_template_list()
        return response
