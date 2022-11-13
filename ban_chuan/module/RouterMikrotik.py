from typing import Any
import routeros_api                 # Gọi API từ Router Mikrotik
from .model.UserHotspot import UserHotspot
from .APIException import APIException

class RouterMikrotik:
    def __init__(self, host: str, username: str, password: str):
        """Khởi tạo object RouterMikrotik

        Args:
            host (str): Hostname hoặc địa chỉ IP của router
            username (str): Tên đăng nhập vào router
            password (str): Mật khẩu đăng nhập vào router
        """
        self.host = host
        self.username = username
        self.password = password
        self.api = self.connect()

    def connect(self) -> Any:
        """Dùng để kết nối đến Router Mikrotik

        Args:
            host (str): Hostname hoặc địa chỉ IP của router
            username (str): Tài khoản để kết nối đến router
            password (str): Mật khẩu của tài khoản được kết nối đến router
        """
        try:
            # Tạo kết nối đến router với các parameter lấy được khi hàm được gọi
            connection = routeros_api.RouterOsApiPool(
                host=self.host,
                username=self.username,
                password=self.password,
                plaintext_login=True)
            api = connection.get_api()
            return api
        except Exception as ex:
            raise ex

    def login(self, user: UserHotspot):
        try:
            # Lấy resource từ router
            login = self.api.get_resource('/ip/hotspot/active')
            params = {
                'user': str(user.username),
                'password': str(user.password),
                'mac-address': str(user.mac),
                'ip': str(user.ip),
            }

            # Gọi lệnh đăng nhập vào router
            login.call('login', params)
        except Exception as ex:
            raise ex