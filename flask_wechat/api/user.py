#!/usr/bin/env python

from .base import BaseApi


class UserApi(BaseApi):
    def __init__(self, openid, access_token):
        self.openid = openid
        self.access_token = access_token

    def get_user_info(self, lang='zh_CN'):
        params = {
            'openid': self.openid,
            'access_token': self.access_token,
            'lang': lang
        }
        return self.get('https://api.weixin.qq.com/sns/userinfo', params=params)
