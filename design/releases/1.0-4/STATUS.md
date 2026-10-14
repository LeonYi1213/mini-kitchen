# 小厨房 1.0 (4)

新增24道本机读取原文、图解和视频字幕后整理的菜谱，内置目录从18道增至42道。图片与完整菜谱随包保存，无需再次调用链接导入API。保留既有视频上传、烹饪进度和历史记录功能。

应用：6822363240，Bundle ID：com.minikitchen.app。目标测试组：小厨房个人测试。

## 验证

- 11项XCTest、46项Python测试全部通过。
- Release归档签名成功；归档内42个唯一菜谱及全部封面、步骤图片存在。
- 每道新菜谱的烹饪步骤与图文步骤文本一一对应；来源记录见 design/releases/1.0-4/recipes.json。
- 本次仅更新App内置资源，未部署或修改云端服务。
- iPhone真实设备更新、原有进度保留与实际使用仍待TestFlight验收。

## 发布状态

2026-10-14上传成功，Apple processingState=VALID，internalBuildState=IN_BETA_TESTING。已关联“小厨房个人测试”内部组，未开启公共链接。

构建ID：a4ee9d6f-3b0f-498f-9319-fd9e56287b51。实时核验记录见 verification.json。
