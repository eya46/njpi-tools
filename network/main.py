from typing import Union, Dict

import httpx
import json


def login(
        account: Union[str, int], password: str,
        callback: str = "data"
) -> Union[str, Dict[str, str]]:
    params = {
        "callback": callback,  # 返回值的函数名称
        "login_method": "1",
        "user_account": f",0,{account}",  # 要加,0,
        "user_password": password,
        "wlan_user_ip": "",  # 当前的ip,不填好像也没事
        "wlan_user_ipv6": "",
        "wlan_user_mac": "000000000000",  # mac,瞎填好像也没事
        "wlan_ac_ip": "",
        "wlan_ac_name": "",
        "jsVersion": "4.1.3",
        "terminal_type": "1",
        "lang": "zh-cn",
        "v": "9323"
    }
    resp = httpx.get("http://172.16.2.6:801/eportal/portal/login", params=params)
    # resp.text # 返回值是js代码
    # 调用的函数名(json值) ["callback"]({})
    # data({"result":1,"msg":"Portal协议认证成功！"});
    try:
        return json.loads(resp.text[len(callback) + 2:-2])
    except:
        return resp.text
