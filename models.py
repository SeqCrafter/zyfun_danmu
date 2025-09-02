from tortoise.models import Model
from tortoise import fields


class Video(Model):
    """
    视频模型 - 记录视频名称
    """

    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=255, description="视频标题")

    # 反向关系
    sources: fields.ReverseRelation["VideoSource"]
    play_links: fields.ReverseRelation["PlayLink"]

    class Meta:
        table = "videos"

    def __str__(self):
        return self.title


class VideoSource(Model):
    """
    视频来源模型 - 记录视频来源，一个视频对应多个来源
    """

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100, description="来源名称")

    # 外键关系：多个来源对应一个视频
    video: fields.ForeignKeyRelation[Video] = fields.ForeignKeyField(
        "models.Video", related_name="sources", description="关联的视频"
    )

    # 反向关系
    play_links: fields.ReverseRelation["PlayLink"]

    class Meta:
        table = "video_sources"
        unique_together = ("video", "name")  # 同一视频下来源名称不能重复

    def __str__(self):
        return f"{self.video.title} - {self.name}"


class PlayLink(Model):
    """
    播放链接模型 - 记录播放链接，包含视频和来源的外键
    """

    id = fields.IntField(primary_key=True)
    episode_index = fields.IntField(description="集数索引")
    url = fields.TextField(description="播放链接")

    # 外键关系
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
