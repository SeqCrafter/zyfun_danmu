from tortoise.models import Model
from tortoise import fields


class Video(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=255, description="视频标题", unique=True)

    # 多对多关系：一个视频可以有多个来源，一个来源也可以对应多个视频
    sources: fields.ManyToManyRelation["VideoSource"] = fields.ManyToManyField(
        "models.VideoSource",
        related_name="videos",
        through="video_video_source",
        description="视频的多个来源",
    )

    # 反向关系
    play_links: fields.ReverseRelation["PlayLink"]

    class Meta:
        table = "videos"

    def __str__(self):
        return self.title


class VideoSource(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100, description="来源名称", unique=True)

    # 多对多关系的反向引用（由Video模型定义）
    videos: fields.ManyToManyRelation[Video]

    # 反向关系
    play_links: fields.ReverseRelation["PlayLink"]

    class Meta:
        table = "video_sources"

    def __str__(self):
        return self.name


class PlayLink(Model):
    id = fields.IntField(primary_key=True)
    episode_index = fields.IntField(description="集数索引")
    url = fields.TextField(description="播放链接")

    # 外键关系 - 仍然需要明确指向具体的视频和来源
    video: fields.ForeignKeyRelation[Video] = fields.ForeignKeyField(
        "models.Video", related_name="play_links", description="关联的视频"
    )

    source: fields.ForeignKeyRelation[VideoSource] = fields.ForeignKeyField(
        "models.VideoSource", related_name="play_links", description="关联的视频来源"
    )

    class Meta:
        table = "play_links"
        unique_together = (
            "video",
            "source",
            "episode_index",
        )  # 同一视频同一来源下集数不能重复
        ordering = ["episode_index"]  # 默认按集数排序

    def __str__(self):
        return f"{self.video.title} - {self.source.name} - 第{self.episode_index}集"
