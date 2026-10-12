# 小厨房

原生 iPhone / iPad App 已开始实现，入口是 [`ios/MiniKitchen.xcodeproj`](ios/MiniKitchen.xcodeproj)。运行与功能说明见 [`ios/README.md`](ios/README.md)，AI 导入服务见 [`backend/README.md`](backend/README.md)。当前云环境未运行 Xcode；原生编译、视觉和真机验收待完成。

以下保留此前网页版本的使用说明。

三道菜并排看，手机左右滑动；每道菜独立备菜 / 烹饪 / 完成，步骤与食材清单可勾选，刷新保留进度。支持菜谱 JSON 批量导入、备份导出。首次打开的三道菜为示例。

## 启动

```sh
python server.py --port 8000
```

本地浏览器访问 8000 端口。应用仅监听本机，数据存于当前浏览器，不跨设备同步。清除浏览器数据会丢失记录，请导出备份。

## 视频提取 skill

阅读 `skills/xiaohongshu-recipe/SKILL.md`。这是仓库内的 agent skill 文档，尚未安装为全局插件。让具备视频理解能力的 agent 按此文档解析、提炼并输出 JSON，再从网页导入。

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
export PATH="$PWD/.venv/bin:$PATH"
python scripts/import_video.py '完整小红书分享链接'
```

需 ffmpeg（当前环境已提供）。网页无后端模型调用；不会把未解析的视频伪装成菜谱。遇到访问限制可提供自行获得的视频或字幕。JSON 格式见 skill。下载内容保存在忽略提交的 imports/，其中元数据可能含临时访问参数，不要提交或分享。

## 验证

```sh
python -m unittest discover -s tests
node --check web/app.js
```

浏览器交互测试（需 Playwright 与 Chromium；当前云环境已提供）：`node tests/browser.cjs`。可通过 CHROMIUM_PATH 指定浏览器路径。

若 HTTP 解析跳到登录页，尝试正常浏览器路径：`.venv/bin/python scripts/import_video.py "完整分享链接" --browser`。需 Playwright 与 Chromium；当前云环境已提供。已用青椒排骨分享笔记验证浏览器能读取公开视频。

多菜优先级：选择至少两道菜时，按长等待菜先准备、已下锅步骤先处理、叶菜最后炒的本地规则给出建议。勾选步骤会更新建议；点击等待步骤的计时按钮后，该菜等待期间优先推荐其他菜。时间为保守估算，不能代替熟度判断。

菜谱可提供 `timing: {prep: [{min: 2, max: 4}], cook: [{min: 40, max: 50, wait: true}]}`，数组与步骤一一对应，单位分钟。缺失时从步骤文字和操作类型估算。总用时按步骤累加，未扣除并行时间。规划测试：`node tests/planner.cjs`。

图文菜谱源文件生成：`python scripts/build_ribs_recipe.py`。已有截图须保留在 `web/recipes/pepper-ribs/`。修改后需重新导出 PDF 和 PNG。
