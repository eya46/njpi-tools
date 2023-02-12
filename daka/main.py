import hashlib
import base64
import random
from typing import Union, Optional, Tuple
from io import BytesIO

import httpx

from lxml.etree import HTML
from PIL import Image, ImageFile
from PIL.PngImagePlugin import PngImageFile

url_main = "https://xgyyx.njpi.edu.cn/"

url_index = url_main + "student/index"

url_img = url_main + "student/website/verify/image"

url_img_result = url_img + "/result"

url_login = url_main + "student/website/login"

url_last_info = url_main + "student/content/student/temp/zzdk/lastone"

url_last_dm = url_main + "student/content/tabledata/student/temp/zzdk"

url_last_info_by_dm = url_main + "student/content/student/temp/zzdk/"

url_send_daka = url_main + "student/content/student/temp/zzdk"

url_send_token = url_main + "student/wap/menu/student/temp/zzdk/_child_/edit"

time_out = httpx.Timeout(4.0)

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, "
                  "like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
}


def md5(passwd: str) -> str:
    temp = hashlib.md5()
    temp.update(str(passwd).encode())
    temp = temp.hexdigest()
    return temp[:5] + 'a' + temp[5:9] + 'b' + temp[9:-2]


def b64_to_img(data: str) -> ImageFile:
    return Image.open(BytesIO(base64.b64decode(data)))


def check_rgb(img: ImageFile, x_start: int = 0, y_start: int = 0, rgb=(192, 192, 192)) -> Tuple[int, int]:
    assert isinstance(img, PngImageFile), "只支持png格式"
    gap_1, gap_2 = (0, 0)
    for y in range(y_start, img.size[1]):
        for x in range(x_start, img.size[0]):
            if img.getpixel((x, y)) == rgb:
                if not gap_1:
                    gap_1 = x
                else:
                    gap_2 = x
        if gap_1 and gap_2:
            break
    return gap_1, gap_2


def deal_img(data: httpx.Response) -> dict:
    _data = data.json()
    img = b64_to_img(_data["SrcImage"])
    x1, x2 = check_rgb(img, y_start=_data["YPosition"] + 10)
    salt = random.randint(-3, 3)
    move_x = x1 - (x2 - x1) / 2 + salt + random.random()
    return {
        "moveEnd_X": str(move_x),
        "wbili": "0.9333333333333333"
    }


async def login(r: httpx.AsyncClient, account: str, password: str, to_md5: bool = True) -> Union[bool, str]:
    try:
        _index = await r.get(
            url_index,
            headers=headers,
            timeout=time_out
        )

        _img_data = await r.get(
            url_img,
            headers=headers,
            timeout=time_out
        )

        _img_check = await r.post(
            url_img_result,
            headers={"X-Requested-With": "XMLHttpRequest", **headers},
            timeout=time_out,
            data=deal_img(_img_data)
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


async def get_last_dm(r: httpx.AsyncClient, length=1) -> Tuple[bool, str]:
    try:
        res = await r.get(url_last_dm, params={
            "bSortable_0": False,
            "bSortable_1": True,
            "iSortingCols": "1",
            "iDisplayStart": "0",
            "iDisplayLength": str(length),
            "iSortCol_0": "1",
            "sSortDir_0": "desc"
        }, headers=headers, timeout=time_out)
        data = res.json()
        if data.get("iTotalRecords", 0) == 0 or len(data.get("aaData", [])) == 0:
            return False, "该用户从未打过卡"
        return True, data["aaData"][0]["DM"]
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False, "获取上次打卡代码超时"
    except IndexError:
        return False, "索引上次打卡代码失败"
    except Exception as e:
        return False, "获取上次打卡代码失败"


async def get_last_info_by_dm(r: httpx.AsyncClient, dm: str) -> Tuple[bool, Union[str, dict]]:
    try:
        res = await r.get(url_last_info_by_dm + dm, headers=headers, timeout=time_out)
        return True, res.json()

    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False, "获取上次打卡信息超时"
    except Exception as e:
        return False, "获取上次打卡信息失败"


async def last_info(r: httpx.AsyncClient) -> Union[bool, dict]:
    try:
        _res = await r.get(
            url_last_info, headers=headers,
            timeout=time_out
        )
        return _res.json()
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return False
    except:
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

    # xgym_true_dm = "2" if data.get("xgym", "2") is None else data.get("xgym", "2")

    try:
        try:
            _jzdValue = data["jzdSheng"]["dm"] + (
                "," + _d if (_d := (data.get("jzdShi") or {}).get("dm", None)) else "") + (
                            "," + _d if (_d := (data.get("jzdXian") or {}).get("dm", None)) else "")
        except:
            return "省份获取失败"
        _temp = {
            'dkdz': data.get("dkd", "") + data.get("jzdDz", ""),
            'dkdzZb': "!dkdzZb",
            'dkly': 'baidu',
            'xcmTjd': '',
            'zzdk_token': "!zzdk_token",
            'dkd': "!dkd",
            'jzdValue': _jzdValue,
            'jzdSheng.dm': '!jzdSheng.dm',
            'jzdShi.dm': '!jzdShi.dm',
            'jzdXian.dm': '!jzdXian.dm',
            'jzdDz': '!jzdDz',
            'jzdDz2': '!jzdDz2',
            'lxdh': '!lxdh',
            'sfzx': '!sfzx',
            'sfzxText': '不在校' if data.get("sfzx") != "1" else "在校",
            'twM.dm': '!twM.dm',
            'twMText': '!twM.mc',
            'yczk.dm': '!yczk.dm',
            'yczkText': '!yczk.mc',
            'xgym': '!xgym',
            'xgymText': '已接种已完成',
            'bz': '!bz',
            'operationType': 'Create',
            'dm': '',
            'tw1M.dm': '',
            'tw2M.dm': '',
            'tw3M.dm': '',
            'brStzk.dm': '!brStzk.dm',
            'brJccry.dm': '!brJccry.dm',
            'jrStzk.dm': '!jrStzk.dm',
            'jrJccry.dm': '!jrJccry.dm',
            'jkm': data.get("jkm") or "1",
            'xcm': data.get("xcm") or "1",
            'hsjc': '!hsjc',
            'jkmcl': '',
            'zdy1': '!zdy1',
            'zdy2': '!zdy2',
            'zdy3': '!zdy3',
            'zdy4': '!zdy4',
            'zdy5': '!zdy5',
            'zdy6': '!zdy6'
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

        success, the_last_info_dm = await get_last_dm(r)

        if not success:
            return f"打卡失败 -> {the_last_info_dm}"

        success, the_last_info = await get_last_info_by_dm(r, the_last_info_dm)

        if not success:
            return f"打卡失败 -> {the_last_info}"

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
        login_now("2xxxxxxxxx", "abcdefg")
    ))
