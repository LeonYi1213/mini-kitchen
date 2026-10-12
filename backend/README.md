# 私有菜谱导入服务

使用现有公开小红书解析器下载真实视频，再抽取最多 80 帧，通过视觉模型提炼食材、备菜、步骤与耗时。只接受具体的小红书分享链接，无法读取内容就失败。视频超过 15 分钟拒绝处理；抽帧并非完整音频转写，完成后须核对菜谱。

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

服务只监听 127.0.0.1；iOS 通过自行配置的 HTTPS 反向代理访问。没有在本次工作中部署外网服务、创建模型账户或填写任何真实密钥。服务是单用户设计；同一访问令牌共享全部任务。多用户发行前应新增用户级认证、任务归属、配额、隐私与删除机制。

## 接口

所有接口都要求 `Authorization: Bearer <KITCHEN_SERVICE_TOKEN>`。

- `POST /imports`，JSON `{ "url": "https://xhslink.cn/o/..." }`：返回 202 和任务。
- `GET /imports/{id}`：查询。
- `DELETE /imports/{id}`：取消。已完成任务保持完成状态；运行中的外部请求可能执行到超时，但迟到结果不会写入已取消任务。

任务格式：`{id, status, completedStages, recipe?, message?}`。status 为 queued / running / completed / failed / cancelled。completedStages 为 0–4；对应完成读取、抽帧、模型整理、结构校验。客户端只在 completed 且菜谱有效后显示 100%。返回菜谱以 `xhs-<笔记ID>` 去重。用量未知为 null/适量。

本地 SQLite 持久化任务；重启时将中断任务标失败，供用户重试。单 worker、最多 3 个排队/运行任务，限制重复模型消耗。读取原视频后优先查找已导入 ID，重复笔记不调用模型。

临时视频与抽帧自动清理；任务结果保存在 SQLite。当前生成内容为结构化文本菜谱，没有把新抽帧持久化为图文资源；原生内置 18 道菜使用已打包真实配图。部署网络需允许小红书、视频 CDN 与配置的模型服务。

当前环境未提供模型密钥；已验证协议、错误处理和状态机，尚未完成真实在线端到端验收。

## 使用本机 Kimi API

支持直接读取已有的 `KIMI_API_KEY`；同时设置 `KIMI_BASE_URL`（中国区默认 `https://api.moonshot.cn/v1`）和 `KIMI_MODEL`。模型必须支持图片输入与 JSON 输出；不默认将任意 Kimi 文字模型当成视觉模型。示例见 `kimi.env.example`。若使用国际区或代理网关，以你现有的 Base URL 为准。也可继续使用 `OPENAI_*` 变量连接兼容服务。

Mac 的 Chromium 不再默认使用 Linux 路径。项目目录内执行 `npm install --no-save playwright` 与 `npx playwright install chromium` 后使用 Playwright 自带浏览器；或显式设置 `CHROMIUM_PATH`。仍需安装 ffmpeg/ffprobe。

Kimi Key 不填入 Xcode 配置。iOS 的 `IMPORT_SERVICE_URL` 指向这个菜谱服务，`IMPORT_SERVICE_TOKEN` 是私有服务令牌，不是 Kimi Key。当前没有使用你的真实密钥进行调用验收。
