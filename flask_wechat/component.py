#!/usr/bin/env python

import traceback

from flask import request, redirect, current_app

from .api import ComponentAppApi
from .app import AuthorizedAppClient
from .exceptions import WechatException


class ComponentAppClient(object):
    """
    Usage:

    >> from some_where import app
    >> from flask_wechat import WeChatComponent
    >> wechat_component = WeChatComponent(app)
    >> # or
    >> wechat_component = WeChatComponent()
    >> wechat_component.init_app(app)
    """
    def __init__(self, app=None):
        self.appid = None
        self.component_app_api = None
        self.cache = None
        self.message_handlers = {}
        if app:
            self.init_app(app)
        self.flask_app = app

    def get_or_create_wechat_app(self):
        pass

    @property
    def verify_ticket(self):
        """
        internal use only
        """
        cache_key = '{}_verify_ticket'.format(self.cache_key_prefix)
        return self.cache.get(cache_key)

    @verify_ticket.setter
    def verify_ticket(self, verify_ticket):
        """
        internal use only
        """
        cache_key = '{}_verify_ticket'.format(self.cache_key_prefix)
        self.cache.set(cache_key, verify_ticket)

    @property
    def access_token(self):
        cache_key = '{}_access_token'.format(self.cache_key_prefix)
        access_token = self.cache.get(cache_key)
        if access_token is None:
            result = self.component_app_api.get_access_token(self.verify_ticket)
            access_token = result['component_access_token']
            expires_in = result['expires_in']
            self.cache.set(cache_key, access_token, timeout=expires_in)

        # print('raw component_access_token: {}'.format(access_token))
        return access_token

    def init_app(self, app, cache=None):
        self.appid = app.config['WECHAT_COMPONENT_APPID']
        secret = app.config['WECHAT_COMPONENT_SECRET']
        token = app.config['WECHAT_COMPONENT_TOKEN']
        encrypt_key = app.config['WECHAT_COMPONENT_ENCRYPT_KEY']

        self.cache = cache

        default_cache_key_prefix = 'wechat_component_{}_'.format(self.appid)
        self.cache_key_prefix = app.config.get('WECHAT_COMPONENT_CACHE_KEY_PREFIX', default_cache_key_prefix)

        self.component_app_api = ComponentAppApi(self.appid, secret, token, encrypt_key)

        @self.message_handler('component_verify_ticket')
        def handle_component_verify_ticket(message):
            self.verify_ticket = message['ComponentVerifyTicket']

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        wechat = app.extensions.get('wechat', {})
        wechat['component'] = self
        app.extensions['wechat'] = wechat
        self.flask_app = app

    def callback(self):
        """
        Usage:

        >> from some_where import app
        >> from some_where import wechat_component
        >>
        >> @app.route('/wechat/open/callback')
        >> def callback_view():
        >>     return wechat_component.callback()
        """
        request_body = request.data.decode('utf-8')
        current_app.logger.info('-'*100)
        current_app.logger.info(request.url)
        current_app.logger.info(request_body)
        timestamp = request.args['timestamp']
        nonce = request.args['nonce']
        msg_signature = request.args['msg_signature']

        message = self.component_app_api.callback(request_body, timestamp, nonce, msg_signature)
        info_type = message['InfoType']

        message_handlers = self.message_handlers.get(info_type, [])
        for message_handler in message_handlers:
            try:
                message_handler(message)
            except Exception as e:
                current_app.logger.exception(e)
                # traceback.print_exc()

        return 'success'

    def message_handler(self, info_type):
        """
        Usage:

        >> from some_where import wechat_component
        >> @wechat_component.message_handler('authorized')
        >> def handl_authorized(wechat_message):
        >>     pass
        info_type: component_verify_ticket, authorized, unauthorized, updateauthorized
        """
        message_handlers = self.message_handlers.get(info_type, [])

        def wrapper(func):
            message_handlers.append(func)
            return func

        self.message_handlers[info_type] = message_handlers
        return wrapper

    def authorize(self, auth_type, redirect_uri, biz_appid=None, **params):
        """
        Usage:

        >> from some_where import wechat_component
        >> @app.route('/wechat/open/authorize')
        >> def authorize_view():
        >>     auth_type = ...
        >>     redirect_uri = ...
        >>     return wechat_component.authorize(auth_type, redirect_uri)
        """
        result = self.component_app_api.create_pre_auth_code(self.access_token)
        if result.get('errcode'):
            code = result.get('errcode')
            message = result.get('errmsg')
            raise WechatException(code, message)

        pre_auth_code = result['pre_auth_code']
        authorize_url = self.component_app_api.get_app_authorize_url(
            pre_auth_code, auth_type,
            redirect_uri, biz_appid=biz_appid
        )
        return redirect(authorize_url)

    def authorized_response(self):
        auth_code = request.args['auth_code']
        result = self.component_app_api.query_auth(self.access_token, auth_code)
        # print(json.dumps(result, indent=4, ensure_ascii=False))
        return result.get('authorization_info')

    def refresh_authorizer_token(self, authorizer_appid, authorizer_refresh_token):
        return self.component_app_api.refresh_authorizer_token(self.access_token, authorizer_appid, authorizer_refresh_token)

    def get_authorizer_info(self, authorizer_appid):
        result = self.component_app_api.get_authorizer_info(self.access_token, authorizer_appid)
        return result['authorizer_info']

    def set_authorizer_option(self, authorizer_appid, option_name, option_value):
        return self.component_app_api.set_authorizer_option(self.access_token, authorizer_appid, option_name, option_value)

    def get_authorizer_option(self, authorizer_appid, option_name):
        return self.component_app_api.get_authorizer_option(self.access_token, authorizer_appid, option_name)

    def create_app_client(self, appid, access_token):
        return AuthorizedAppClient(appid, access_token, self)

    def get_wxapp_draft_templates(self):
        """
        获取小程序模板草稿列表
        :return: 获取小程序模板草稿列表
        """
        result = self.component_app_api.get_draft_templates(self.access_token)
        return result.get('draft_list')

    def get_wxapp_templates(self):
        """
        获取小程序模板列表
        :return: 小程序模板列表
        """
        result = self.component_app_api.get_templates(self.access_token)
        return result.get('template_list')

    def add_wxapp_template(self, draft_template_id):
        """
        添加小程序模板
        :param: 小程序模板草稿ID
        :return: 添加结果
        """
        result = self.component_app_api.add_template(self.access_token, draft_template_id)
        return result

    def jscode2session(self, appid, js_code, grant_type='authorization_code'):
        return self.component_app_api.jscode2session(self.access_token, appid, js_code, grant_type=grant_type)

    def user_authorize(self, appid, redirect_uri, scope, state, response_type='code'):
        authorize_url = self.component_app_api.get_user_authorize_url(appid, redirect_uri, scope, state, response_type=response_type)
        return redirect(authorize_url)

    def user_authorized_response(self, grant_type='authorization_code'):
        appid = request.args['appid']
        code = request.args['code']
        return self.component_app_api.get_user_access_token(self.access_token, appid, code, grant_type=grant_type)

    def user_refresh_token(self, appid, refresh_token):
        return self.component_app_api.user_refresh_token(self.access_token, appid, refresh_token)
