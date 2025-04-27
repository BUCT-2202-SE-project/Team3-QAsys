
class ClientError(Exception):
    code = -200


class ClientUrlFormatError(ClientError):
    """
    url格式错误
    """
    code = -201

    def __init__(self, url):
        super().__init__(f"url格式错误: {url}")


class ClientAPIUnsupportedError(ClientError):
    """
    url格式错误
    """
    code = -202

    def __init__(self, url):
        super().__init__(f"不支持如下的第三方模型api: {url}")