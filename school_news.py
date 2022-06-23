import os
from typing import Union, List, Tuple, Dict
import json

from httpx import AsyncClient
from lxml import etree

DEBUG = True


def log(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


class Article:
    def __init__(self, *args):
        self.time = args[0]
        self.url = args[1]
        self.title = args[2]


local = os.path.dirname(__file__)


# 获取当前目录下的文件地址
def get_file_path(name: str) -> str:
    return os.path.join(local, name)


def get_old_news() -> Dict[str, str]:
    with open(get_file_path("news.json"), 'r', encoding="utf-8") as f:
        return json.loads(f.read())


def save_old_news(old_news: Dict[str, str]):
    with open(get_file_path("news.json"), 'w', encoding="utf-8") as f:
        f.write(json.dumps(old_news, ensure_ascii=False))


async def get_articles(tid: Union[str, int], pass_title: str) -> Tuple[str, List[Article]]:
    _articles: List[Article] = []
    async with AsyncClient(verify=False) as r:
        r: AsyncClient
        web = await r.get(f"https://www.njpi.edu.cn/xww/{tid}/list.htm")
        x: etree._Element = etree.HTML(web.text)
        try:
            _type = "|".join([i.text for i in x.xpath('//*[@id="container"]/div/div[2]/div[1]/ul/li[2]/a')])
        except Exception as e:
            log(e)
            log("获取学校新闻的分类失败，url:" + f"https://www.njpi.edu.cn/xww/{tid}/list.htm")
            _type = "未知(解析失败)"
        
        for i in x.xpath('//*[@id="wp_news_w8"]/ul/li'):
            try:
                _time = i.xpath("./div/span/text()")[1]
            except Exception as e:
                log(e)
                log("获取学校新闻失败，url:" + f"https://www.njpi.edu.cn/xww/{tid}/list.htm")
                continue
            try:
                _url = "https://www.njpi.edu.cn" + i.xpath("./div/span/a")[0].get("href")
                _title = i.xpath("./div/span/a")[0].get("title")
            except Exception as e:
                log(e)
                log("获取学校新闻标题和网址失败，url:" + f"https://www.njpi.edu.cn/xww/{tid}/list.htm")
                continue
            if _title == pass_title:
                break
            _articles.append(Article(_time, _url, _title))
        return _type, _articles


async def get_all_articles() -> List[Tuple[str, List[Article]]]:
    all_articles: List[Tuple[str, List[Article]]] = []
    _old_news = get_old_news()
    for i in _old_news:
        _type, _articles = await get_articles(i, _old_news[i])
        if len(_articles) == 0:
            continue
        # 太多新新闻也不记录
        if len(_articles) > 5:
            _old_news[i] = _articles[0].title
            continue
        else:
            for j in _articles[::-1]:
                _old_news[i] = j.title
        all_articles.append((_type, _articles))
    save_old_news(_old_news)
    return all_articles


def article_to_str(str_articles: Tuple[str, List[Article]]):
    # 反文章索引，这样最新的文章会在最新的消息发出
    for i in str_articles[1][::-1]:
        # 原本用在机器里面，方便构造Message，现在改成直接返回str
        msg = \
            f"《学校新闻》\n" \
            f"分类:{str_articles[0]}\n\n" \
            f"标题:\n--{i.title}\n\n" \
            f"时间:{i.time}\n\n" \
            f"网址:\n{i.url}"
        yield msg


if __name__ == '__main__':
    import asyncio
    
    arts = asyncio.get_event_loop().run_until_complete(get_articles("53", ""))
    print(arts[0], "标题:", [i.title for i in arts[1]])
