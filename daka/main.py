import hashlib
from typing import Union, Optional

import httpx
from lxml.etree import HTML

url_main = "https://xgyyx.njpi.edu.cn/"

url_index = url_main + "student/index"

url_login = url_main + "student/website/login"

url_last_info = url_main + "student/content/student/temp/zzdk/lastone"

url_send_daka = url_main + "student/content/student/temp/zzdk"

url_send_token = url_main + "student/wap/menu/student/temp/zzdk/_child_/edit"

time_out = httpx.Timeout(4.0)

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, "
                  "like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
}

xgym_dm = {
    '0': '未接种',
    '1': '已接种未完成',
    '2': '已接种已完成',
    '3': '已接种加强针',
    '4': '未接种加强针',
}

color = {
    "": "",
    "0": "",
    "1": "绿色",
    "2": "黄色",
    "3": "红色"
}

hsjc = {
    "": "",
    "0": "否",
    "1": "是"
}


def md5(passwd: str) -> str:
    temp = hashlib.md5()
    temp.update(str(passwd).encode())
    temp = temp.hexdigest()
    return temp[:5] + 'a' + temp[5:9] + 'b' + temp[9:-2]


async def login(r: httpx.AsyncClient, account: str, password: str, to_md5: bool = True) -> Union[bool, str]:
    try:
        _index = await r.get(
            url_index,
            headers=headers,
            timeout=time_out
        )
        
        _res = await r.post(
            url_login,
            headers=headers,
            params={
                'uname': account,
                'pd_mm': md5(password) if to_md5 else password
            },
            timeout=time_out
        )
        
        try:
            __data = _res.json()
        except:
            return f"登录结果解析失败，codes=[{_index.status_code},{_res.status_code}]"
        
        if __data.get("goto2") is not None:
            return True
        else:
            if (_res := __data.get("msg")) is None:
                return "解析登录失败原因失败"
            else:
                return _res
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False
    except Exception as e:
        return f"登录失败，{e}"


# True登录成功，False超时，str:登录失败:原因
async def login_now(account: str, password: str, *args, **kwargs) -> Union[bool, str]:
    r = httpx.AsyncClient()
    try:
        return await login(r, account, password, *args, **kwargs)
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False
    finally:
        await r.aclose()


async def last_info(r: httpx.AsyncClient) -> Union[bool, dict]:
    try:
        _res = await r.get(
            url_last_info, headers=headers,
            timeout=time_out
        )
        return _res.json()
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False


async def get_token(r: httpx.AsyncClient) -> Optional[str]:
    try:
        resp = await r.get(
            url_send_token
            , headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, "
                              "like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
            }
        )
        return HTML(resp.text).xpath('//*[@id="zzdk_token"]')[0].get("value")
    except:
        return None


