# LoginWiFi
## Project backend hỗ trợ đăng nhập qua hệ thống WiFi

Đây là project được thực hiện bởi thành viên câu lạc bộ mạng trường Đại học Lạc Hồng

## Tính năng

- Đăng nhập vào hệ thống WiFi Mikrotik
- Thống kê danh sách thành viên có mặt, trễ, vắng

## Yêu cầu

Project có thể hoạt động trên các hệ điều hành Windows, Unix có cài đặt[ Python3](https://www.python.org/downloads/).
Cần sử dụng cài đặt các module sau:
- [Aiohttp](https://docs.aiohttp.org/en/stable/) - Package dùng để dựng server
- [Aiohttp_cors](https://github.com/aio-libs/aiohttp-cors) - Kiểm soát truy cập tài nguyên
- [RouterOS-api](https://pypi.org/project/RouterOS-api/) - API kết nối đến router Mikrotik

## Cài đặt

LoginWifi yêu cầu [Python3](https://www.python.org/downloads/).

Cài đặt các package cần thiết qua file requirements.txt.

```sh
cd LoginWiFi
pip install -r requirements.txt -y
```