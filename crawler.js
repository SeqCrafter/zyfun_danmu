import {
  getOrCreateSource,
  getOrCreateVideo,
  addVideoSource,
  bulkUpsertEpisodes,
  getStats,
} from "./database.js";
import { getConfig } from "./config.js";

const API_ENDPOINT = "/api.php/provide/vod";

/**
 * 根据标题获取视频数据
 * @param {string} title - 视频标题
 * @returns {Promise<Array>} 视频数据数组
 */
export async function fetchVideosByTitle(title) {
  const config = getConfig();
  const API_HOST = config.crawlApiUrl;

  const params = new URLSearchParams({
    ac: "detail",
    wd: title,
  });

  const headers = {
    "User-Agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  };

  try {
    const response = await fetch(`${API_HOST}${API_ENDPOINT}?${params}`, {
      headers,
      signal: AbortSignal.timeout(30000), // 30秒超时
    });

    if (!response.ok) {
      console.error(`❌ HTTP错误! 状态: ${response.status}`);
      return [];
    }

    const data = await response.json();
    const videos = data.list || [];
    console.log(`📥 获取到 ${videos.length} 个视频`);
    return videos;
  } catch (error) {
    console.error(`❌ 获取视频失败: ${error.message}`);
    return [];
  }
}

/**
 * 解析播放来源和播放地址
 * @param {string} vod_play_from - 播放来源字符串
 * @param {string} vod_play_url - 播放地址字符串
 * @returns {Array} 解析后的播放数据
 */
export function parsePlayData(vod_play_from, vod_play_url) {
  const sources = vod_play_from.split("$$$");
  const urls = vod_play_url.split("$$$");

  const result = [];

  for (let i = 0; i < sources.length; i++) {
    if (i >= urls.length) {
      continue;
    }

    const sourceName = sources[i].trim();
    const episodesData = [];
    const episodeList = urls[i].split("#");

    for (const episodeStr of episodeList) {
      if (episodeStr.includes("$")) {
        const parts = episodeStr.split("$", 2);
        if (parts.length === 2) {
          const [title, url] = parts;
          // 只采集包含 m3u8 的视频链接
          if (url.toLowerCase().includes("m3u8")) {
            episodesData.push({
              title: title.trim(),
              url: url.trim(),
            });
          }
        }
      }
    }

    // 只添加有有效集数的来源
    if (episodesData.length > 0) {
      result.push({
        source: sourceName,
        episodes: episodesData,
      });
    }
  }

  return result;
}

/**
 * 保存视频数据到数据库
 * @param {Database} db - 数据库实例
 * @param {Object} videoData - 视频数据
 * @param {Object} sourceCache - Source缓存对象
 */
export async function saveVideoData(db, videoData, sourceCache) {
  const vod_douban_id = videoData.vod_douban_id || 0;

  // 过滤：只采集 vod_douban_id != 0 的视频
  if (!vod_douban_id || vod_douban_id === 0) {
    return;
  }

  const vod_id = videoData.vod_id;
  const title = videoData.vod_name || "";
  const type_name = videoData.type_name || "";
  const vod_play_from = videoData.vod_play_from || "";
  const vod_play_url = videoData.vod_play_url || "";

  if (!vod_play_from || !vod_play_url) {
    return;
  }

  // 解析播放数据
  const playData = parsePlayData(vod_play_from, vod_play_url);

  if (playData.length === 0) {
    return;
  }

  try {
    // 创建或获取视频记录
    const { id: videoId, created } = await getOrCreateVideo(db, {
      vod_id,
      title,
      type: type_name,
      douban_id: vod_douban_id,
    });

    if (created) {
      console.log(`  ✨ 新增视频: ${title} (豆瓣ID: ${vod_douban_id})`);
    } else {
      console.log(`  🔄 更新视频: ${title} (豆瓣ID: ${vod_douban_id})`);
    }

    // 收集所有剧集数据
    const allEpisodes = [];

    // 处理每个播放来源
    for (const sourceData of playData) {
      const sourceName = sourceData.source;
      const episodes = sourceData.episodes;

      // 获取或创建播放来源
      let sourceId;
      if (sourceCache[sourceName]) {
        sourceId = sourceCache[sourceName];
      } else {
        sourceId = await getOrCreateSource(db, sourceName);
        sourceCache[sourceName] = sourceId;
      }

      // 建立视频和来源的关联
      await addVideoSource(db, videoId, sourceId);

      // 准备剧集数据
      for (const episode of episodes) {
        allEpisodes.push({
          title: episode.title,
          url: episode.url,
          video_id: videoId,
          source_id: sourceId,
        });
      }
    }

    // 批量插入剧集
    if (allEpisodes.length > 0) {
      await bulkUpsertEpisodes(db, allEpisodes);
      console.log(`    📺 处理剧集: ${allEpisodes.length} 条`);
    }
  } catch (error) {
    console.error(`  ❌ 保存视频数据失败 (${title}): ${error.message}`);
  }
}

/**
 * 根据标题采集视频数据
 * @param {Database} db - 数据库实例
 * @param {string} title - 视频标题
 */
export async function crawlVideosByTitle(db, title) {
  const config = getConfig();

  console.log("\n" + "=".repeat(50));
  console.log(`🚀 开始采集视频数据: ${title}`);
  console.log(`📡 采集站: ${config.crawlApiUrl}`);
  console.log("=".repeat(50));

  // 创建 Source 缓存
  const sourceCache = {};

  // 获取视频数据
  const videos = await fetchVideosByTitle(title);

  if (videos.length === 0) {
    console.log("⚠️  未找到任何视频数据");
    return;
  }

  // 采集数据
  for (const videoData of videos) {
    await saveVideoData(db, videoData, sourceCache);
  }

  // 统计数据
  const stats = await getStats(db);

  console.log("\n" + "=".repeat(50));
  console.log("✅ 采集完成！");
  console.log(`📊 视频总数: ${stats.videos}`);
  console.log(`📊 来源总数: ${stats.sources}`);
  console.log(`📊 剧集总数: ${stats.episodes}`);
  console.log("=".repeat(50) + "\n");
}
