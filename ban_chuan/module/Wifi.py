import socket                       # Lấy MAC và IP
import logging                      # Hiển thị thông báo trên Terminal
import aiohttp
import json
import copy
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
        text = 'Đây là homepage clb mạng LHU-CISCO'
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
            logging.info('Đã nhận được yêu cầu. Đang xử lý...')

            # Trích xuất dữ liệu của request từ json thành dict
            dataRequest = await request.json()
            # Tách dữ liệu thành các biến
            user = UserHotspot(
                ip=dataRequest['IP'],
                mac=dataRequest['Mac-Address'],
                username=dataRequest['Username'],
                password=dataRequest['Password']
            )

            logging.info(
                f'Yêu cầu được gửi bởi người dùng tên {user.username} có địa chỉ IP là {user.ip}')

            self.router.login(user=user)

            # Thông báo nếu đăng nhập thành công
            logging.info('Login thành công!')
            return web.HTTPOk(text='Login thành công')
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
        request = LRequest(
            url='https://tapi.lhu.edu.vn/nema/auth/CLB_Select_AllThanhVien')
        result = dict()

        async with aiohttp.ClientSession() as session:
            async with session.get(url=request.url) as response:
                requestData = await response.json()
                listUsers = copy.copy(requestData['data'])
                count = len(listUsers)
                # Tạm tạo thêm username bằng mssv
                # Sau khi anh Lực thêm cột username vào database sẽ xoá đoạn này
                for user in listUsers:
                    user['Username'] = user['MSSV']
                    hoten = user.pop('HoTen')
                    try:
                        user['Ho'] = hoten[:hoten.rindex(' ')]
                        user['Ten'] = hoten[hoten.rindex(' ')+1:]
                    except:
                        user['Ho'] = None
                        user['Ten'] = None

                result['SoLuongThanhVien'] = count
                result['DanhSachThanhVien'] = listUsers

        return web.HTTPOk(body=json.dumps(result), content_type='application/json')

    async def getTotalNumberOfMembers(self, request) -> 'web.HTTPException':
        """Lấy tổng số lượng thành viên hiện tại

        Args:
            request (_type_): HTTP Request

        Returns:
            web.HTTPException: Trả về tổng số lượng thành viên hiện tại
        """
        request = LRequest(
            url='https://tapi.lhu.edu.vn/nema/auth/CLB_Select_AllThanhVien')

        async with aiohttp.ClientSession() as session:
            async with session.get(url=request.url) as response:
                requestData = await response.json()
                listUsers = requestData['data']
                count = len(listUsers)

        return web.HTTPOk(text=str(count))

    async def getLoggonListByDate(self, request) -> 'web.HTTPException':
        """Lấy danh sách các thành viên đã đăng nhập theo ngày

        Args:
            request (_type_): HTTP Request. Date có format là yyyy-MM-dd

        Returns:
            web.HTTPException: Trả về danh sách các thành viên đã đăng nhập, có check đi trễ
        """

        if request.method == 'GET':
            date = str(request.match_info['date'])
        else:
            requestData = await request.json()
            date = requestData['Date']

        request = LRequest(
            url='https://tapi.lhu.edu.vn/nema/auth/CLB_DiemDanh_Select_byDate',
        )

        lateTime = datetime.strptime('18:30:00', '%H:%M:%S').time()
        checkinTime = datetime.strptime('18:00:00', '%H:%M:%S').time()

        async with aiohttp.ClientSession() as session:
            async with session.post(url=request.url, json={'Date': date}) as response:
                requestData = await response.json()
                users = requestData['data']
                result = dict()
                countLate = 0

                for user in users[:]:
                    _date = user.pop('ThoiGian')
                    date = _date.split('T')[0]
                    user['Ngay'] = date

                    _time = user.pop('ThoiGianDiemDanh')
                    loggonTime = datetime.strptime(_time, '%H:%M:%S').time()
                    user['Gio'] = str(loggonTime)

                    if loggonTime < checkinTime:
                        users.remove(user)
                        continue
                    elif loggonTime > lateTime:
                        user['DiTre'] = True
                        countLate += 1
                    else:
                        user['DiTre'] = False

                result['SoLuongCoMat'] = len(users)
                result['SoLuongTre'] = countLate
                result['DanhSachCoMat'] = users
        return web.HTTPOk(body=json.dumps(result), content_type='application/json')

    async def getHotspotUserList(self, request) -> 'web.HTTPException':
        """Lấy danh sách tài khoản của thành viên trên router Mikrotik

        Args:
            request (_type_): HTTP Request

        Returns:
            web.HTTPException: Trả về HTTP Response danh sách các tài khoản trên router Mikrotik
        """
        try:
            list = self.router.getHotspotUserList()
            return web.HTTPOk(text=json.dumps(list))
        except Exception as ex:
            return web.HTTPInternalServerError(text=str(ex))

    async def addMember(self, request) -> 'web.HTTPException':
        """Gồm 2 phần:
                1. Tạo thành viên trong database
                2. Tạo tài khoản trên router Mikrotik

        Args:
            request (_type_): HTTP Request với dữ liệu dưới dạng:
                {
                    'Username': '111222333',
                    'MSSV': '111222333',
                    'Ho': 'Nguyễn Văn',
                    'Ten': 'A',
                    'NgaySinh': '2000-01-22',
                    'Lop': '22CT111',
                    'Email': 'nguyenvana@gmail.com',
                    'DienThoai': '0987654321'
                }

        Returns:
            web.HTTPException: Nếu tạo thành công, trả về kết quả tạo thành công. Nếu tạo không thành công, trả về lỗi
        """
        try:
            dataRequest = await request.json()
            user = UserHotspot(
                username=dataRequest['Username'],
                profile='student',
                mssv=dataRequest['MSSV'],
                ho=dataRequest['Ho'],
                ten=dataRequest['Ten'],
                ngaysinh=dataRequest['NgaySinh'],
                lop=dataRequest['Lop'],
                email=dataRequest['Email'],
                sdt=dataRequest['DienThoai'],
                password='1'
            )

            data = {
                'MSSV': user.mssv,
                'HoSV': user.ho,
                'TenSV': user.ten,
                'NgaySinh': user.ngaysinh,
                'Lop': user.lop,
                'Email': user.email,
                'DienThoai': user.sdt
            }

            request = LRequest(
                url='https://tapi.lhu.edu.vn/nema/auth/CLB_ThanhVien_Insert')

            async with aiohttp.ClientSession() as session:
                async with session.post(url=request.url, json=data) as response:
                    result = await response.json()

            # self.router.createHotspotUser(user=user)
            return web.HTTPOk(text=str(result))
        except Exception as ex:
            return web.HTTPInternalServerError(text=str(ex))

    async def getHotspotUserID(self, request) -> 'web.HTTPException':
        """Lấy ID của tài khoản trên router Mikrotik

        Args:
            request (_type_): HTTP Request với dữ liệu dưới dạng:
                {
                    'Username': '111222333'
                }

        Returns:
            web.HTTPException: Trả về UserID của tài khoản
        """
        try:
            dataRequest = await request.json()
            id = self.router.getHotspotUserID(username=dataRequest['Username'])
            return web.HTTPOk(text=id)
        except Exception as ex:
            return web.HTTPInternalServerError(text=str(ex))

    async def removeHotspotUser(self, request) -> 'web.HTTPException':
        """Xoá tài khoản của thành viên trên router Mikrotik

        Args:
            request (_type_): HTTP Request truyền dữ liệu đầu vào dưới dạng:
                {
                    'Username': '111222333'
                }

        Returns:
            web.HTTPException: Nếu xoá thành công, trả về thông báo xoá thành công. Nếu không thành công, trả về lỗi
        """
        try:
            dataRequest = await request.json()
            self.router.removeHotspotUser(username=dataRequest['Username'])
            return web.HTTPOk(text='Remove completed')
        except Exception as ex:
            print(ex)
            return web.HTTPInternalServerError(text='User did not exist')

    async def createHotspotUser(self, request) -> 'web.HTTPException':
        """Tạo tài khoản của user trên router Mikrotik

        Args:
            request (_type_): Truyền dữ liệu đầu vào dưới dạng:
                {
                    'Username': '111222333'
                }

        Returns:
            web.HTTPException: Nếu tạo thành công, trả về thông báo tạo thành công. Nếu không thành công, trả về lỗi
        """
        try:
            dataRequest = await request.json()
            user = UserHotspot(username=dataRequest['Username'])
            self.router.createHotspotUser(user=user)
            return web.HTTPOk(text='User created')
        except Exception as ex:
            return web.HTTPInternalServerError(text='User exists')

    async def editHotspotUser(self, request) -> 'web.HTTPException':
        try:
            dataRequest = await request.json()
            user = UserHotspot(
                username=dataRequest['Username'],
                profile=dataRequest['Profile'],
                mssv=dataRequest['MSSV'],
                ho=dataRequest['Ho'],
                ten=dataRequest['Ten'],
                ngaysinh=dataRequest['NgaySinh'],
                lop=dataRequest['Lop'],
                email=dataRequest['Email'],
                sdt=dataRequest['DienThoai']
            )

            self.router.editHotspotUser(user=user)
            return web.HTTPOk(text='Edit successful')
        except Exception as ex:
            return web.HTTPInternalServerError(text=str(ex))

    async def changePassword(self, request):
        try:
            dataRequest = await request.json()
            user = UserHotspot(
                username=dataRequest['Username'],
                password=dataRequest['Password']
            )

            self.router.editHotspotUser(user=user)
            return web.HTTPOk(text='Change password successful')
        except Exception as ex:
            return web.HTTPInternalServerError(text=str(ex))

    async def changeUsername(self, request):
        try:
            dataRequest = await request.json()
            user = UserHotspot(
                username=dataRequest['Username']
            )

            self.router.editHotspotUser(user=user)
            return web.HTTPOk(text='Change username successful')
        except Exception as ex:
            return web.HTTPInternalServerError(text=str(ex))

    async def getMemberInfo(self, request) -> 'web.HTTPException':
        try:
            dataRequest = await request.json()
            request = LRequest(
                url="https://tapi.lhu.edu.vn/nema/auth/CLB_Select_ThanhVien_byMSSV"
            )
            async with aiohttp.ClientSession() as session:
                async with session.post(url=request.url, json={'MSSV': dataRequest['mssv']}) as response:
                    responseData = await response.json()
                    member = copy.copy(responseData['data'][0])
                    hoten = member.pop('HoTen')
                    member['Ho'] = hoten[:hoten.rindex(' ')]
                    member['Ten'] = hoten[hoten.rindex(' ')+1:]
            return web.HTTPOk(body=json.dumps(member), content_type='application/json')
        except Exception as ex:
            try:
                return web.HTTPInternalServerError(text=responseData['Message'])
            except:
                return web.HTTPInternalServerError(text='Member was deleted')

    async def removeMember(self, request) -> 'web.HTTPException':
        try:
            dataRequest = await request.json()
            request = LRequest(
                url="https://tapi.lhu.edu.vn/nema/auth/CLB_ThanhVien_Delete"
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url=request.url, json={'UserID': dataRequest['UserID']}) as response:
                    responseData = await response.json()
                    result = responseData['data']

            self.router.removeHotspotUser(username=dataRequest['Username'])
            return web.HTTPOk(text='Member deleted') 
        except Exception as ex:
            return web.HTTPInternalServerError(text='Member not found')

    async def editMember(self, request) -> 'web.HTTPException':
        try:
            dataRequest = await request.json()
            user = UserHotspot(
                username=dataRequest['Username'],
                mssv=dataRequest['MSSV'],
            )
        except:
            pass