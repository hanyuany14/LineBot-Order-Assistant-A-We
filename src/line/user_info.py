user_info_map = {
    "0": {
        "userId": "U8c673b20a160a68f671d0cc94969ba55",
        "name": "阿翰",
        "age": 30,
        "payment_method": "信用卡",
        "address": "台北市文山區莊敬10舍",
    },
}


class UserInfoMapping:
    def __init__(self, user_id: str):
        self.user_id = user_id
        print(f"user_id: {user_id}")
        print(f"type(user_id): {type(user_id)}")

    def get_user_info(self):
        for _, user_info in user_info_map.items():
            if user_info.get("userId") == self.user_id:
                return user_info
        return {}

    def get_user_name(self):
        return self.get_user_info().get("name", "Unknown")

    def get_user_age(self):
        return self.get_user_info().get("age", 18)

    def get_payment_method(self):
        return self.get_user_info().get("payment_method", "貨到付款")

    def get_address(self):
        return self.get_user_info().get("address", "來店取貨")
