import socket                       # Lấy MAC và IP
import logging

from aiohttp import web             # Viết và gọi API
from .APIException import APIException
from .model.UserHotspot import UserHotspot
from .RouterMikrotik import RouterMikrotik

# Format định dạng cơ bản của Log
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%y-%m-%d %H:%M:%S', level=logging.DEBUG)

class Wifi:
    def __init__(self, router: 'RouterMikrotik') -> None:
        self.router = router

    async def getHomepage(self, request):
        text = "Đây là homepage clb mạng LHU-CISCO"
        return web.HTTPOk(text=text)

    async def getIP(self, request):
        """Lấy địa chỉ IP

        Args:
            request (_type_): HTTP Request

        Returns:
            Response: Trả về địa chỉ IP qua HTTP Response
        """
        # Lấy tên thiết bị
        try:
            hostname = socket.gethostname()
            # Lấy địa chỉ IP thông qua tên thiết bị
            ip = socket.gethostbyname(hostname)
            return web.Response(text=ip)
        except Exception as ex:
            return web.HTTPError()

    async def loginHotspot(self, request):
        """Đăng nhập vào router để client có thể kết nối mạng

        Args:
            request (_type_): HTTP Request

        Returns:
            _type_: Trả về kết quả đăng nhập thành công hay không.
                    Nếu không trả về lỗi.
        """
        try:
            print('----------------------')
            logging.info("Đã nhận được yêu cầu. Đang xử lý...")

            # Trích xuất dữ liệu của request từ json thành dict
            dataRequest = await request.json()
            # Tách dữ liệu thành các biến
            user = UserHotspot(
                ip=dataRequest["ip"],
                mac=dataRequest["mac-address"],
                username=dataRequest["user"],
                password=dataRequest["password"]
            )

            logging.info(f"Yêu cầu được gửi bởi người dùng tên {user.username} có địa chỉ IP là {user.ip}")

            self.router.login(user=user)

            # Thông báo nếu đăng nhập thành công
            logging.info('Login thành công!')
            return web.HTTPOk(text="Login thành công")
        except Exception as ex:
            # Kiểm tra lý do gây lỗi
            err = APIException.identify(str(ex))
            logging.error(err)
            return web.HTTPInternalServerError(text=str(err))