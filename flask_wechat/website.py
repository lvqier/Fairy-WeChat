#!/usr/bin/env python

from flask import redirect

from .app import SecretAppClient


class WeChatAuthError(Exception):
    def __init__(self):
        pass


class WebsiteAppClient(SecretAppClient):
    def init_app(self, app, cache=None):
        appid = app.config['WECHAT_WEBSITE_APPID']
        secret = app.config['WECHAT_WEBSITE_SECRET']
        super(WebsiteAppClient, self).init_app(app, appid, secret, cache=cache)

    def authorize(self, redirect_uri, state, scope='snsapi_login'):
        redirect_url = self.app_api.get_oauth2_qrconnect_url(redirect_uri, scope, state)
        return redirect(redirect_url)
