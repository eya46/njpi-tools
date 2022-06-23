from typing import Union

import httpx


class PayElect:
    def __init__(self, ticket: str):
        """
        :param ticket: 相当于token,权限很大(一串32位字符，根据名称自行抓包获取)
        """
        self.ticket = ticket
    
    @classmethod
    def _build_data(cls, room: str, money: float):
        money *= 100
        money = str(int(money))
        
        if room[0] in ["1", "2", "3", "4", "5", "6", "10"]:
            aid = "0030000000002501"
            floor_id = ""
            room_id = room
            _room = room
            if len(room) == 5:
                if room[1] == "0":
                    building = f"{room[0]}号楼"
                    building_id = "69"
                else:
                    building = f"{room[0]}号楼"
                    building_id = room[0]
            else:
                building = f"{room[0]}号楼"
                building_id = room[0]
            area_id = "1"
            area_name = "南京科技职业学院"
        else:
            aid = "0030000000003801"
            floor_id = f"00{room[1]}"
            room_id = f"0{room[1:4]}"
            _room = room[1:4]
            building_id = f"00{room[0]}"
            building = f"{room[0]}号楼"
            area_id = "主校区"
            area_name = "主校区"
        
        post_data = {
            "acctype": "###",
            "paytype": "1",
            "aid": aid,
            # 不确定要必须正确
            "account": "312345",
            "tran": money,
            "roomid": room_id,
            "room": _room,
            "floorid": floor_id,
            "floor": "",
            "buildingid": building_id,
            "building": building,
            "areaid": area_id,
            "areaname": area_name,
            "qpwd": "",
            "json": "true"
        }
        
        return post_data
    
    @classmethod
    def check_room(cls, room: Union[str, int]) -> bool:
        room = str(room)
        if isinstance(room, str):
            if not room.isdigit():
                return False
            else:
                room = int(room)
        if not (1000 < room < 99999):
            return False
        else:
            return True
    
    @classmethod
    def check_money(cls, money: Union[str, int, float]):
        if isinstance(money, str):
            try:
                money = float(money)
            except:
                return False
        # 一次性限制充100
        if not (0 < money <= 100):
            return False
        else:
            return True
    
    def call(self, room: Union[str, int], money: Union[str, int, float]) -> httpx.Response:
        if not self.check_room(room):
            raise Exception("房间号错误！")
        if not self.check_money(money):
            raise Exception("充值金额错误！")
        room = str(room)
        money = float(money)
        #
        with httpx.Client() as client:
            client: httpx.Client
            _resp = client.get(
                f"http://210.28.10.180:8988/web/common/checkEle.html?ticket={self.ticket}&from=ehall&cometype="
            )
            client.cookies.extract_cookies(_resp)
            if _resp.status_code in (502, 302):
                raise Exception("学付宝无法连接")
            return client.post(
                "http://210.28.10.180:8988/web/Elec/PayElecGdc.html?sf_request_type=ajax",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                },
                data=self._build_data(room, money)
            )
    
    async def call_sync(self, room: Union[str, int], money: Union[str, int, float]) -> httpx.Response:
        if not self.check_room(room):
            raise Exception("房间号错误！")
        if not self.check_money(money):
            raise Exception("充值金额错误！")
        room = str(room)
        money = float(money)
        #
        async with httpx.AsyncClient() as client:
            client: httpx.AsyncClient
            _resp = await client.get(
                f"http://210.28.10.180:8988/web/common/checkEle.html?ticket={self.ticket}&from=ehall&cometype="
            )
            client.cookies.extract_cookies(_resp)
            if _resp.status_code in (502, 302):
                raise Exception("学付宝无法连接")
            return await client.post(
                "http://210.28.10.180:8988/web/Elec/PayElecGdc.html?sf_request_type=ajax",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                },
                data=self._build_data(room, money)
            )
    
    @classmethod
    def resp_to_str(cls, resp: httpx.Response) -> str:
        try:
            if "异常" in resp.text:
                return "学付宝暂时关闭!"
            _res = resp.json()
            return _res["pay_elec_gdc"]["errmsg"]
        except:
            return "充值结果解析失败"
    
    def main(self, room: Union[str, int], money: Union[str, int, float]) -> str:
        try:
            resp = self.call(room, money)
            return self.resp_to_str(resp)
        except Exception as e:
            return f"错误:{e}"
    
    async def main_sync(self, room: Union[str, int], money: Union[str, int, float]) -> str:
        try:
            resp = await self.call_sync(room, money)
            return self.resp_to_str(resp)
        except Exception as e:
            return f"错误:{e}"


if __name__ == '__main__':
    p = PayElect("????????????????????????????????")
    e = p.call("1234", "0.1")
    print(
        e
    )
