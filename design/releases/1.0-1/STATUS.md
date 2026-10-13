# 小厨房 1.0 (1) TestFlight 发布记录

2026-10-13，首版已在 TestFlight 开放内部测试，邀请已发送至账户持有人。

- GitHub 项目 mini-kitchen；独立 Bundle ID `com.minikitchen.app` 已注册，iCloud KVS 能力已开启。
- 真机 Release 签名归档通过。新增不透明 App Store 图标、隐私清单与版本设置；最终归档已使用经过验证的 HTTPS 服务地址，并完成严格验签。
- XCTest 10 项通过；本机 Python 37 项通过；阿里云 Python 37 项通过。
- 阿里云独立目录 `/opt/minikitchen`，systemd 单元 `minikitchen`，监听 `127.0.0.1:18320`，独立用户与 SQLite 数据。
- 服务器 Kimi `kimi-k3` 真实图片输入与 JSON 输出验证通过，密钥只留在权限为 0600 的服务环境文件。
- 同一牛肋条分享链接在阿里云被小红书拒绝，返回可见错误“IP存在风险 / 300012”。不绕过原平台限制；读取失败不调用付费模型。新增固定错误说明，不回传底层日志或分享令牌。
- 用户明确授权临时共享步步域名；独立入口 `https://bubufriends.cn/minikitchen-api/` 已部署，严格 TLS 验证及未鉴权 401 / 正确令牌 404 探针通过。
- `iwengua.com` DNS 指向服务器，但外网返回阿里云 `Non-compliance ICP Filing` 403，ACME 验证失败。没有禁用 TLS 校验或部署无效证书。
- App Store Connect 应用记录 `6822363240`，名称“小厨房·今天吃什么”。独立内部测试组“小厨房个人测试”已添加账号本人，不开公开链接。
- `xcodebuild -exportArchive` 返回 `EXPORT SUCCEEDED`，2026-10-13 23:24:58 上传成功。

最终确认：`processingState=VALID`，`internalBuildState=IN_BETA_TESTING`，本人测试员状态 `INVITED`。

- 构建 ID：`270285f9-23b9-449c-aae6-11f6c4cf8299`。
- 内部组 ID：`c80746e2-9c48-4a0a-af24-cb7aad6af684`。
- 外部测试未开启；真机安装与使用反馈仍待用户验证。
