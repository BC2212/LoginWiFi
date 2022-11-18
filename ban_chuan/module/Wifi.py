import socket                       # Lấy MAC và IP
import logging                      # Hiển thị thông báo trên Terminal
import aiohttp
import json
from datetime import datetime

from aiohttp import web             # Viết và gọi API
from .APIException import APIException
from .model.UserHotspot import UserHotspot
from .RouterMikrotik import RouterMikrotik
from .LHURequest import LRequest

# Format định dạng cơ bản của Log
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%y-%m-%d %H:%M:%S', level=logging.DEBUG)


class Wifi:
    def __init__(self, router: 'RouterMikrotik') -> None:
        self.router = router

    async def getHomepage(self, request) -> 'web.HTTPException':
        text = "Đây là homepage clb mạng LHU-CISCO"
        return web.HTTPOk(text=text)

    async def getIP(self, request) -> 'web.HTTPException':
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

    async def loginHotspot(self, request) -> 'web.HTTPException':
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

            logging.info(
                f"Yêu cầu được gửi bởi người dùng tên {user.username} có địa chỉ IP là {user.ip}")

            self.router.login(user=user)

            # Thông báo nếu đăng nhập thành công
            logging.info('Login thành công!')
            return web.HTTPOk(text="Login thành công")
        except Exception as ex:
            # Kiểm tra lý do gây lỗi
            err = APIException.identify(str(ex))
            logging.error(err)
            return web.HTTPInternalServerError(text=str(err))

    async def getMemberList(self, request) -> 'web.HTTPException':
        """Lấy danh sách thành viên hiện tại của câu lạc bộ

        Args:
            request (_type_): HTTP Request

        Returns:
            web.HTTPException: Trả về số lượng, danh sách các thành viên hiện tại
        """
        request = LRequest(url="https://tapi.lhu.edu.vn/nema/auth/CLB_Select_AllThanhVien")
        result = dict()

        async with aiohttp.ClientSession() as session:
            async with session.get(url=request.url) as response:
                requestData = await response.json()
                listUsers = requestData['data']
                count = len(listUsers)

                result['SoLuongThanhVien'] = count
                result['DanhSachThanhVien'] = listUsers

        return web.HTTPOk(body=json.dumps(result), content_type="application/json")

    async def getTotalNumberOfMembers(self, request) -> 'web.HTTPException':
        """Lấy tổng số lượng thành viên hiện tại

        Args:
            request (_type_): HTTP Request

        Returns:
            web.HTTPException: Trả về tổng số lượng thành viên hiện tại
        """
        request = LRequest(url="https://tapi.lhu.edu.vn/nema/auth/CLB_Select_AllThanhVien")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url=request.url) as response:
                requestData = await response.json()
                listUsers = requestData["data"]
                count = len(listUsers)
        
        return web.HTTPOk(text=str(count))

    async def getLoggonListByDate(self, request) -> 'web.HTTPException':
        """Lấy danh sách các thành viên đã đăng nhập theo ngày

        Args:
            request (_type_): HTTP Request. Date có format là HH:mm:ss

        Returns:
            web.HTTPException: Trả về danh sách các thành viên đã đăng nhập, có check đi trễ
        """

        if request.method == "GET":
            date = str(request.match_info['date'])
        else:
            requestData = await request.json()
            date = requestData['Date']

        request = LRequest(
            url="https://tapi.lhu.edu.vn/nema/auth/CLB_DiemDanh_Select_byDate",
        )

        keyTime = datetime.strptime('18:30:00', '%H:%M:%S').time()

        async with aiohttp.ClientSession() as session:
            async with session.post(url=request.url, json={'Date': date}) as response:
                requestData = await response.json()
                users = requestData['data']
                result = dict()
                result['SoLuongCoMat'] = len(users)
                countLate = 0

                for user in users:
                    _date = user.pop("ThoiGian")
                    date = _date.split("T")[0]
                    user['Ngay'] = date

                    _time = user.pop("ThoiGianDiemDanh")
                    loggonTime = datetime.strptime(_time, '%H:%M:%S').time()
                    user['Gio'] = str(loggonTime)

                    if loggonTime > keyTime:
                        user['DiTre'] = True
                        countLate += 1
                    else:
                        user['DiTre'] = False

                result['SoLuongTre'] = countLate
                result['DanhSachCoMat'] = users
        return web.HTTPOk(body=json.dumps(result), content_type="application/json")
