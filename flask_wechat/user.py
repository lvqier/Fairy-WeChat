#!/usr/bin/env python

from .api import UserApi


class UserClient(object):
    def __init__(self, openid, access_token):
        self.openid = openid
        self.access_token = access_token
        self.user_api = UserApi(openid, access_token)

    def get_userinfo(self):
        return self.user_api.get_user_info()
