import httpx
import re
from typing import Optional, Dict
from pathlib import Path
import os

# 配置常量
DANMU_API_BASE_URL = os.getenv("DANMU_API_BASE_URL", "")
ZYPLAYER_BASE_URL = "http://127.0.0.1:9978/api/v1"
OUTPUT_DIR = Path(".")


def request(api, params=None):
    url = f"{ZYPLAYER_BASE_URL}/{api}"
    if params is None:
        response = httpx.get(url)
    else:
        response = httpx.get(url, params=params)
    if response.status_code != 200:
        print(f"{url} 请求失败！")
        return None
    data = response.json()
    return data


def get_activate_id(source_name: str) -> Optional[str]:
    api = "site/active"
    response_data = request(api)
    if not response_data:
        return None
    sources = response_data.get("data", {}).get("data", [])
    if not sources:
        print("没有找到任何激活的视频源")
        return None
    for item in sources:
        if source_name in item.get("name", ""):
            return item.get("id")
    return None


def get_video_id(source_id: str, film_name: str) -> Optional[str]:
    api = "cms/search"
    params = {"sourceId": source_id, "wd": film_name, "quick": "true"}
    response_data = request(api, params)
    if not response_data:
        return None
    video_list = response_data.get("data", {}).get("list", [])
    if not video_list:
        print(f"未找到影片: {film_name}")
        return None
    video_info = video_list[0]
    vod_id = video_info.get("vod_id")
    vod_name = video_info.get("vod_name", "未知")
    print(f"获取视频信息成功: 名称={vod_name}, ID={vod_id}, 请核对是否正确")
    return vod_id


def correct_episode_str(episode_str: str) -> int:
    episode_numbers = re.findall(r"\d+", episode_str)
    if episode_numbers:
        episode_num = int(episode_numbers[0])
        return episode_num
    else:
        return -1


def get_video_links(source_id: str, film_id: str) -> Dict[str, Dict[int, str]]:
    api = "cms/detail"
    params = {"sourceId": source_id, "id": film_id}
    response_data = request(api, params)
    if not response_data:
        return {}
    vod_links = {}
    video_list = response_data.get("data", {}).get("list", [])
    if not video_list:
        print("未找到视频播放列表！")
        return {}
    video_detail = video_list[0]
    play_from = video_detail.get("vod_play_from", "")
    play_url = video_detail.get("vod_play_url", "")
    if not play_from or not play_url:
        print("未找到视频来源和播放链接")
        return {}
    source_names = play_from.split("$$$")
    source_urls = play_url.split("$$$")
    for source_name, source_url in zip(source_names, source_urls):
        single_source_links = {}
        if not source_url:
            print("source_url拆分失败请检查!")
            continue
        episode_links = source_url.split("#")
        vod_type = "tv" if len(episode_links) > 1 else "movie"
        for episode_link in episode_links:
            if not episode_link or "$" not in episode_link:
                print("episode_link拆分失败请检查!")
                continue
            episode_str, link = episode_link.split("$", 1)  # 只分割第一个$
            episode_index = correct_episode_str(episode_str)
            if episode_index != -1 and link.strip():
                single_source_links[episode_index] = link.strip()
            else:
                if vod_type == "movie":
                    single_source_links[1] = link.strip()
        if single_source_links:
            vod_links[source_name] = single_source_links
    return vod_links


def zyplayer_to_json(
    source_name: str, film_name: str, film_source: Optional[str] = None
) -> bool:
    save_data = {}
    save_data["title"] = film_name
    # 获取视频源ID
    source_id = get_activate_id(source_name)
    if not source_id:
        print(f"获取视频源ID失败: {source_name}")
        return False
    # 获取影片ID
    film_id = get_video_id(source_id, film_name)
    if not film_id:
        print(f"获取影片ID失败: {film_name}")
        return False

    # 获取播放链接
    vod_links = get_video_links(source_id, film_id)
    if not vod_links:
        print(f"获取播放链接失败: {film_name}")
        return False
    if film_source is not None:
        if film_source in vod_links:
            save_data["list"] = {film_source: vod_links[film_source]}
        else:
            print(
                f"未找到指定的播放源'{film_source}'，可用播放源: {list(vod_links.keys())}"
            )
            return False
    else:
        save_data["list"] = vod_links
        print(save_data)
        # 发送到接口
        res = httpx.post(f"{DANMU_API_BASE_URL}/upload", json=save_data)
        if res.status_code != 200:
            print("发送数据失败")
            return False
        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="获取视频播放链接工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-s", "--sourceName", type=str, required=True, help="视频源名称（必需）"
    )

    parser.add_argument(
        "-f", "--filmName", type=str, required=True, help="影片名称（必需）"
    )

    parser.add_argument(
        "-j",
        "--filmSource",
        type=str,
        required=False,
        default=None,
        help="指定播放源（可选），不指定时保存所有播放源",
    )
    args = parser.parse_args()
    # 执行主函数
    success = zyplayer_to_json(
        args.sourceName.strip(),
        args.filmName.strip(),
        args.filmSource.strip() if args.filmSource else None,
    )
    if success:
        print("发送数据成功")
    else:
        print("发送数据失败")
