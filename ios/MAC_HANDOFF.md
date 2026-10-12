# 导入 Mac 本地项目

本次交接使用 `MiniKitchen.bundle`：完整的本地 Git 快照，没有推送 GitHub。包含原生工程、菜谱图片、设计稿、后台服务与测试；不包含 .env、私有 Xcode 配置、视频下载、依赖目录或密钥。

## 已有“小厨房”本地项目

把 `MiniKitchen.bundle` 与 `install_mini_kitchen.py` 下载到同一目录，执行以下命令，将目标路径替换为自己的项目目录：

```sh
python3 ~/Downloads/install_mini_kitchen.py '/你的本地路径/小厨房'
open '/你的本地路径/小厨房/ios/MiniKitchen.xcodeproj'
```

脚本会保留本地 `.git`、`.env*`、`ios/Config/Local.xcconfig`；相同文件不写入，发生变化的文件先备份到项目旁的 `小厨房.before-import-时间-*` 目录。不会删除本地额外文件，也不会自动提交或推送。本地代码如有不同实现，导入后通过 git diff 和备份核对合并。

## 新目录直接 clone

```sh
git clone ~/Downloads/MiniKitchen.bundle ~/Developer/mini-kitchen
open ~/Developer/mini-kitchen/ios/MiniKitchen.xcodeproj
```

这里 origin 指向下载的 bundle；不会自动把远程地址设为 GitHub，更不会覆盖远端分支。

## 本地 Kimi

服务已支持 `KIMI_API_KEY`、`KIMI_BASE_URL`、`KIMI_MODEL` 环境变量。保持已有密钥在本机，指定支持图片理解和 JSON 输出的模型名称；参考 backend/kimi.env.example。API Key 不进入 App，客户端仍连接私有菜谱服务。不同 Kimi 网关的模型名和功能可能不同，真实兼容性需用你的配置验证。

先在 Xcode 打开工程，选择模拟器验证离线功能；真实 AI 导入和 iCloud 配置参见 ios/README.md 与 backend/README.md。此快照在 Linux 做过静态与 Python 检查，尚未在 Xcode 编译。
