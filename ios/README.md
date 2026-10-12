# 小厨房 · 原生 iOS / iPadOS App

SwiftUI Universal App，iOS / iPadOS 17+。打开 `MiniKitchen.xcodeproj`，选择 `MiniKitchen` scheme 和模拟器，运行即可使用 18 道离线图文菜谱。没有 CocoaPods、SPM 或 WebView 依赖。

## 已实现

- 沿用 `web/design/ios` 的暖白背景、深绿按钮、圆角菜谱卡片、底部四项导航和 iPad 侧栏；系统负责状态栏、安全区与字号，不绘制假的状态栏。
- 首次打开不预选菜；空首页以紧凑列表展示常做的菜，按制作次数降序排列，每行显示“已做 X 次”；次数相同时保留菜谱原顺序。最后一步点击“做好了”记录一次，同一餐反复完成不会重复计数；开始新的一餐保留历史。旧版本没有历史记录的菜从 0 次开始。
- 菜名/食材搜索、30 分钟内筛选、本餐筛选、查看详情、加入/移除本餐。
- 分菜查看与勾选备菜食材，缺失用量显示适量。
- 手机横向滑动切换菜谱；宽屏横向并排展示，空间不足时滚动。用量在 sheet 中查看，保留当前步骤。
- 每道菜独立步骤、返回上一步、完成、暂停/恢复计时；绝对截止时间保证后台或重启后继续计算，不会自动跳步。当前没有锁屏提醒或后台通知。
- 多菜优先级按当前步骤、等待时间和到时计时器更新；这是本地调度规则。
- 本地原子写入；开始新的一餐需要确认，清除本餐步骤和计时，不删除菜谱。
- 配置签名与 iCloud Key-value storage 后，同一 Apple 账户同步本餐、分菜步骤、分菜备料勾选和新收藏。步骤与备料分键，避免相互覆盖；同键以较新时间戳合并，整个选菜列表以最近修改为准。同步并非实时，不显示虚假的已同步状态。个人小规模使用受系统 1 MB 总容量/单键大小约束，超额仍保留本机数据。
- 链接导入：系统 PasteButton、四阶段真实任务进度、取消、重试、核对与收藏、规范化 ID 去重；不使用模拟进度。`minikitchen://import?text=...` 可打开导入入口，当前没有 Share Extension。
- 用户界面无“原型”“演示”“双设备设计”“服务待接入”等开发说明。

## 在 Mac 运行

1. 使用 Xcode 16+ 打开 `ios/MiniKitchen.xcodeproj`。
2. 运行在 iPhone / iPad 模拟器；真机需在 Signing & Capabilities 选择自己的开发团队、唯一 Bundle ID，启用 iCloud → Key-value storage。两台设备需使用同一签名标识与 iCloud 账户。
3. ⌘U 运行 `MiniKitchenTests`。跨设备同步需两台登录同一账户的真机验证。

`Config/Local.xcconfig` 是可选私有配置，已忽略提交。没有 AI 配置时，离线功能仍可使用；发起生成会显示可重试的失败状态，不会伪造结果。

## AI 服务配置

见 [`../backend/README.md`](../backend/README.md)。将 `Config/Local.xcconfig.example` 复制为 `Config/Local.xcconfig`，填写 HTTPS 服务地址与私有服务访问令牌。模型 API Key 只配置在服务端。

这是个人自用的单用户服务模式。App 内的服务访问令牌可被设备持有人提取，不是面向公众发行的认证方案；公开发行前需要替换为用户登录与短期凭证。代码中不包含任何真实密钥。

## 验证与维护

```sh
python scripts/bundle_ios_recipes.py
python scripts/generate_xcode_project.py
.venv/bin/pip install -r ios/requirements-check.txt
.venv/bin/python scripts/check_ios.py
python -m unittest discover -s tests
KITCHEN_RUN_HTTP_TESTS=1 python -m unittest discover -s tests
# macOS / Xcode:
xcodebuild test -project ios/MiniKitchen.xcodeproj -scheme MiniKitchen \
  -destination 'platform=iOS Simulator,name=iPhone 16' CODE_SIGNING_ALLOWED=NO
```

`check_ios.py` 检查 Swift 语法树、工程资源引用、配置、菜谱与图片，不代替 Swift 类型检查或 Xcode 编译。仓库已提供 macOS CI，尚需实际触发。

现已在 Mac / Xcode 26.3 完成模拟器编译和单元测试，并接入本机 Kimi 服务；启动方式见 [Mac 本地开发](../backend/LOCAL_MAC.md)。一比一视觉验收、Dynamic Type、横竖屏、iPad 分屏、VoiceOver、系统通知与云同步仍需在 Apple 设备上验收。没有生成真机签名安装包或提交 App Store。
