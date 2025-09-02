from models import Video, VideoSource, PlayLink
from typing import Optional, List, Dict, Any


async def delete_video_source(title: str, source: str) -> int:
    """
    删除指定视频和来源的所有播放链接
    
    Args:
        title: 视频标题
        source: 视频来源名称
    
    Returns:
        删除的记录数量
    """
    try:
        # 查找视频
        video = await Video.filter(title=title).first()
        if not video:
            print(f"未找到视频: {title}")
            return 0
        
        # 查找视频来源
        video_source = await VideoSource.filter(video=video, name=source).first()
        if not video_source:
            print(f"未找到视频'{title}'的来源: {source}")
            return 0
        
        # 删除所有相关的播放链接
        deleted_count = await PlayLink.filter(
            video=video, 
            source=video_source
        ).delete()
        
        print(f"成功删除视频'{title}'来源'{source}'的{deleted_count}条播放链接")
        
        # 如果该来源下没有其他播放链接了，删除来源记录
        remaining_links = await PlayLink.filter(source=video_source).count()
        if remaining_links == 0:
            await video_source.delete()
            print(f"删除空的视频来源记录: {source}")
        
        # 如果该视频下没有其他来源了，删除视频记录
        remaining_sources = await VideoSource.filter(video=video).count()
        if remaining_sources == 0:
            await video.delete()
            print(f"删除空的视频记录: {title}")
        
        return deleted_count
        
    except Exception as e:
        print(f"删除数据出错: {e}")
        return 0


async def query_by_url(url: str) -> Optional[Dict[str, Any]]:
    try:
        # 根据URL查询PlayLink，并预加载相关的video和source
        play_link = (
            await PlayLink.filter(url=url).prefetch_related("video", "source").first()
        )

        if not play_link:
            print(f"未找到URL: {url}")
            return None

        # 获取相关信息
        title = play_link.video.title
        episode_index = play_link.episode_index
        source_name = play_link.source.name

        # 打印来源名称（根据用户要求）
        print(f"来源名称: {source_name}")

        result = {
            "title": title,
            "episode_index": episode_index,
            "source_name": source_name,
            "url": url,
        }

        print(
            f"查询结果: 视频标题='{title}', 集数={episode_index}, 来源='{source_name}'"
        )
        return result

    except Exception as e:
        print(f"查询出错: {e}")
        return None


async def batch_insert_videos(
    title: str, source: str, episode_indexes: List[int], urls: List[str]
) -> bool:
    try:
        # 检查参数长度是否一致
        if len(episode_indexes) != len(urls):
            print(
                f"错误: episode_indexes长度({len(episode_indexes)})与urls长度({len(urls)})不匹配"
            )
            return False

        # 创建或获取视频记录
        video, created = await Video.get_or_create(title=title)
        if created:
            print(f"创建新视频: {title}")
        else:
            print(f"使用已存在的视频: {title}")

        # 创建或获取视频来源记录
        video_source, created = await VideoSource.get_or_create(
            video=video, name=source
        )
        if created:
            print(f"创建新视频来源: {source}")
        else:
            print(f"使用已存在的视频来源: {source}")

        # 批量创建播放链接
        play_links_to_create = []
        existing_count = 0

        for episode_index, url in zip(episode_indexes, urls):
            # 检查是否已存在相同的记录
            existing = await PlayLink.filter(
                video=video, source=video_source, episode_index=episode_index
            ).exists()

            if existing:
                existing_count += 1
                print(f"跳过已存在的记录: 第{episode_index}集")
                continue

            play_links_to_create.append(
                PlayLink(
                    video=video,
                    source=video_source,
                    episode_index=episode_index,
                    url=url,
                )
            )

        # 批量插入新的播放链接
        if play_links_to_create:
            await PlayLink.bulk_create(play_links_to_create)
            print(f"成功插入 {len(play_links_to_create)} 条播放链接记录")

        if existing_count > 0:
            print(f"跳过了 {existing_count} 条已存在的记录")

        print(
            f"批量插入完成: 视频='{title}', 来源='{source}', 总集数={len(episode_indexes)}"
        )
        return True

    except Exception as e:
        print(f"批量插入出错: {e}")
        return False
