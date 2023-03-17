class LRequest:
    def __init__(self, url=None, contentType="application/json", accept="application/json") -> None:
        self.url = url
        self.contentType = contentType
        self.accept = accept
        self.headers = {
            'accept': self.accept,
            'content-type': self.contentType
        }