import sqlite3 from "sqlite3";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// 获取当前文件所在目录
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 数据库文件路径
const DB_PATH = join(__dirname, "db.sqlite3");

/**
 * 初始化数据库连接和表结构
 */
export function initDatabase() {
  const db = new sqlite3.Database(DB_PATH);

  console.log("📦 初始化数据库表结构...");

  // 启用外键约束
  db.run("PRAGMA foreign_keys = ON");

  // 创建 video 表
  db.run(`
    CREATE TABLE IF NOT EXISTS video (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      vod_id INTEGER NOT NULL,
      title VARCHAR(255) NOT NULL,
      type VARCHAR(100) NOT NULL,
      douban_id INTEGER UNIQUE NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // 创建 video 表索引
  db.run(`CREATE INDEX IF NOT EXISTS idx_video_douban_id ON video(douban_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_video_vod_id ON video(vod_id)`);

  // 创建 source 表
  db.run(`
    CREATE TABLE IF NOT EXISTS source (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name VARCHAR(100) UNIQUE NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // 创建 episode 表
  db.run(`
    CREATE TABLE IF NOT EXISTS episode (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title VARCHAR(255) NOT NULL,
      url VARCHAR(500) UNIQUE NOT NULL,
      video_id INTEGER NOT NULL,
      source_id INTEGER NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (video_id) REFERENCES video(id),
      FOREIGN KEY (source_id) REFERENCES source(id)
    )
  `);

  // 创建 episode 表索引
  db.run(`CREATE INDEX IF NOT EXISTS idx_episode_url ON episode(url)`);
  db.run(
    `CREATE INDEX IF NOT EXISTS idx_episode_video_source ON episode(video_id, source_id)`
  );

  // 创建 video_source 关联表
  db.run(`
    CREATE TABLE IF NOT EXISTS video_source (
      video_id INTEGER NOT NULL,
      source_id INTEGER NOT NULL,
      PRIMARY KEY (video_id, source_id),
      FOREIGN KEY (video_id) REFERENCES video(id),
      FOREIGN KEY (source_id) REFERENCES source(id)
    )
  `);

  console.log("✅ 数据库表结构初始化完成");

  return db;
}

/**
 * 根据 URL 查询视频信息
 * @param {Database} db - 数据库实例
 * @param {string} url - 视频播放地址
 * @returns {Promise<Object|null>} 返回视频信息或null
 */
export function queryVideoByUrl(db, url) {
  return new Promise((resolve, reject) => {
    const sql = `
      SELECT 
        v.douban_id,
        e.title as episode_title,
        v.title as video_title,
        s.name as source_name
      FROM episode e
      INNER JOIN video v ON e.video_id = v.id
      INNER JOIN source s ON e.source_id = s.id
      WHERE e.url = ?
    `;

    db.get(sql, [url], (err, row) => {
      if (err) {
        reject(err);
      } else {
        resolve(row || null);
      }
    });
  });
}

/**
 * 获取或创建 Source
 * @param {Database} db - 数据库实例
 * @param {string} name - 来源名称
 * @returns {Promise<number>} source_id
 */
export function getOrCreateSource(db, name) {
  return new Promise((resolve, reject) => {
    // 先尝试查询
    db.get("SELECT id FROM source WHERE name = ?", [name], (err, row) => {
      if (err) {
        reject(err);
        return;
      }

      if (row) {
        resolve(row.id);
      } else {
        // 不存在则创建
        db.run("INSERT INTO source (name) VALUES (?)", [name], function (err) {
          if (err) {
            reject(err);
          } else {
            resolve(this.lastID);
          }
        });
      }
    });
  });
}

/**
 * 获取或创建 Video
 * @param {Database} db - 数据库实例
 * @param {Object} videoData - 视频数据
 * @returns {Promise<Object>} {id, created} - 返回视频ID和是否新创建
 */
export function getOrCreateVideo(db, videoData) {
  return new Promise((resolve, reject) => {
    const { vod_id, title, type, douban_id } = videoData;

    // 先尝试查询
    db.get(
      "SELECT id FROM video WHERE douban_id = ?",
      [douban_id],
      (err, row) => {
        if (err) {
          reject(err);
          return;
        }

        if (row) {
          // 更新现有视频
          const updateSql = `
            UPDATE video 
            SET vod_id = ?, title = ?, type = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE douban_id = ?
          `;
          db.run(updateSql, [vod_id, title, type, douban_id], (err) => {
            if (err) {
              reject(err);
            } else {
              resolve({ id: row.id, created: false });
            }
          });
        } else {
          // 不存在则创建
          const insertSql = `
            INSERT INTO video (vod_id, title, type, douban_id) 
            VALUES (?, ?, ?, ?)
          `;
          db.run(insertSql, [vod_id, title, type, douban_id], function (err) {
            if (err) {
              reject(err);
            } else {
              resolve({ id: this.lastID, created: true });
            }
          });
        }
      }
    );
  });
}

/**
 * 添加 video-source 关联
 * @param {Database} db - 数据库实例
 * @param {number} videoId - 视频ID
 * @param {number} sourceId - 来源ID
 * @returns {Promise<void>}
 */
export function addVideoSource(db, videoId, sourceId) {
  return new Promise((resolve, reject) => {
    const sql = `
      INSERT OR IGNORE INTO video_source (video_id, source_id) 
      VALUES (?, ?)
    `;
    db.run(sql, [videoId, sourceId], (err) => {
      if (err) {
        reject(err);
      } else {
        resolve();
      }
    });
  });
}

/**
 * 创建或更新 Episode
 * @param {Database} db - 数据库实例
 * @param {Object} episodeData - 剧集数据
 * @returns {Promise<void>}
 */
export function upsertEpisode(db, episodeData) {
  return new Promise((resolve, reject) => {
    const { title, url, video_id, source_id } = episodeData;

    const sql = `
      INSERT INTO episode (title, url, video_id, source_id) 
      VALUES (?, ?, ?, ?)
      ON CONFLICT(url) DO UPDATE SET 
        title = excluded.title,
        video_id = excluded.video_id,
        source_id = excluded.source_id
    `;

    db.run(sql, [title, url, video_id, source_id], (err) => {
      if (err) {
        reject(err);
      } else {
        resolve();
      }
    });
  });
}

/**
 * 批量插入剧集（使用事务）
 * @param {Database} db - 数据库实例
 * @param {Array} episodes - 剧集数组
 * @returns {Promise<void>}
 */
export function bulkUpsertEpisodes(db, episodes) {
  return new Promise((resolve, reject) => {
    db.serialize(() => {
      db.run("BEGIN TRANSACTION");

      const sql = `
        INSERT INTO episode (title, url, video_id, source_id) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET 
          title = excluded.title,
          video_id = excluded.video_id,
          source_id = excluded.source_id
      `;

      const stmt = db.prepare(sql);

      for (const episode of episodes) {
        stmt.run(
          [episode.title, episode.url, episode.video_id, episode.source_id],
          (err) => {
            if (err) {
              console.error("插入剧集失败:", err);
            }
          }
        );
      }

      stmt.finalize((err) => {
        if (err) {
          db.run("ROLLBACK");
          reject(err);
        } else {
          db.run("COMMIT", (err) => {
            if (err) {
              reject(err);
            } else {
              resolve();
            }
          });
        }
      });
    });
  });
}

/**
 * 获取数据库统计信息
 * @param {Database} db - 数据库实例
 * @returns {Promise<Object>}
 */
export function getStats(db) {
  return new Promise((resolve, reject) => {
    const stats = {};

    db.get("SELECT COUNT(*) as count FROM video", (err, row) => {
      if (err) {
        reject(err);
        return;
      }
      stats.videos = row.count;

      db.get("SELECT COUNT(*) as count FROM source", (err, row) => {
        if (err) {
          reject(err);
          return;
        }
        stats.sources = row.count;

        db.get("SELECT COUNT(*) as count FROM episode", (err, row) => {
          if (err) {
            reject(err);
          } else {
            stats.episodes = row.count;
            resolve(stats);
          }
        });
      });
    });
  });
}
