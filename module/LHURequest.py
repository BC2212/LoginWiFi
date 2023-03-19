class LRequest:
    def __init__(self, url=None, **kwargs) -> None:
        self.url = url
        self.headers = {
            "Accept": kwargs.get('accept','*/*'),
            "Content-Type": kwargs.get('contentType', 'text/plain'),
            "Authorization": kwargs.get('authorization', '')
        }