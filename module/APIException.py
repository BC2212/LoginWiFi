import re

class APIException:
    exList = [
        {
            "errStr": ".invalid username or password.*",
            "reason": "Sai username hoặc password"
        },
        {
            "errStr": ".unknown host IP.*",
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
            "errStr": ".invalid value of mac-address.*",
            "reason": "Địa chỉ MAC không hợp lệ"
        },
        {
            "errStr": ".target machine actively refused it.*",
            "reason": "Sai hostname hoặc địa chỉ IP của router"
        },
        {
            "errStr": "'Data'",
            "reason": "Token invalid"
        }
    ]

    @staticmethod
    def list():
        return APIException.exList

    @staticmethod
    def identify(err: str) -> str:
        """Xác định nguyên nhân gây lỗi khi đăng nhập không thành công

        Args:
            err (str): Thông báo lỗi được truyền vào

        Returns:
            str: Trả về nguyên nhân gây lỗi
        """

        for e in APIException.exList:
            if (re.search(e['errStr'], err)):
                return e['reason']
        return "Lỗi không xác định"