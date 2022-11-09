from aiohttp import web             # Viết và gọi API
import socket                       # Lấy MAC và IP
import aiohttp_cors                 # Thay đổi quyền truy cập khi client gọi API
import routeros_api                 # Gọi API từ Router Mikrotik
import re                           # RegEx - lọc chuỗi
import logging                      # Tạo log

ROUTER = '192.168.89.1'
USERNAME = 'wifiapi'
PASSWORD = 'wifilogin'

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
        return web.HTTPAccepted(text="Login thành công")
    except Exception as ex:
        # err = str(ex)
        err = identifyError(str(ex))
        logging.error(err)
        return web.HTTPNonAuthoritativeInformation(text=str(err))


def identifyError(err: str) -> str:
    """Xác định nguyên nhân gây lỗi khi đăng nhập không thành công

    Args:
        err (str): Thông báo lỗi được truyền vào

    Returns:
        str: Trả về nguyên nhân gây lỗi
    """
    errList = [
        {
            "reason": ".invalid username or password.*",
            "notify": "Sai username hoặc password"
        },
        {
            "reason": ".unknown host IP .*",
            "notify": "Địa chỉ IP không tồn tại"
        },
        {
            "reason": ".invalid value for argument ip.*",
            "notify": "Địa chỉ IP không hợp lệ"
        },
        {
            "reason": ".wrong MAC provided.*",
            "notify": "Sai địa chỉ MAC"
        },
        {
            "reason": ".invalid value of mac-address, mac address required.*",
            "notify": "Địa chỉ MAC không hợp lệ"
        }
    ]
    for i in errList:
        if (re.search(i['reason'], err)):
            return i['notify']
        else:
            return "Lỗi không xác định"

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/ip', getIP),
                web.post('/login', loginHotspot)])

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
