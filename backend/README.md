# 私有菜谱导入服务

使用现有公开小红书解析器下载真实视频，再抽取最多 80 帧，通过视觉模型提炼食材、备菜、步骤与耗时。支持用户主动上传 MP4/MOV 视频，以及可正常访问的小红书分享链接；无法读取内容就失败。视频超过 15 分钟拒绝处理；抽帧并非完整音频转写，完成后须核对菜谱。

## 运行

依赖 Python、Node、Playwright、Chromium、ffmpeg/ffprobe。Python 依赖见根目录 requirements.txt；Node 使用 `npm install playwright` 安装，`CHROMIUM_PATH` 指向实际 Chromium。服务调用的是已有 `scripts/import_video.py --browser`。

在进程环境配置（不要将真实值提交至仓库）：
- `KITCHEN_SERVICE_TOKEN`：随机的个人服务访问令牌，客户端使用同一值。
- `OPENAI_API_KEY`：模型密钥，仅服务端使用。
- `OPENAI_BASE_URL`：可选，默认 `https://api.openai.com/v1`，要求 HTTPS。
- `OPENAI_MODEL`：可选，默认 `gpt-4.1`，需支持图片与 JSON 输出。
- `KITCHEN_DATA_DIR`：可选，默认 `imports/service`，已忽略提交。

```sh
.venv/bin/python backend/server.py --port 8080
```

服务只监听 127.0.0.1；iOS 通过自行配置的 HTTPS 反向代理访问。2026-10-13 已按用户授权部署阿里云独立私有服务，入口为 `https://bubufriends.cn/minikitchen-api/`，具体运行配置见 `deploy/README.md`。服务是单用户设计；同一访问令牌共享全部任务。多用户发行前应新增用户级认证、任务归属、配额、隐私与删除机制。

## 接口

所有接口都要求 `Authorization: Bearer <KITCHEN_SERVICE_TOKEN>`。

- `POST /imports`，JSON `{ "url": "https://xhslink.cn/o/..." }`：返回 202 和任务。
- `POST /imports/video`：鉴权后的原始视频请求体（`video/mp4`、`video/quicktime` 或 `application/octet-stream`），必须提供 Content-Length，最大 200 MiB；返回 202 和任务。视频流式写入临时文件，SHA-256 内容摘要去重；只使用 MOV/MP4 解码器与本地文件协议，时长最多 15 分钟。处理结束、失败或取消后删除原视频；重启清理残留上传文件。上传与链接共用最多 3 个活跃任务。
- `GET /imports/{id}`：查询。
- `DELETE /imports/{id}`：取消。已完成任务保持完成状态；运行中的外部请求可能执行到超时，但迟到结果不会写入已取消任务。

任务格式：`{id, status, completedStages, recipe?, message?}`。status 为 uploading / queued / running / completed / failed / cancelled；上传接口在接收完成后才返回任务。completedStages 为 0–4；对应完成读取、抽帧、模型整理、结构校验。客户端只在 completed 且菜谱有效后显示 100%。返回菜谱以 `xhs-<笔记ID>` 去重。用量未知为 null/适量。

本地 SQLite 持久化任务；重启时将中断任务标失败，供用户重试。单 worker、最多 3 个排队/运行任务，限制重复模型消耗。读取原视频后优先查找已导入 ID，重复笔记不调用模型。

临时视频与未选中抽帧自动清理；任务结果保存在 SQLite。API 与原生内置菜谱使用相同图文结构：`cover`、逐项食材、`prep` / `cook`、对应 `timing`、`notes` 与 `illustrated_steps`。模型选择真实视频帧编号和食物/操作中心，服务端校验后裁成 8:5 横图并持久化封面及每个做法步骤的配图，并从 `cook` 原文生成图片关联，避免文字差异导致图片不显示。图片通过鉴权的 `GET /assets/...` 返回，iOS 下载到 Application Support，可离线查看；云同步仅保存图片引用。格式版本或图片缺失时重新生成，旧纯文字缓存不再直接返回。部署网络需允许小红书、视频 CDN 与配置的模型服务。

Mac 本地已复用钥匙串中的 Kimi API 配置并验证图片输入与 JSON 输出；完整小红书视频导入尚未端到端验收。参见 [Mac 本地开发](LOCAL_MAC.md)。

## 使用本机 Kimi API

支持直接读取已有的 `KIMI_API_KEY`；同时设置 `KIMI_BASE_URL`（中国区默认 `https://api.moonshot.cn/v1`）和 `KIMI_MODEL`。模型必须支持图片输入与 JSON 输出；不默认将任意 Kimi 文字模型当成视觉模型。示例见 `kimi.env.example`。若使用国际区或代理网关，以你现有的 Base URL 为准。也可继续使用 `OPENAI_*` 变量连接兼容服务。

Mac 的 Chromium 不再默认使用 Linux 路径。项目目录内执行 `npm install --no-save playwright` 与 `npx playwright install chromium` 后使用 Playwright 自带浏览器；或显式设置 `CHROMIUM_PATH`。仍需安装 ffmpeg/ffprobe。

Kimi Key 不填入 Xcode 配置。iOS 的 `IMPORT_SERVICE_URL` 指向这个菜谱服务，`IMPORT_SERVICE_TOKEN` 是私有服务令牌，不是 Kimi Key。本机 Kimi 的图片输入与 JSON 输出已通过真实请求验证。

## 图文格式回归

```sh
KITCHEN_RUN_HTTP_TESTS=1 .venv/bin/python -m unittest discover -s tests
```

`backend/recipe_format.py` 定义图文格式与抽帧引用校验。模型仍使用原有 `KIMI_MODEL` 和地址；格式不合格时最多再请求一次纠正，禁止用占位图或编造步骤补齐。已收藏的旧纯文字菜谱重新导入后，可在核对页选择“更新为图文菜谱”，保持相同 ID，不重复收藏。步骤变化后重置旧的步骤索引及勾选。

2026-10-13 使用用户提供的牛肋条烩饭分享链接，以本机 `kimi-k3` 完成真实图文导入验证。原视频约 197 秒，未独立转写音频。抽帧位置标为约数；模型提取内容仍保留用量与耗时的不确定性。

## 视频导入（1.0 build 2）

iOS 支持相册系统选择器和文件选择器，视频上传前提示处理方式。用户核对生成结果后收藏；原视频不持久保存，配图下载到本机。视频导入 ID 使用 `video-<SHA256前24位>`，来源显示“用户上传的视频”，不会冒充小红书笔记。现有 `xhs-` 图片和菜谱保持兼容。