async def get_location(address: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient() as r:
            # 原免费接口容易出错，自行前往百度地图申请[ak]
            # https://lbsyun.baidu.com/apiconsole/key#/home
            resp = await r.get(
                "http://api.map.baidu.com/geocoding/v3/",
                params={"address": address, "output": "json", "ak": "********************************"}
            )
            _data = resp.json()["result"]["location"]
            return f"{_data['lng']},{_data['lat']}"
    except:
        return None


def build_form(data: dict) -> Union[dict, str]:
    def _build(key: str) -> str:
        if key.startswith("!"):
            try:
                __temp = data
                for __i in key[1:].split('.'):
                    __temp = __temp[__i]
                return __temp if __temp is not None else ""
            except:
                return ""
        else:
            return key
    
    xgym_true_dm = "2" if data.get("xgym", "2") is None else data.get("xgym", "2")
    
    try:
        try:
            _jzdValue = data["jzdSheng"]["dm"] + (
                "," + _d if (_d := (data.get("jzdShi") or {}).get("dm", None)) else "") + (
                            "," + _d if (_d := (data.get("jzdXian") or {}).get("dm", None)) else "")
        except:
            return "省份获取失败"
        _temp = {
            'dkdz': "!dkdz",
            'dkdzZb': "!dkdzZb",
            'dkly': 'baidu',
            'dkd': "!dkd",
            'zzdk_token': "!zzdk_token",
            'jzdValue': _jzdValue,
            'jzdSheng.dm': '!jzdSheng.dm',
            'jzdShi.dm': '!jzdShi.dm',
            'jzdXian.dm': '!jzdXian.dm',
            'jzdDz': '!jzdDz',
            'jzdDz2': '!jzdDz2',
            'lxdh': '!lxdh',
            'sfzx': '!sfzx',
            'sfzx1': '不在校' if data.get("sfzx") != "1" else "在校",
            'twM.dm': '!twM.dm',
            'tw1': '!twM.mc',
            'tw1M.dm': "",
            'tw11': "",
            'tw2M.dm': "",
            'tw12': "",
            'tw3M.dm': "",
            'tw13': "",
            'yczk.dm': '!yczk.dm',
            'yczk1': '!yczk.mc',
            'fbrq': '!fbrq',
            'jzInd': '!jzInd',
            'jzYy': '!jzYy',
            'zdjg': '!zdjg',
            'fxrq': '!fxrq',
            'brStzk.dm': '!brStzk.dm',
            'brStzk1': '!brStzk.mc',
            'brJccry.dm': '!brJccry.dm',
            'brJccry1': '!brJccry.mc',
            'jrStzk.dm': '!jrStzk.dm',
            'jrStzk1': '!jrStzk.mc',
            'jrJccry.dm': '!jrJccry.dm',
            'jrJccry1': '!jrJccry.mc',
            'jkm': data.get("jkm") or "1",
            'jkm1': color[data.get("jkm") or "1"],
            'xcm': data.get("xcm") or "1",
            'xcm1': color[data.get("xcm") or "1"],
            'xgym': '!xgym',
            'xgym1': xgym_dm[xgym_true_dm],
            'hsjc': '!hsjc',
            'hsjc1': hsjc[data.get("hsjc") or "1"],
            'bz': '!bz',
            'operationType': 'Create',
            'dm': ''
        }
        
        for i in _temp:
            _temp[i] = _build(_temp[i])
        
        return _temp
    except Exception as e:
        return str(e)


async def post_daka(r: httpx.AsyncClient, form: dict) -> str:
    try:
        _res = await r.post(
            url_send_daka,
            headers=headers,
            data=form,
            timeout=time_out
        )
        
        if "重复提交" in _res.text:
            return "打卡失败 -> 今日已打卡"
        elif "非法请求" in _res.text:
            return "打卡失败 -> 提交参数不足或有误"
        elif "message" in _res.text:
            __temp = "打卡失败 -> 预料之外的错误，错误如下:\n"
            for i in _res.json()['errorInfoList']:
                __temp += f"{i['message']}\n"
            return __temp[:-1]
        else:
            return f"打卡成功! -> 地点:{form['dkd']}"
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return "打卡失败 -> 提交打卡超时"
    except:
        return "打卡失败 -> 提交打卡出现未知错误"


async def daka(account: str, password: str, *args, **kwargs) -> str:
    r = httpx.AsyncClient()
    try:
        login_res = await login(r, account, password, *args, **kwargs)
        if isinstance(login_res, str):
            return f"打卡失败 -> {login_res}"
        if isinstance(login_res, bool) and not login_res:
            return f"打卡失败 -> 打卡网站超时"
        
        the_last_info = await last_info(r)
        
        if isinstance(the_last_info, bool):
            return "打卡失败 -> 获取上次打卡信息超时"
        
        form = build_form(the_last_info)
        
        if isinstance(form, str):
            return f"打卡失败 -> 表单构建错误:{form}"
        
        form["zzdk_token"] = await get_token(r)
        # 获取打卡token
        if form["zzdk_token"] is None:
            return "打卡失败 -> 获取打卡token失败"
        if not form:
            return "打卡失败 -> 构建打卡信息失败"
        
        if (dkdz := form.get("dkdz")) is None:
            return "打卡失败 -> 打卡地获取失败"
        else:
            _dkdzZb = await get_location(dkdz)
            if _dkdzZb is None:
                return "打卡失败 -> 经纬度获取失败"
            form["dkdzZb"] = _dkdzZb
        
        return await post_daka(r, form)
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return "打卡失败 -> 打卡网站超时"
    except httpx.ConnectError:
        return "打卡失败 -> 打卡网站连接失败"
    except Exception as e:
        return f"打卡失败 -> 打卡函数未知错误:{e}"
    finally:
        await r.aclose()


if __name__ == '__main__':
    import asyncio
    
    print(asyncio.run(
        daka("2xxxxxxxxx", "abcdefg")
    ))
