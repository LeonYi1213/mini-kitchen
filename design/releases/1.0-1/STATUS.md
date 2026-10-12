# 小厨房 1.0 (1) 发布准备

2026-10-13，尚未上传 TestFlight，不能下载。

- GitHub 项目 mini-kitchen；独立 Bundle ID `com.minikitchen.app` 已注册，iCloud KVS 能力已开启。
- 真机 Release 签名归档通过。新增不透明 App Store 图标、隐私清单与版本设置；最终归档需在 HTTPS 服务地址确定后重新生成。
- XCTest 10 项通过；本机 Python 37 项通过；阿里云 Python 37 项通过。
- 阿里云独立目录 `/opt/minikitchen`，systemd 单元 `minikitchen`，监听 `127.0.0.1:18320`，独立用户与 SQLite 数据。
- 服务器 Kimi `kimi-k3` 真实图片输入与 JSON 输出验证通过，密钥只留在权限为 0600 的服务环境文件。
- 同一牛肋条分享链接在阿里云被小红书拒绝，返回可见错误“IP存在风险 / 300012”。不绕过原平台限制；读取失败不调用付费模型。新增固定错误说明，不回传底层日志或分享令牌。
- 用户明确授权临时共享步步域名；独立入口 `https://bubufriends.cn/minikitchen-api/` 已部署，严格 TLS 验证及未鉴权 401 / 正确令牌 404 探针通过。
- `iwengua.com` DNS 指向服务器，但外网返回阿里云 `Non-compliance ICP Filing` 403，ACME 验证失败。没有禁用 TLS 校验或部署无效证书。
- 首次 App Store Connect 应用记录尚未创建，等待可用网页登录。独立内部测试组仅添加账号本人，不开公开链接。

完成条件：可用 HTTPS 入口 → 真机发布配置 → 最新归档及验签 → Apple 上传 → processingState=VALID → 本人内部组 IN_BETA_TESTING。
