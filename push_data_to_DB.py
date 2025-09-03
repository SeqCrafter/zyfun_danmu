import httpx
import re
import json
import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import os

# 配置常量
DANMU_API_BASE_URL = os.getenv("DANMU_API_BASE_URL", "")
ZYPLAYER_BASE_URL = "http://127.0.0.1:9978/api/v1"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
OUTPUT_DIR = Path(".")

# 配置日志 - 只输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def request(
    api: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    发送HTTP请求到ZYPlayer API

    Args:
        api: API端点
        params: 请求参数

    Returns:
        响应的JSON数据，失败时返回None
    """
    url = f"{ZYPLAYER_BASE_URL}/{api}"

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"正在请求API: {api}, 参数: {params}, 尝试次数: {attempt + 1}")

            response = httpx.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()  # 检查HTTP状态码

            data = response.json()
            logger.info(f"API请求成功: {api}")
            return data

        except httpx.TimeoutException:
            logger.warning(f"请求超时 (尝试 {attempt + 1}/{MAX_RETRIES}): {url}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误 {e.response.status_code}: {url}")
            break  # HTTP错误通常不需要重试
        except httpx.RequestError as e:
            logger.warning(f"请求错误 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
        except json.JSONDecodeError:
            logger.error(f"JSON解析失败: {url}")
            break
        except Exception as e:
            logger.error(f"未知错误: {e}")
            break

    logger.error(f"API请求失败，已达到最大重试次数: {api}")
    return None


def get_activate_id(source_name: str) -> Optional[str]:
    """
    获取激活的视频源ID

    Args:
        source_name: 视频源名称

    Returns:
        视频源ID，未找到时返回None
    """
    if not source_name or not source_name.strip():
        logger.error("视频源名称不能为空")
        return None

    api = "site/active"
    response_data = request(api)

    if not response_data:
        logger.error("获取激活源列表失败")
        return None

    try:
        sources = response_data.get("data", {}).get("data", [])
        if not sources:
            logger.warning("没有找到任何激活的视频源")
            return None

        for item in sources:
            if source_name in item.get("name", ""):
                logger.info(
                    f"找到匹配的视频源: {item.get('name')}, ID: {item.get('id')}"
                )
                return item.get("id")

        logger.warning(f"未找到匹配的视频源: {source_name}")
        return None

    except (KeyError, TypeError) as e:
        logger.error(f"解析激活源数据时出错: {e}")
        return None


def get_video_id(source_id: str, film_name: str) -> Optional[str]:
    """
    根据视频源ID和影片名称搜索视频ID

    Args:
        source_id: 视频源ID
        film_name: 影片名称

    Returns:
        视频ID，未找到时返回None
    """
    if not source_id or not film_name:
        logger.error("视频源ID和影片名称不能为空")
        return None

    api = "cms/search"
    params = {"sourceId": source_id, "wd": film_name, "quick": "true"}
    response_data = request(api, params)

    if not response_data:
        logger.error(f"搜索影片失败: {film_name}")
        return None

    try:
        video_list = response_data.get("data", {}).get("list", [])
        if not video_list:
            logger.warning(f"未找到影片: {film_name}")
            return None

        video_info = video_list[0]
        vod_id = video_info.get("vod_id")
        vod_name = video_info.get("vod_name", "未知")
        vod_content = video_info.get("vod_content", "无简介")

        logger.info(f"获取视频信息成功: 名称={vod_name}, ID={vod_id}")
        logger.debug(f"视频简介: {vod_content[:100]}...")  # 只显示前100个字符

        return vod_id

    except (KeyError, TypeError, IndexError) as e:
        logger.error(f"解析搜索结果时出错: {e}")
        return None


def correct_episode_str(episode_str: str) -> int:
    """
    从剧集字符串中提取集数

    Args:
        episode_str: 剧集字符串，如"第1集"、"EP01"等

    Returns:
        集数，提取失败时返回-1
    """
    if not episode_str:
        logger.warning("剧集字符串为空")
        return -1

    try:
        episode_numbers = re.findall(r"\d+", episode_str)
        if episode_numbers:
            episode_num = int(episode_numbers[0])
            logger.debug(f"从'{episode_str}'中提取到集数: {episode_num}")
            return episode_num
        else:
            logger.warning(f"无法从'{episode_str}'中提取集数")
            return -1
    except (ValueError, TypeError) as e:
        logger.error(f"解析剧集字符串时出错: {e}")
        return -1


def get_video_links(source_id: str, film_id: str) -> Dict[str, Dict[int, str]]:
    """
    获取视频播放链接

    Args:
        source_id: 视频源ID
        film_id: 影片ID

    Returns:
        视频链接字典，格式为 {播放源名称: {集数: 播放链接}}
    """
    if not source_id or not film_id:
        logger.error("视频源ID和影片ID不能为空")
        return {}

    api = "cms/detail"
    params = {"sourceId": source_id, "id": film_id}
    response_data = request(api, params)

    if not response_data:
        logger.error(f"获取视频详情失败: film_id={film_id}")
        return {}

    vod_links = {}

    try:
        video_list = response_data.get("data", {}).get("list", [])
        if not video_list:
            logger.warning(f"未找到视频详情: film_id={film_id}")
            return {}

        video_detail = video_list[0]
        play_from = video_detail.get("vod_play_from", "")
        play_url = video_detail.get("vod_play_url", "")

        if not play_from or not play_url:
            logger.warning("视频播放信息为空")
            return {}

        source_names = play_from.split("$$$")
        source_urls = play_url.split("$$$")

        for source_name, source_url in zip(source_names, source_urls):
            logger.info(f"处理播放源: {source_name}")
            single_source_links = {}

            if not source_url:
                logger.warning(f"播放源'{source_name}'的链接为空")
                continue
            episode_links = source_url.split("#")
            vod_type = "tv" if len(episode_links) > 1 else "movie"
            for episode_link in episode_links:
                if not episode_link or "$" not in episode_link:
                    logger.debug(f"跳过无效的剧集链接: {episode_link}")
                    continue

                try:
                    episode_str, link = episode_link.split("$", 1)  # 只分割第一个$
                    episode_index = correct_episode_str(episode_str)

                    if episode_index != -1 and link.strip():
                        single_source_links[episode_index] = link.strip()
                    else:
                        if vod_type == "movie":
                            single_source_links[1] = link.strip()
                        else:
                            logger.debug(f"跳过无效剧集: {episode_str}")

                except ValueError as e:
                    logger.warning(f"解析剧集链接失败: {episode_link}, 错误: {e}")
                    continue

            if single_source_links:
                vod_links[source_name] = single_source_links
                logger.info(
                    f"播放源'{source_name}'获取到{len(single_source_links)}个剧集"
                )
            else:
                logger.warning(f"播放源'{source_name}'没有有效的剧集链接")

    except (KeyError, TypeError, IndexError) as e:
        logger.error(f"解析视频链接时出错: {e}")
        return {}

    logger.info(f"总共获取到{len(vod_links)}个播放源")
    return vod_links


def zyplayer_to_json(
    source_name: str, film_name: str, film_source: Optional[str] = None
) -> bool:
    """
    从ZYPlayer获取视频链接并保存为JSON文件

    Args:
        source_name: 视频源名称
        film_name: 影片名称
        film_source: 指定播放源，为None时保存所有播放源

    Returns:
        操作是否成功
    """
    save_data = {}
    save_data["title"] = film_name
    try:
        logger.info(f"开始处理ZYPlayer视频: {film_name}, 源: {source_name}")

        # 获取视频源ID
        source_id = get_activate_id(source_name)
        if not source_id:
            logger.error(f"获取视频源ID失败: {source_name}")
            return False

        logger.info(f"获取到视频源ID: {source_id}")

        # 获取影片ID
        film_id = get_video_id(source_id, film_name)
        if not film_id:
            logger.error(f"获取影片ID失败: {film_name}")
            return False

        logger.info(f"获取到影片ID: {film_id}")

        # 获取播放链接
        vod_links = get_video_links(source_id, film_id)
        if not vod_links:
            logger.error(f"获取播放链接失败: {film_name}")
            return False

        if film_source is not None:
            if film_source in vod_links:
                save_data["list"] = {film_source: vod_links[film_source]}
                logger.info(f"保存指定播放源'{film_source}'的链接")
            else:
                logger.error(
                    f"未找到指定的播放源'{film_source}'，可用播放源: {list(vod_links.keys())}"
                )
                return False
        else:
            save_data["list"] = vod_links
            logger.info("保存所有播放源的链接")

        # 发送到接口
        res = httpx.post(f"{DANMU_API_BASE_URL}/upload", json=save_data)
        print(res.json())
        return True

    except Exception as e:
        logger.error(f"处理ZYPlayer视频时出错: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="获取视频播放链接工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python fetch_data.py -s "爱奇艺" -f "狂飙"
  python fetch_data.py -s "腾讯视频" -f "三体" -j "高清"
        """,
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

    try:
        args = parser.parse_args()

        # 参数验证
        if not args.sourceName.strip():
            logger.error("视频源名称不能为空")
            sys.exit(1)

        if not args.filmName.strip():
            logger.error("影片名称不能为空")
            sys.exit(1)

        # 执行主函数
        success = zyplayer_to_json(
            args.sourceName.strip(),
            args.filmName.strip(),
            args.filmSource.strip() if args.filmSource else None,
        )

        # 根据执行结果设置退出码
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序执行异常: {e}")
        sys.exit(1)
