# Zyfun 弹幕插件

## 插件原理描述

zyfun(ZyPlayer)的弹幕获取方式为在你设置的接口上拼接视频的播放地址，那么对于非官方源来说，必须根据地址反向获取视频的豆瓣 id 和对应的集数，然后根据豆瓣 id 和集数获取弹幕。
因此，本插件的作用是，首先用户手动输入需要观看的视频标题，然后本插件会从用户设置的采集网站抓取视频链接保存到本地。当用户播放该视频时，本插件负责根据地址获取视频的豆瓣 id 和对应的集数，然后转发到第三方弹幕接口获取弹幕。因此，本插件需要一个额外的根据 douban_id 和集数获取弹幕的接口和采集站接口

## 依赖接口

- 采集站接口(例如电影天堂)： https://dyttzy.tv
- 弹幕接口(支持 douban_id 和集数获取弹幕),可自行部署该项目：
  - [SeqCrafter/fetch_danmu](https://github.com/SeqCrafter/fetch_danmu)
  - [SeqCrafter/danmu_api](https://github.com/SeqCrafter/danmu_api)

## 插件安装

1. 下载本仓库然后解压
2. 打开软件的插件页面，点击安装按钮，会弹出安装步骤
3. 将下载的插件包复制到安装目录
4. 填入插件名(zyfun_danmu)来安装本插件
5. 点击启动按钮，插件就会启动

## 插件使用

插件自带一个前端界面，插件启动后访问`http://localhost:8080`即可访问到插件的前端界面。

![](https://tncache1-f1.v3mh.com/image/2026/01/11/a17d1c44266a5e21707b5822b9efb16d.png)

1. 首先在系统设置里填入采集站 API 地址和弹幕 API 地址，然后点击保存按钮。
2. 然后把你想要看的影视剧名称输入视频采集框，点击开始采集按钮，插件会自动从采集站获取视频链接并保存到本地。
3. 然后把弹幕接口`http://localhost:8080/api/comment?url=`填入 zyfun 的弹幕接口设置中即可。

![](https://tncache1-f1.v3mh.com/image/2026/01/11/01619f53477e93097bb2f5c5ee2b16c0.png)
