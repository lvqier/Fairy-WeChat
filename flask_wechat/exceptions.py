

class WechatException(Exception):
    def __init__(self, code, message, **params):
        self.code = code
        self.message = message

        if params:
            self.message = message.format(**params)

    def __repr__(self):
        return '<%s:%s>' % (self.code, self.message)
