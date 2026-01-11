import { readFileSync, writeFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// 获取当前文件所在目录
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 配置文件路径
const CONFIG_PATH = join(__dirname, "config.json");

// 默认配置
const DEFAULT_CONFIG = {
  crawlApiUrl: "https://caiji.dyttzyapi.com",
  danmuApiUrl: "https://novel-ninnetta-xiaohanys-f9773a5c.koyeb.app/api/douban",
};

/**
 * 读取配置
 */
export function getConfig() {
  try {
    if (existsSync(CONFIG_PATH)) {
      const data = readFileSync(CONFIG_PATH, "utf-8");
      return { ...DEFAULT_CONFIG, ...JSON.parse(data) };
    }
  } catch (error) {
    console.error("读取配置文件失败:", error.message);
  }
  return DEFAULT_CONFIG;
}

/**
 * 保存配置
 */
export function saveConfig(config) {
  try {
    const currentConfig = getConfig();
    const newConfig = { ...currentConfig, ...config };
    writeFileSync(CONFIG_PATH, JSON.stringify(newConfig, null, 2), "utf-8");
    console.log("✅ 配置保存成功");
    return true;
  } catch (error) {
    console.error("❌ 保存配置文件失败:", error.message);
    return false;
  }
}

/**
 * 重置为默认配置
 */
export function resetConfig() {
  try {
    writeFileSync(
      CONFIG_PATH,
      JSON.stringify(DEFAULT_CONFIG, null, 2),
      "utf-8"
    );
    console.log("✅ 配置已重置为默认值");
    return true;
  } catch (error) {
    console.error("❌ 重置配置失败:", error.message);
    return false;
  }
}
