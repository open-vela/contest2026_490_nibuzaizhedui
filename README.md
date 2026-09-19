# 静息（breathcoach）—— AI 压力呼吸教练

> 2026 首届 openvela AI 硬件开发者大赛 · 队伍 490「你不在这队」· 手表应用创新赛道

## 一、作品简介

**静息**是一个跑在 openvela 手表上的快应用：持续监测腕上压力与心率，压力偏高时引导你完成科学节奏的呼吸训练，训练后展示前后对比并给出 AI 恢复建议。

**解决的痛点**：现有智能手表的健康能力普遍「只监测、不干预」——压力值偏高之后没有下文；手机端呼吸/冥想类 App 又需要主动掏出手机、依赖网络、干扰强。静息把手表的「常驻、被动感知」特性变成「感知即干预」的闭环，全程离线完成。

**核心亮点**：

- **监测—干预—复盘完整闭环**：实时压力仪表盘（1Hz 刷新 + 等级变色圆环 + 脉搏涟漪）→ 双模式呼吸训练（4-2-6 平复 / 4-7-8 助眠，圆环随节律缩放）→ 训练前后压力/心率对比（数字滚动）→ AI 个性化恢复建议
- **端侧 AI + 全环境降级架构**：AI 问答基于 `@system.velaclaw`，软加载 + 4 秒超时兜底 + 关键词匹配本地建议三级降级，端侧 AI 不可用时功能不缺席、演示不中断
- **液态玻璃视觉体系**：Python 脚本离线预渲染肥皂泡虹彩/玻璃折射材质序列帧，在引擎不支持 `backdrop-filter` 的约束下实现玻璃质感
- **严肃的圆屏适配**：所有 UI 按「圆心安全圆 + 弦宽」约束逐页算账，466 圆屏无元素溢出表圈

**演示视频**：[video/2026 首届 openvela AI 硬件开发者大赛-你不在这队-静息-演示视频.mp4](video/2026%20首届%20openvela%20AI%20硬件开发者大赛-你不在这队-静息-演示视频.mp4)（4 分 33 秒，1080p；故事线：压力偏高 → 选择模式 → 呼吸训练 → 前后对比 → AI 建议 → AI 助手问答）

## 二、选题方向

**手表应用创新**。选择理由：

1. openvela 的 `service.health` 服务与内置健康数据回放，让「腕上健康闭环」可以在模拟器环境完整开发与验证；
2. 本届大赛提供的 `@system.velaclaw` 端侧 AI 能力天然适合「训练后即时解读与建议」这类短平快的交互；
3. 手表的常驻性与呼吸训练的短时长（约 72 秒）是天然匹配，能把「监测数据」真正转化为「干预行为」。

## 三、目录结构

```text
├── README.md                        # 本文件（作品说明）
├── LICENSE                          # Apache-2.0
├── contest2026_490_nibuzaizhedui.xml
├── openvela.xml                     # repo manifest：一键拉取 openvela 全量工程
├── quickapp/
│   └── breathcoach/                 # ★ 参赛作品（openvela 手表快应用）
│       ├── README.md                # 项目详细说明（简介/演示/快速开始/附录）
│       ├── package.json
│       ├── src/                     # 快应用源码（三页面 + 三模块）
│       ├── docs/                    # 踩坑指南 / 作品介绍文档 / 视频脚本 / 材质渲染脚本
│       ├── skills/
│       │   └── vela-emulator/       # AI 沉淀 Skill：Vela 模拟器启停与手动部署
│       └── .vscode/mcp.json         # velajs-mcp 配置
└── logs/                            # AI Coding 日志（导出后提交，格式见 logs/README.md）
```

manifest 通过 `<linkfile>` 将 `quickapp/breathcoach` 映射到 openvela 编译树 `packages/apps/contest2026_490_breathcoach`。

## 四、运行方式

**方式一：repo 拉取完整工程（推荐，与 openvela 编译树联动）**

```bash
repo init -u https://github.com/open-vela/contest2026_490_nibuzaizhedui \
  -b dev-ai-contest-2026 -m contest2026_490_nibuzaizhedui.xml
repo sync -c -j8
# 快应用位于 <workspace>/contest2026_490_nibuzaizhedui/quickapp/breathcoach
```

**方式二：单独克隆本仓开发快应用（初赛模拟器环境）**

1. 下载安装 AIoT-IDE，更新 `aiot-core`、`aiot-emulator` 扩展至 1.7.22+；
2. 新建模拟器，镜像选 `vela-miwear-watch-5.0(开发者大赛)`（内置 health 模块与数据回放）；
3. IDE「打开项目」选中 `quickapp/breathcoach/`，点「调试/运行」。

**命令行构建（免 IDE）**：`npm install && npx aiot build`（调试包）/ `npx aiot release`（签名发布包）；adb 手动部署与崩溃恢复见 `quickapp/breathcoach/docs/模拟器踩坑与启动指南.md`。

velaclaw 端侧 AI 环境（决赛/进阶，Ubuntu goldfish）配置步骤见 `quickapp/breathcoach/README.md` 附录 A。

## 五、AI Coding 使用说明

本项目以 ZCode（GLM 大模型驱动）为 AI 协作主力，覆盖四类工作：

1. **需求拆解与编码**：三页面快应用的全部业务源码、呼吸训练纯函数引擎、velaclaw 三级降级封装均由 AI 生成，人工负责需求定义、验收清单执行与动画手感调参；
2. **视觉资产管线**：AI 编写 Python 脚本离线预渲染肥皂泡/液态玻璃材质序列帧（`quickapp/breathcoach/docs/gen_*.py`）；
3. **环境排障知识沉淀**：开发中踩过的 16 个模拟器/工具链坑（adb 互杀、圆屏安全区、引擎 CSS 限制等）由 AI 整理成结构化指南，并进一步沉淀为可复用 Skill：`quickapp/breathcoach/skills/vela-emulator/SKILL.md`；
4. **MCP 工具链**：配置 velajs-mcp 打通模拟器设备管理、截图、UI 元素检查与构建自动化（`quickapp/breathcoach/.vscode/mcp.json`）。

完整 AI 对话日志见 `logs/` 目录（按《AI Coding 日志归集与提交手册》格式导出后提交）。

## LICENSE

该项目基于 Apache-2.0 license 开源（见 [LICENSE](LICENSE)）。
