import asyncio
import json
import time
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Tuple, Callable, Awaitable
from urllib.parse import urlparse

from playwright.async_api import Browser, Playwright, async_playwright, Page, BrowserContext, Error


def url_to_proxy(url: str) -> str:
    _ = urlparse(url)
    return "http://{0}{1}{2}.atrust.njpi.edu.cn:443{3}{4}".format(
        _.hostname.replace(".", "-"),
        (f"-{_.port}-p" if _.port else ""),
        ("-s" if _.scheme == "https" else ""),
        (_.path if _.path else "/"),
        (f"?{_.query}" if _.query else "")
    )


class Url(Enum):
    login = "https://at.njpi.edu.cn/portal/#!/login"
    center = "https://at.njpi.edu.cn/portal/service_center.html"
    qrCode = "https://open.work.weixin.qq.com/wwopen/sso/qrImg?key="  # 16位字符串
    xfbApi = "http://ykt.njpi.edu.cn:8988/web/Common/Tsm.html"
    onlineInfo = "https://at.njpi.edu.cn/passport/v1/user/onlineInfo?clientType=SDPBrowserClient&platform=Windows" \
                 "&lang=zh-CN "
    
    @staticmethod
    def to_proxy(url: "Url"):
        return url_to_proxy(url.value)


class VPN:
    def __init__(self):
        self._client: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page_alive: Optional[Page] = None
        self.last_alive_time = ""
    
    async def _start(self, **kwargs):
        try:
            if not self._client:
                self._client = await async_playwright().start()
            _browser = await self._client.chromium.launch(**kwargs)
            return _browser
        except Exception as e:
            print("请检查是否配置好playwright环境")
            raise e
    
    async def get_context(self) -> BrowserContext:
        if not self._browser:
            await self._start(headless=True)
        if not self._context:
            self._context = await self._browser.new_context(storage_state='context.json')
        return self._context
    
    async def get_page(self) -> Page:
        return await (await self.get_context()).new_page()
    
    async def get_page_alive(self) -> Page:
        if not self._page_alive:
            self._page_alive = await self.get_page()
        return self._page_alive
    
    async def save(self):
        await (await self.get_context()).storage_state(path='context.json')
    
    def update_time(self):
        self.last_alive_time = str(datetime.now())[:-7]
    
    async def keep_alive(self):
        page = await self.get_page_alive()
        if await self.if_login():
            try:
                await page.goto("https://at.njpi.edu.cn/")
                await asyncio.sleep(1)
                await page.goto("https://at.njpi.edu.cn/portal/service_center.html#/app_apply")
            except Error:
                pass
            print(f"atrust VPN保活成功")
        else:
            print(f"atrust VPN保活失败")
        self.update_time()
        await self.save()
    
    async def login(self, callBack: Callable):
        if await self.if_login():
            return "已登陆"
        page = await self.get_page()
        try:
            await page.goto(Url.login.value)
            img = "https:" + await page.frame_locator("#scan_qrcode_iframe") \
                .frame_locator("iframe") \
                .locator('//*[@id="wwopen.ssoPage_$"]/div/div/div[2]/div[1]/img').get_attribute("src")
            if isinstance(callBack, Awaitable):
                await callBack(img)
            else:
                callBack(img)
            start_time = time.time()
            
            while time.time() - start_time <= 57:
                if Url.center.value in page.url or await self.if_login():
                    break
                await asyncio.sleep(1)
            if await self.if_login():
                print("登录成功")
            else:
                print("登录超时")
        finally:
            await page.close()
            await self.save()
    
    async def get_cookie(self, url: str) -> Optional[Tuple[str, str]]:
        if not await self.if_login():
            return None
        
        if not urlparse(url).hostname.endswith('atrust.njpi.edu.cn'):
            url = url_to_proxy(url)
        
        page = await self.get_page()
        
        try:
            await page.goto(url)
            for i in await (await self.get_context()).cookies():
                if i["name"] == "sdp_user_token":
                    return url, f"sdp_user_token={i['value']}"
            return None
        finally:
            await page.close()
            await self.save()
    
    async def get_login_info(self) -> Tuple[bool, Dict[str, str]]:
        try:
            resp = await (await self.get_context()).request.get(Url.onlineInfo.value)
            data = await resp.json()
        except Exception as e:
            print(f"获取登陆信息失败:\n{e}")
            data = {}
        return data.get("code") == 0, data
    
    async def if_login(self) -> bool:
        try:
            resp = await (await self.get_context()).request.get(Url.onlineInfo.value)
            data = await resp.text()
        except Exception as e:
            print(f"if_login[请求错误]:{e}")
            return False
        try:
            return json.loads(data)["code"] == 0
        except Exception as e:
            print(f"if_login[判断错误]:{e}")
            return False
