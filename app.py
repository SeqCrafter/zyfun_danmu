from robyn import Robyn, ALLOW_CORS
from robyn.logger import logger, Colors
import json
import os

from contrib import register_tortoise
from crud import query_by_url, batch_insert_videos

from function import fetch_danmu_by_title

app = Robyn(__file__)
app.add_response_header("content-type", "application/json")
ALLOW_CORS(app, origins=["*"])

# 构建PostgreSQL连接URL
db_url = os.getenv("DATABASE_URL")

# 注册Tortoise ORM
register_tortoise(
    app,
    db_url=db_url,
    modules={"models": ["models"]},
    generate_schemas=True,
)


@app.before_request()
async def log_request(request):
    logger.info("Received request: %s", request.query_params, color=Colors.BLUE)
    return request


@app.get("/url")
async def get_video_info(query_params):
    url = query_params.get("url", "")
    if not url:
        return {"error": "URL参数是必需的"}, {}, 400
    result = await query_by_url(url)
    if result:
        danmu = await fetch_danmu_by_title(
            result["title"], str(result["episode_index"])
        )
        return danmu, {}, 200
    else:
        return {"error": "未找到匹配的URL"}, {}, 404


@app.post("/upload")
async def upload_video_data(body):
    try:
        data = json.loads(body)

        # 验证数据格式
        if not data.get("title") or not data.get("list"):
            return {"error": "数据格式错误，需要包含title和list字段"}, {}, 400

        title = data["title"]
        sources_data = data["list"]

        if not isinstance(sources_data, dict) or not sources_data:
            return {"error": "list字段必须是非空字典"}, {}, 400

        success_count = 0
        error_count = 0

        # 遍历每个来源
        for source_name, episodes in sources_data.items():
            if not isinstance(episodes, dict):
                error_count += 1
                continue

            try:
                # 转换集数索引和URL列表
                episode_indexes = []
                urls = []

                for episode_str, url in episodes.items():
                    try:
                        episode_index = int(episode_str)
                        episode_indexes.append(episode_index)
                        urls.append(url)
                    except ValueError:
                        logger.warning(f"跳过无效的集数索引: {episode_str}")

                if not episode_indexes:
                    error_count += 1
                    continue

                # 批量插入数据
                insert_success = await batch_insert_videos(
                    title=title,
                    source=source_name,
                    episode_indexes=episode_indexes,
                    urls=urls,
                )
                if insert_success:
                    success_count += 1
                else:
                    error_count += 1

            except Exception as e:
                error_count += 1

                logger.error(f"处理来源 {source_name} 时出错: {e}", color=Colors.RED)

        return (
            {
                "success": success_count > 0,
                "message": f"处理完成：成功 {success_count} 个来源，失败 {error_count} 个来源",
                "data": {
                    "title": title,
                    "success_count": success_count,
                    "error_count": error_count,
                },
            },
            {},
            200,
        )

    except json.JSONDecodeError:
        return {"error": "JSON格式错误"}, {}, 400
    except Exception as e:
        logger.error(f"上传数据时出错: {e}", color=Colors.RED)
        return {"error": f"服务器内部错误: {str(e)}"}, {}, 500


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=8080)
