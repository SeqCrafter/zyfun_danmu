import Fastify from "fastify";
import { initDatabase, queryVideoByUrl } from "./database.js";
import { crawlVideosByTitle } from "./crawler.js";
import { getConfig, saveConfig, resetConfig } from "./config.js";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// 获取当前文件所在目录
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const fastify = Fastify({
  logger: true,
});

// 初始化数据库
const db = initDatabase();

//function part

async function url2douban(url) {
  try {
    // 直接调用数据库查询函数，不需要通过HTTP请求
    const result = await queryVideoByUrl(db, url);

    if (!result) {
      return {
        douban_id: 0,
        episode_title: "",
        video_title: "",
        source_name: "",
      };
    }

    return result;
  } catch (error) {
    console.error(error);
    return {
      douban_id: 0,
      episode_title: "",
      video_title: "",
      source_name: "",
    };
  }
}

async function douban2danmu(douban_id, episode_number) {
  const config = getConfig();
  const danmuApiUrl = config.danmuApiUrl;

  try {
    const response = await fetch(
      `${danmuApiUrl}?douban_id=${douban_id}&episode_number=${episode_number}`
    );
    if (!response.ok) {
      console.log(`HTTP error! status: ${response.status}`);
      return {
        code: 1,
        name: "get danmu error",
        danmu: 0,
        danmuku: [],
      };
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(error);
    return {
      code: 1,
      name: "get danmu error",
      danmu: 0,
      danmuku: [],
    };
  }
}

function extractEpisodeNumberFromTitle(episodeTitle) {
  // 匹配格式：第1集、第01集、第10集等
  const chineseMatch = episodeTitle.match(/第(\d+)集/);
  if (chineseMatch) {
    return parseInt(chineseMatch[1], 10);
  }
  // 匹配格式：EP01、EP1、E01、E1等
  const epMatch = episodeTitle.match(/[Ee][Pp]?(\d+)/);
  if (epMatch) {
    return parseInt(epMatch[1], 10);
  }
  // 匹配格式：01、1（纯数字，通常在标题开头或结尾）
  const numberMatch = episodeTitle.match(/(?:^|\s)(\d+)(?:\s|$)/);
  if (numberMatch) {
    return parseInt(numberMatch[1], 10);
  }
  return null;
}

//main function

async function getDanmu(url) {
  const douban_info = await url2douban(url);
  if (douban_info.douban_id === 0) {
    return {
      code: 1,
      name: "get douban info error from videourl.zeabur.app",
      danmu: 0,
      danmuku: [],
    };
  }
  const episode_number = extractEpisodeNumberFromTitle(
    douban_info.episode_title
  );
  if (episode_number === null) {
    return {
      code: 1,
      name: "extract episode number error",
      danmu: 0,
      danmuku: [],
    };
  }
  const danmu_info = await douban2danmu(
    douban_info.douban_id.toString(),
    episode_number.toString()
  );
  if (danmu_info.code === 1) {
    return {
      code: 1,
      name: "get danmu error from dmkus.zeabur.app",
      danmu: 0,
      danmuku: [],
    };
  }
  return danmu_info;
}

// 根路径返回 HTML 页面
fastify.get("/", async function (request, reply) {
  const html = readFileSync(join(__dirname, "index.html"), "utf-8");
  return reply.type("text/html").send(html);
});

// 弹幕接口（保留原有功能）
fastify.get("/api/comment", async function (request, reply) {
  const danmu_info = await getDanmu(request.query.url);
  return reply.send(danmu_info);
});

// 视频查询接口
fastify.get("/api/query", async function (request, reply) {
  const { url } = request.query;

  if (!url) {
    return reply.status(400).send({
      error: "Bad Request",
      message: "缺少必需参数: url",
    });
  }

  try {
    const result = await queryVideoByUrl(db, url);

    if (!result) {
      return reply.status(404).send({
        error: "Not Found",
        message: `未找到对应的视频信息，播放地址: ${url}`,
      });
    }

    return reply.send({
      douban_id: result.douban_id,
      episode_title: result.episode_title,
      video_title: result.video_title,
      source_name: result.source_name,
    });
  } catch (error) {
    console.error("查询视频信息失败:", error);
    return reply.status(500).send({
      error: "Internal Server Error",
      message: "查询视频信息失败",
    });
  }
});

// 视频爬取接口（异步后台执行）
fastify.post("/api/crawl/:title", async function (request, reply) {
  const { title } = request.params;

  if (!title) {
    return reply.status(400).send({
      error: "Bad Request",
      message: "缺少必需参数: title",
    });
  }

  // 立即返回响应
  reply.send({
    status: "started",
    message: "已开始采集视频信息，任务将在后台执行",
    task: "crawl_by_title",
  });

  // 后台异步执行爬取任务（不等待）
  crawlVideosByTitle(db, title).catch((err) => {
    console.error("❌ 爬取任务失败:", err);
  });
});

// 获取配置接口
fastify.get("/api/config", async function (request, reply) {
  try {
    const config = getConfig();
    return reply.send(config);
  } catch (error) {
    console.error("获取配置失败:", error);
    return reply.status(500).send({
      error: "Internal Server Error",
      message: "获取配置失败",
    });
  }
});

// 保存配置接口
fastify.post("/api/config", async function (request, reply) {
  try {
    const { crawlApiUrl, danmuApiUrl } = request.body;

    if (!crawlApiUrl || !danmuApiUrl) {
      return reply.status(400).send({
        error: "Bad Request",
        message: "缺少必需参数",
      });
    }

    const success = saveConfig({ crawlApiUrl, danmuApiUrl });

    if (success) {
      return reply.send({
        success: true,
        message: "配置保存成功",
      });
    } else {
      return reply.status(500).send({
        error: "Internal Server Error",
        message: "配置保存失败",
      });
    }
  } catch (error) {
    console.error("保存配置失败:", error);
    return reply.status(500).send({
      error: "Internal Server Error",
      message: "保存配置失败",
    });
  }
});

// 重置配置接口
fastify.post("/api/config/reset", async function (request, reply) {
  try {
    const success = resetConfig();

    if (success) {
      return reply.send({
        success: true,
        message: "配置已重置为默认值",
      });
    } else {
      return reply.status(500).send({
        error: "Internal Server Error",
        message: "重置配置失败",
      });
    }
  } catch (error) {
    console.error("重置配置失败:", error);
    return reply.status(500).send({
      error: "Internal Server Error",
      message: "重置配置失败",
    });
  }
});

const start = async () => {
  try {
    await fastify.listen({ port: 8080, host: "::" });
    console.log("🚀 Server is running on http://localhost:8080");
  } catch (err) {
    console.error("🚨 Server startup failed:", err);
    fastify.log.error(err);
    process.exit(1);
  }
};

// 停止服务
const stop = async () => {
  try {
    // 停止主服务器
    await fastify.server.close();
    console.log("🛑 所有服务已优雅停止");
  } catch (err) {
    fastify.log.error(`停止服务器时发生错误:${err.message}`);
  }
};

export { start, stop };

start();
