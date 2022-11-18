from aiohttp import web             # Viết và gọi API
import aiohttp_cors                 # Thay đổi quyền truy cập khi client gọi API

import config
from module.RouterMikrotik import RouterMikrotik
from module.Wifi import Wifi

# Khởi tạo object routerAPI và kết nối đến router
routerAPI = RouterMikrotik(
    host=config.ROUTER,
    username=config.USERNAME,
    password=config.PASSWORD
)

# Khởi tạo object wifi với tham số truyền vào là object routerAPI
# Object wifi được dùng để xử lý request từ client
wifi = Wifi(router=routerAPI)

# Khởi tạo webapp
app = web.Application()
app.add_routes([
    web.get('/', wifi.getHomepage),
    web.post('/login', wifi.loginHotspot),
    web.get('/lay-danh-sach-dang-nhap/{date}', wifi.getLoggonListByDate),
    web.post('/lay-danh-sach-dang-nhap', wifi.getLoggonListByDate),
    web.get('/lay-so-luong-thanh-vien', wifi.getTotalNumberOfMembers),
    web.get('/lay-danh-sach-thanh-vien', wifi.getMemberList)
])

# Khởi tạo Cross-Origin Resource Sharing (cors)
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

# Thêm cors vào từng route
for route in list(app.router.routes()):
    cors.add(route)

if __name__ == '__main__':
    web.run_app(app, port=8000)
