from aiohttp import web             # Viết và gọi API
import aiohttp
import socket                       # Lấy MAC và IP
import aiohttp_cors                 # Thay đổi quyền truy cập khi client gọi API
import routeros_api                 # Gọi API từ Router Mikrotik
import re                           # RegEx - lọc chuỗi
import logging                      # Tạo log
from datetime import datetime
import json

ROUTER = '172.16.2.1'
USERNAME = 'wifilogin'
PASSWORD = 'wifiapi'

# Format định dạng cơ bản của Log
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%y-%m-%d %H:%M:%S', level=logging.DEBUG)


def connectToRouter(host: str, username: str, password: str):
    """Dùng để kết nối đến Router Mikrotik

    Args:
        host (str): Hostname hoặc địa chỉ IP của router
        username (str): Tài khoản để kết nối đến router
        password (str): Mật khẩu của tài khoản được kết nối đến router
    """

    # Tạo global var
    global routerAPI
    # Tạo kết nối đến router với các parameter lấy được khi hàm được gọi
    connection = routeros_api.RouterOsApiPool(
        host=host,
        username=username,
        password=password,
        plaintext_login=True)
    # Kết nối
    routerAPI = connection.get_api()


async def handle(request):
    text = "Hello, mình là Quỳnh"
    return web.Response(text=text)


async def getIP(request):
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


async def loginHotspot(request):
    """Đăng nhập vào router để client có thể kết nối mạng

    Args:
        request (_type_): HTTP Request

    Returns:
        _type_: Trả về kết quả đăng nhập thành công hay không.
                Nếu không trả về lỗi.
    """
    try:
        global routerAPI

        print('----------------------')
        logging.info("Đã nhận được yêu cầu. Đang xử lý...")

        # Trích xuất dữ liệu của request từ json thành dict
        dataRequest = await request.json()
        # Tách dữ liệu thành các biến
        username = dataRequest["user"]
        password = dataRequest["password"]
        mac = dataRequest["mac-address"]
        ip = dataRequest["ip"]

        logging.info("User: {username}\tIP: {ip}\tMAC: {mac}".format(
            username=username, ip=ip, mac=mac, passwd=password))
        logging.info("Đang login vào router")

        # Lấy resource từ router
        login = routerAPI.get_resource('/ip/hotspot/active')
        params = {
            'user': str(username),
            'password': str(password),
            'mac-address': str(mac),
            'ip': str(ip),
        }
        # Gọi lệnh đăng nhập vào router
        login.call('login', params)

        logging.info('Login thành công!')
        return web.HTTPOk()
    except Exception as ex:
        # print(ex)
        err = identifyError(str(ex))
        logging.error(err)
        return web.HTTPInternalServerError(text=str(err))


def identifyError(err: str) -> str:
    """Xác định nguyên nhân gây lỗi khi đăng nhập không thành công

    Args:
        err (str): Thông báo lỗi được truyền vào

    Returns:
        str: Trả về nguyên nhân gây lỗi
    """
    errList = [
        {
            "errStr": ".invalid username or password.*",
            "reason": "Sai username hoặc password"
        },
        {
            "errStr": ".unknown host IP .*",
            "reason": "Địa chỉ IP không tồn tại"
        },
        {
            "errStr": ".invalid value for argument ip.*",
            "reason": "Địa chỉ IP không hợp lệ"
        },
        {
            "errStr": ".wrong MAC provided.*",
            "reason": "Sai địa chỉ MAC"
        },
        {
            "errStr": ".invalid value of mac-address, mac address required.*",
            "reason": "Địa chỉ MAC không hợp lệ"
        }
    ]
    
    for i in errList:
        if (re.search(i['errStr'], err)):
            return i['reason']
    return "Lỗi không xác định"

async def getLoggonListByDate(request) -> 'web.HTTPException':
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

    url = "https://tapi.lhu.edu.vn/nema/auth/CLB_DiemDanh_Select_byDate"
    contentType = "application/json"
    accecpt = "application/json"
    headers = {
        'accept': accecpt,
        'content-type': contentType
    }

    keyTime = datetime.strptime('18:30:00', '%H:%M:%S').time()

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, json={'Date': date}) as response:
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

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/ip', getIP),
                web.post('/login', loginHotspot),
                web.get('/lay-danh-sach-dang-nhap/{date}', getLoggonListByDate),
                web.post('/lay-danh-sach-dang-nhap', getLoggonListByDate)])

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

for route in list(app.router.routes()):
    cors.add(route)

connectToRouter(host=ROUTER, username=USERNAME, password=PASSWORD)

if __name__ == '__main__':
    web.run_app(app, port=8000)
