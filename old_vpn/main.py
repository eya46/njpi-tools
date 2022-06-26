import os
from typing import Optional

from httpx import post, get
from lxml import etree

local = os.path.dirname(__file__)
cookie_path = os.path.join(local, "cookie.txt")


def _cookie_get() -> str:
    try:
        with open(cookie_path, 'r') as f:
            return f.read()
    except Exception as e:
        return ""


def _cookie_save(_):
    with open(cookie_path, 'w') as f:
        f.write(_)


def get_proxy_cookie(account: str, password: str) -> Optional[str]:
    _cookie = _cookie_get()
    try:
        try:
            if _cookie == "":
                raise Exception
            post(
                "http://210-28-10-180-8988-p.vpn.njpi.edu.cn:8118/web/Common/Tsm.html",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Cookie": _cookie
                }, timeout=2
            )
            return _cookie
        except:
            pass
        web = get(
            "http://uia-njpi-edu-cn-s.vpn.njpi.edu.cn:8118/login?service=https://vpn.njpi.edu.cn:4433/auth"
            "/cas_validate?entry_id=1",
            timeout=2
        )
        
        execution = etree.HTML(web.text).xpath(
            "/html/body/div/div[2]/div[2]/div[2]/div[2]/div/div/div/div/form/div[2]/div[2]/input[2]"
        )[0].get("value")
        
        data = {
            "lt": "",
            "execution": execution,
            "_eventId": "submit",
            "customerCode": "1_52",
            "accountTypeCode": "1_01",
            "username": account,
            "password": password,
            "captchaCode": "",
            "rememberMe": "true"
        }
        
        _cookie = post(
            "https://uia.njpi.edu.cn/login",
            data=data,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/99.0.4844.84 Safari/537.36 "
            }, timeout=2
        ).request.headers.get("Cookie")
        print("vpn Cookie更新 -> " + _cookie)
        _cookie_save(_cookie)
        return _cookie
    except:
        return None
