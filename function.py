import httpx
from typing import Optional, Dict, List, Any
import os

# 常量定义
API_BASE_URL = os.getenv("API_BASE_URL", "")
DEFAULT_FONT_SIZE = "25px"


def parse_barrage(barrage_data: dict) -> List[Any]:
    text = barrage_data.get("m", "")
    meta = barrage_data.get("p", "0,1,16777215,0")
    time_str, mode_str, color_str, sender = meta.split(",", 3)
    time = float(time_str)
    mode = int(mode_str)
    color_int = int(color_str)
    color = f"#{color_int:06X}" if color_int >= 0 else "#FFFFFF"
    return [time, mode, color, DEFAULT_FONT_SIZE, text]


async def fetch_episode_id_by_title(
    title: str, episode_number: str, client: httpx.AsyncClient
) -> Optional[str]:
    api_url = f"{API_BASE_URL}/search/episodes"
    response = await client.get(
        api_url, params={"anime": title, "episode": episode_number}
    )
    res_data = response.json()
    if (
        res_data.get("success")
        and res_data.get("animes")
        and len(res_data["animes"]) > 0
    ):
        episode_id = res_data["animes"][0]["episodes"][0].get("episodeId")
        if episode_id:
            return episode_id
    return None


async def fetch_danmu_by_episode_id(
    episode_id: str, client: httpx.AsyncClient
) -> Dict[str, Any]:
    api_url = f"{API_BASE_URL}/comment/{episode_id}"
    response = await client.get(api_url)
    res_data = response.json()
    if res_data:
        # 获取弹幕数量
        danmu_count = res_data.get("count", 0)
        # 批量处理弹幕内容
        comments = res_data.get("comments", [])
        # 使用列表推导式提高性能
        danmu_content = [
            parse_barrage(barrage_data)
            for barrage_data in comments
            if isinstance(barrage_data, dict)
            and barrage_data.get("m")
            and barrage_data.get("p")
        ]
        return {
            "code": 1,
            "name": episode_id,
            "danmu": danmu_count,  # 使用实际解析成功的数量
            "danmuku": danmu_content,
        }
    return {
        "code": 0,
        "name": episode_id,
        "danmu": 0,
        "danmuku": [],
    }


async def fetch_danmu_by_title(title: str, episode_number: str) -> Dict[str, Any]:
    ## check if api_base_url is valid
    if not API_BASE_URL:
        return {
            "code": 0,
            "name": title,
            "danmu": 0,
            "danmuku": [],
        }
    async with httpx.AsyncClient() as client:
        episode_id = await fetch_episode_id_by_title(title, episode_number, client)
        if episode_id:
            return await fetch_danmu_by_episode_id(episode_id, client)

    return {
        "code": 0,
        "name": title,
        "danmu": 0,
        "danmuku": [],
    }
