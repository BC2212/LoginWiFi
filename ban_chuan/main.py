from aiohttp import web             # Viết và gọi API
import socket                       # Lấy MAC và IP
import aiohttp_cors                 # Thay đổi quyền truy cập khi client gọi API
import logging                      # Tạo log
from module.APIException import APIException
from module.RouterMikrotik import RouterMikrotik
from module.model.UserHotspot import UserHotspot

ROUTER = '192.168.89.1'
USERNAME = 'wifiapi'
PASSWORD = 'wifilogin'

routerAPI = RouterMikrotik(host=ROUTER, username=USERNAME, password=PASSWORD)

# Format định dạng cơ bản của Log
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%y-%m-%d %H:%M:%S', level=logging.DEBUG)

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
        user = UserHotspot(
            ip=dataRequest["ip"],
            mac=dataRequest["mac-address"],
            username=dataRequest["user"],
            password=dataRequest["password"]
        )
        routerAPI.login(user=user)

        # Thông báo nếu đăng nhập thành công
        logging.info('Login thành công!')
        return web.HTTPOk(text="Login thành công")
    except Exception as ex:
        # Kiểm tra lý do gây lỗi
        err = APIException.identify(str(ex))
        logging.error(err)
        return web.HTTPInternalServerError(text=str(err))


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

if __name__ == '__main__':
    web.run_app(app, port=8080)