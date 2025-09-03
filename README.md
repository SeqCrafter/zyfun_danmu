# 弹幕库 API for ZYPlayer

使用 Robyn 构建的 api 用于转换 zyplayer 的播放链接到视频标题和集数，需要配合弹幕抓取接口(例如[misaka_danmu_server](https://github.com/l429609201/misaka_danmu_server))使用

## 功能

- 上传视频的名称，播放地址以及播放线路到数据库
- 通过视频的播放链接获取视频的弹幕
- 删除视频和对应来源的链接

## 原理

[zyfun(ZyPlayer)](https://github.com/Hiram-Wong/ZyPlayer)的弹幕获取方式为在你设置的接口上拼接视频的播放地址，那么对于非官方源来说，
必须根据地址反向获取视频的名称和集数，然后根据名称和集数从弹幕接口获取弹幕。

这个弹幕接口我们使用[misaka_danmu_server](https://github.com/l429609201/misaka_danmu_server)，因为这个有一个 UI 界面可以允许用户手动设置需要抓取的视频弹幕，我们可以轻易的根据视频标题和集数获取对应的弹幕（详细请查询`弹弹Play`的接口文档）

## 依赖

- Docker Compose
- misaka_danmu_server

## 快速开始

### 使用 Docker Compose 启动

需要修改`docker-compose.yml`中的`POSTGRES_PASSWORD`为你的 PostgreSQL 密码，以及`API_BASE_URL`为你的弹幕抓取接口的地址
这里的 API_BASE_URL 是`misaka_danmu_server`接口的地址，例如：`http://localhost:7768/api/v1/<API_KEY>`

```bash
# 启动服务
docker-compose up -d
```

## 环境变量

配置以下环境变量用于 PostgreSQL 连接:

- `POSTGRES_USER`: PostgreSQL username (default: `postgres`)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: `password`)
- `POSTGRES_HOST`: PostgreSQL host (default: `localhost`)
- `POSTGRES_PORT`: PostgreSQL port (default: `5432`)
- `POSTGRES_DB`: Database name (default: `video_database`)
- `API_BASE_URL`: 弹幕抓取接口的地址 (default: `http://localhost:7768/api/v1/<API_KEY>`)

## API 接口

### GET /url

通过 URL 查询视频信息和获取弹幕

```bash
curl "http://localhost:8080/url?url=https://example.com/video.mp4"
```

### POST /upload

批量上传视频数据

```bash
curl -X POST http://localhost:8080/upload \
  -H "Content-Type: application/json" \
  -d '{
    "title": "视频标题",
    "list": {
      "源1": {
        "1": "https://example.com/ep1.mp4",
        "2": "https://example.com/ep2.mp4"
      }
    }
  }'
```

### DELETE /video

删除指定视频来源的所有播放链接

```bash
curl -X DELETE "http://localhost:8080/video?title=视频标题&source=源1"
```

## 从 ZYPlayer 获取数据

需要手动将你想观看的视频地址发送到接口数据库中才可以获取弹幕
本仓库也提供了一个获取视频地址并上传的脚本

使用 `push_data_to_DB.py` 脚本从 ZYPlayer 获取数据:

```bash
## 播放源是可选项，因为有的视频并没有播放源
DANMU_API_BASE_URL={你搭建的zyfun弹幕的api接口非API_BASE_URL} python push_data_to_DB.py -s "视频源名称" -f "影片名称" [-j "播放源"]
```

## License

MIT License
