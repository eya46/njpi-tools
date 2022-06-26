import os
import traceback
from typing import Optional

import httpx
from lxml import etree
from urllib.parse import urlparse

local = os.path.dirname(__file__)
cookie_path = os.path.join(local, "cookie.txt")


def url_to_proxy(url: str) -> str:
    _ = urlparse(url)
    _url = "http://{0}{1}{2}.atrust.njpi.edu.cn:443{3}{4}".format(
        _.hostname.replace(".", "-"),
        (f"{_.port}-p" if _.port else ""),
        ("-s" if _.scheme == "https" else ""),
        (_.path if _.path else "/"),
        (f"?{_.query}" if _.query else "")
    )
    
    return _url


def _cookie_save(_):
    with open(cookie_path, 'w') as f:
        f.write(_)


def _cookie_get():
    try:
        with open(cookie_path, 'r') as f:
            return f.read()
    except Exception as e:
        return ""


def get_proxy_cookie(account: str, password: str) -> Optional[str]:
    _cookie = _cookie_get()
    try:
        if _cookie == "":
            raise Exception
        pre_web = httpx.get(
            "https://at.njpi.edu.cn/portal/service_center.html#/app_center",
            headers={
                "Cookie": _cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" +
                              " (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
            }, timeout=2, verify=False, follow_redirects=False
        )
        if pre_web.status_code != 200:
            raise Exception
        print("vpn Cookie 有效")
        return _cookie
    except:
        pass
    try:
        with httpx.Client(verify=False) as r:
            web = r.get(
                "http://uia-njpi-edu-cn-s.atrust.njpi.edu.cn:443/login?service=" + \
                "https://at.njpi.edu.cn:443/passport/v1/auth/cas"
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
            
            resp1 = r.post(
                "http://uia-njpi-edu-cn-s.atrust.njpi.edu.cn:443/login?service="
                "https://at.njpi.edu.cn:443/passport/v1/auth/cas",
                params=data,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" +
                                  " (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
                }, timeout=2, follow_redirects=False
            )
            
            r.get(
                resp1.headers["Location"],
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
                                  "(KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
                }, timeout=2, follow_redirects=True
            )
            
            _cookie = "; ".join(f"{i[0]}={i[1]}" for i in r.cookies.items())
            print("vpn Cookie更新 -> " + _cookie)
            _cookie_save(_cookie)
            return _cookie
    except:
        print(traceback.format_exc())
        return None


if __name__ == '__main__':
    a = get_proxy_cookie("", "")
    print(a)
