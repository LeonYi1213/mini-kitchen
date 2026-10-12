# 阿里云私有导入服务

运行目录 `/opt/minikitchen/current` 指向独立版本目录，数据 `/opt/minikitchen/data`；进程以 `minikitchen` 用户运行，仅监听 `127.0.0.1:18320`。

依赖：Python 3.11 venv、`requirements.txt`、锁定的 Node 依赖；Alibaba Cloud Linux 使用发行版 `chromium-headless`，`CHROMIUM_PATH=/usr/lib64/chromium-browser/headless_shell`。ffmpeg/ffprobe 可执行文件以独立 `/opt/minikitchen/bin` 符号链接加入 PATH。

`/opt/minikitchen/service.env` 为 root:root 0600，配置 `KITCHEN_SERVICE_TOKEN`、`KITCHEN_DATA_DIR`、`CHROMIUM_PATH`、`KIMI_API_KEY`、`KIMI_BASE_URL`、`KIMI_MODEL`。不得提交实际值。systemd 模板见 `minikitchen.service`。

用户已明确授权临时共享域名，HTTPS 入口为 `https://bubufriends.cn/minikitchen-api/`；严格 TLS 校验、401/404 鉴权探针与 Kimi 图片/JSON 请求已验证。反代片段见 `minikitchen.locations`，仅加入 HTTPS 域名服务器块。公网仅开放 nginx，不暴露 Python 端口。

小红书可能限制数据中心 IP，当前服务器对牛肋条链接返回 300012；这与 Kimi 的连通性无关，不应以重试、替换输出或伪造菜谱掩盖。遇到原站访问限制时不绕过。
