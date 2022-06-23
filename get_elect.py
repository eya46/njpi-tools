import json
from typing import Union, Dict, Any

import httpx
from httpx import ReadTimeout, ConnectTimeout


class Elect:
    def __init__(self, room: Union[str, int]):
        if not self.check_room(room):
            raise Exception("房间号错误!")
        self.room = room
        # 想办法访问到(这个外网访问不了，想办法弄个校内代理吧)
        self.url = "http://210.28.10.180:8988/web/Common/Tsm.html"
    
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
    
    def _build_data(self) -> Dict[str, Any]:
        room = self.room
        _data = {
            "funname": "synjones.onecard.query.elec.roominfo",
            "json": "true"
        }
        
        def cgdk():
            if len(room) == 5:
                if room[1] == "0":
                    building = f"{room[0]}号楼"
                    buildingid = "69"
                else:
                    building = f"{room[0]}号楼"
                    buildingid = room[0]
            else:
                building = f"{room[0]}号楼"
                buildingid = room[0]
            
            return json.dumps({'query_elec_roominfo': {
                'aid': '0030000000002501',
                'account': '33333',
                'room': {'roomid': room, 'room': room},
                'floor': {'floorid': '', 'floor': ''},
                'area': {'area': '1', 'areaname': ''},
                'building': {'buildingid': buildingid, 'building': building}
            }}, ensure_ascii=False)
        
        def sfdk():
            return json.dumps({'query_elec_roominfo': {
                'aid': '0030000000003801',
                'account': '33333',
                'room': {'roomid': '0' + room[1:4], 'room': room[1:4]},
                'floor': {'floorid': '00' + room[1], 'floor': '00' + room[1]},
                'area': {'area': '主校区', 'areaname': '主校区'},
                'building': {'buildingid': '00' + room[0], 'building': room[0] + '号楼'}}
            }, ensure_ascii=False)
        
        # 不同的电控系统
        if room[0] in ["1", "2", "3", "4", "5", "6", "10"]:
            _data["jsondata"] = cgdk()
        else:
            _data["jsondata"] = sfdk()
        return _data
    
    # 大概率会请求失败，自行处理
    def call(self) -> httpx.Response:
        return httpx.post(
            self.url,
            params=self._build_data(),
            timeout=2
        )
    
    # 大概率会请求失败，自行处理
    async def call_sync(self) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            client: httpx.AsyncClient
            return await client.post(
                self.url,
                params=self._build_data(),
                timeout=2
            )
    
    @classmethod
    def resp_to_str(cls, resp: httpx.Response) -> str:
        if "系统异常" in resp.text:
            return "学付宝暂时关闭!"
        try:
            elect = resp.json()["query_elec_roominfo"]["errmsg"]
        except:
            return "电费结果解析失败!"
        
        # 如果存在房间号会抹除
        if len(elect.split("电量")) < 2:
            return elect
        else:
            if len(elect.split("电量为")) < 2:
                return f'房间剩余电量为{elect.split("电量")[1]}'
            else:
                return f'房间剩余电量为{elect.split("电量为")[1]}'
    
    def main(self):
        try:
            return self.resp_to_str(self.call())
        except Exception as e:
            if isinstance(e, (ReadTimeout, ConnectTimeout)):
                return f"网络超时{e}"
            return f"未知报错:{e}"
    
    async def main_sync(self):
        try:
            return self.resp_to_str(await self.call_sync())
        except Exception as e:
            if isinstance(e, (ReadTimeout, ConnectTimeout)):
                return "网络超时"
            return f"未知报错:{e}"


if __name__ == '__main__':
    print(
        Elect("1234").main()
    )
