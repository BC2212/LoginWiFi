from typing import Any, List, Dict
import routeros_api                 # Gọi API từ Router Mikrotik
from .model.UserHotspot import UserHotspot

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

    def login(self, user: UserHotspot) -> bool:
        """Thành viên đăng nhập vào router Mikrotik để sử dụng Internet

        Args:
            user (UserHotspot): Tham số truyền vào phải là object của UserHotspot. Trong đó phải có địa chỉ MAC, địa chỉ IP, username, password của thành viên

        Returns:
            bool: Trả về True nếu đăng nhập thành công
        Raises:
            Exception nếu gặp lỗi
        """
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
            return True
        except Exception as ex:
            raise ex

    def createHotspotUser(self, user:'UserHotspot') -> bool:
        """Tạo tài khoản trên router Mikrotik

        Args:
            user (UserHotspot): Tham số truyền vào

        Returns:
            bool: Trả về True nếu tạo thành công
        """
        try:
            init = self.api.get_resource('ip/hotspot/user')
            params = {
                'name': user.username,
                'password': user.password,
                'profile': user.profile
            }
            init.call('add', params)
            return True
        except Exception as ex:
            raise ex

    def getHotspotUserList(self) -> List[Dict]:
        """Lấy danh sách tài khoản trên router Mikrotik

        Returns:
            List[Dict]: Trả về danh sách tài khoản
        """
        try:
            api = self.api.get_resource('ip/hotspot/user')
            userList = api.call('print')
            return userList
        except Exception as ex:
            raise ex

    def getHotspotUserID(self, username:str) -> str:
        """Lấy ID của tài khoản trên router Mikrotik

        Args:
            username (str): Tên đăng nhập của tài khoản trên router Mikrotik

        Returns:
            str: Trả về ID của tài khoản dưới dạng chuỗi
        """
        try:
            userList = self.getHotspotUserList()
            for user in userList:
                if user['name'] == username:
                    return user['id']
            raise Exception('User did not exist')
        except Exception as ex:
            raise ex

    def removeHotspotUser(self, username:str) -> bool:
        """Xoá tài khoản trên router Mikrotik

        Args:
            username (str): Tên đăng nhập của tài khoản trên router Mikrotik

        Returns:
            bool: Trả về True nếu xoá tài khoản thành công
        """
        try:
            id = self.getHotspotUserID(username=username)
            remove = self.api.get_resource('ip/hotspot/user')
            params = {
                'numbers': id
            }
            print(remove.call('remove', params))
        except Exception as ex:
            raise ex

    def editHotspotUser(self, user: UserHotspot) -> bool:
        """Chỉnh sửa tài khoản của thành viên trên router Mikrotik

        Args:
            user (UserHotspot): Dữ liệu truyền vào

        Returns:
            bool: Trả về True nếu chỉnh sửa thành công
        """
        try:
            id = self.getHotspotUserID(username=user.username)
            edit = self.api.get_resource('ip/hotspot/user')
            params = {
                'numbers': id,
                'profile': user.profile,
                'name': user.username,
                'password': user.password
            }
            edit.call('set', params)
            return True
        except Exception as ex:
            raise ex