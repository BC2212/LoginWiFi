from aiohttp import web
import socket
import aiohttp_cors
import routeros_api
import re

def connectToRouter():
    global routerAPI
    connection = routeros_api.RouterOsApiPool(
    host='192.168.89.1',
    username='wifiapi',
    password='wifilogin',
    plaintext_login=True)
    routerAPI = connection.get_api()

async def handle(request):
    text = "Hello, mình là Quỳnh"
    return web.Response(text=text)

async def getip(request):
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return web.Response(text=ip)

async def login_user_hotspot(request):
    try:
        global routerAPI
        print("\n\n\nĐã nhận được yêu cầu. Đang xử lý...")
        dataRequest = await request.json()
        username = dataRequest["user"]
        password = dataRequest["password"]
        mac = dataRequest["mac-address"]
        ip = dataRequest["ip"]

        print("User: {username}\nIP: {ip}\nMAC: {mac}\nPasswd: {passwd}".format(username=username, ip=ip, mac=mac, passwd=password))
        print("Đang login vào router")
        login = routerAPI.get_resource('/ip/hotspot/active')
        params = {
            'user': str(username),
            'password': str(password),
            'mac-address': str(mac),
            'ip': str(ip),
        }
        login.call('login', params)
        print("Login thành công\n\n\n")
        return web.HTTPAccepted(text="Login thành công")
    except Exception as ex:
        # err = identifyError(str(ex).split("\"")[1])
        # print(ex)
        err = identifyError(str(ex))
        return web.HTTPNonAuthoritativeInformation(text=str(err))

def identifyError(err: str):
    if (re.search(".unknown host IP .*", err)):
        return "Địa chỉ IP không tồn tại."

def addCorsToServer(app: web.Application):
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)


def login_wifi_app():
    try:
        global app
        connectToRouter()
        app = web.Application()
        app.add_routes([web.get('/', handle),
                    web.get('/ip', getip),
                    web.post('/login', login_user_hotspot)])
        addCorsToServer(app)
        web.run_app(app,port=8000)
    except Exception as ex:
        print(ex)

app = web.Application()
app.add_routes([web.get('/', handle),
            web.get('/ip', getip),
            web.post('/login', login_user_hotspot)])

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

for route in list(app.router.routes()):
    cors.add(route)

connectToRouter()

if __name__ == '__main__':
    # login_wifi_app()
    web.run_app(app, port=8000)