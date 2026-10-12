# 小厨房 TestFlight

独立 Bundle ID `com.minikitchen.app`，团队连接从本机 `.codex/memories/app-delivery-connections.json` 读取。不保存 Apple 密码或私钥。

1. 首次在 App Store Connect 网站创建 iOS 应用，SKU `minikitchen-ios-001`、简体中文；记录名称优先“小厨房”。
2. `ruby scripts/app-store-connect/prepare-private-beta.rb` 填入真实 App ID，创建“小厨房个人测试”内部组。只添加账号本人作为测试者。
3. 在忽略提交的 `ios/Config/Local.xcconfig` 设置 Release 真机的 HTTPS 服务地址和小厨房服务令牌；模型 Key 仅在服务器环境文件。
4. 运行 XCTest、Python 测试，完成云端 HTTPS 鉴权、模型与导入测试；如原平台限制访问，记录限制，不能声称端到端可用。
5. `xcodebuild archive`，之后 `python3 scripts/app-store-connect/upload.py <archive>`。
6. 等待 Apple processingState 为 VALID，运行 `ruby scripts/app-store-connect/finish-private-beta.rb`，核实本人测试组和 IN_BETA_TESTING 后才能报告可下载。

不创建公共测试链接、不邀请其他项目测试者、不提交正式 App Store 审核。图标由 `generate-icon.swift` 生成，保持不透明 RGB。
