class UserHotspot:
    # def __init__(self, ip='', mac='', username='', password='', profile='default', mssv='', ho='', ten='', ngaysinh='', lop='', email='', sdt='', accountID='') -> None:
    def __init__(self, ip='', mac='', username='', password='', profile='default', **kwargs) -> None:
        self.ip = ip
        self.mac = mac
        self.username = username
        self.password = password
        self.profile = profile
        self.userid = kwargs.get('userid', '')
        self.mssv = kwargs.get('mssv','')
        self.ho = kwargs.get('ho','')
        self.ten = kwargs.get('ten','')
        self.ngaysinh = kwargs.get('ngaysinh','')
        self.lop = kwargs.get('lop','')
        self.email = kwargs.get('email','')
        self.sdt = kwargs.get('sdt','')
        self.accountID = kwargs.get('accountID','')