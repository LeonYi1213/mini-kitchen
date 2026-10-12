# Mac 本地开发

从仓库根目录运行：

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm install --no-save --package-lock=false playwright
npx playwright install chromium
brew install ffmpeg
.venv/bin/python scripts/run_local_service.py
```

服务监听 `127.0.0.1:18080`。本机已配置 `.local/service.json`，启动器读取其中的 Kimi 模型、地址、钥匙串条目引用和小厨房独立服务令牌。模型密钥在运行时从 macOS 钥匙串读取，不写入项目。也支持环境变量 `KIMI_API_KEY`（或 `MOONSHOT_API_KEY`）、`KIMI_BASE_URL`、`KIMI_MODEL`、`KITCHEN_SERVICE_TOKEN`。TLS 使用系统信任证书，未关闭证书验证。

新 Mac 可通过上述环境变量启动，或自行创建 `.local/service.json`：

```json
{
  "KIMI_BASE_URL": "https://api.moonshot.cn/v1",
  "KIMI_MODEL": "your-vision-model",
  "KITCHEN_SERVICE_TOKEN": "your-own-random-service-token",
  "keychain_service": "your-existing-keychain-service",
  "keychain_account": "your-existing-keychain-account"
}
```

`.local/` 与 `ios/Config/Local.xcconfig` 都在 Git 忽略列表中，私有文件应设为 `chmod 600`。

## Xcode

打开 `ios/MiniKitchen.xcodeproj`，选择 MiniKitchen 和 iPhone/iPad 模拟器。本机私有 xcconfig 已为 Debug 模拟器配置 `http://localhost:18080` 及对应服务令牌。只有 Debug 模拟器允许 HTTP 回环地址，真机和 Release 仍要求 HTTPS。真机需要另行配置开发团队、签名及可访问的 HTTPS 服务地址；模拟器的 localhost 不适用于真机。

重启电脑后，重新执行上面的服务启动命令。没有设置开机自启动。

## 验证

```sh
# 一次真实图片请求，会使用模型 API 额度：
.venv/bin/python scripts/run_local_service.py --check-model
KITCHEN_RUN_HTTP_TESTS=1 .venv/bin/python -m unittest discover -s tests
xcodebuild test -project ios/MiniKitchen.xcodeproj -scheme MiniKitchen \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  -derivedDataPath DerivedData CODE_SIGNING_ALLOWED=NO
```

本次 Mac 验证已通过原生编译、iOS 测试、Python HTTP 测试和 Kimi 图片输入/JSON 输出请求。小红书真实链接的完整视频导入、真机与 iCloud 跨设备同步仍需单独验收。
