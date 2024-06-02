import pandas as pd

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

    def get_user_info(self):
        return user_info_map.get(self.user_id, {})

    def get_user_name(self):
        return self.get_user_info().get("name", "")

    def get_user_age(self):
        return self.get_user_info().get("age", 0)
