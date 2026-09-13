# 静息 · AI 压力呼吸教练

> 2026 首届 openvela AI 硬件开发者大赛 · 手表应用创新赛道参赛作品

**一句话介绍**：持续监测腕上压力与心率，压力偏高时引导你完成科学节奏的呼吸训练，训练后展示前后对比并给出 AI 恢复建议。

## 功能

| 页面 | 功能 |
| --- | --- |
| 首页 | 实时压力仪表盘（压力值 1Hz 刷新 + 等级变色圆环）+ 实时心率 |
| 呼吸训练 | 4-2-6 节奏（吸4s·屏2s·呼6s），圆环随呼吸节律缩放，共 6 组约 72 秒 |
| 训练总结 | 训练前后压力/心率对比 + 端侧 AI（velaclaw）生成个性化恢复建议 |
| AI 助手 | 快捷提问 + 自由问答（压力/心率/睡眠/放松建议），读入当前健康数据作为上下文 |

**降级设计**：`velaclaw` 仅在 openvela 真实环境（goldfish 模拟器/真机，且 `ai_agent` 进程已配置大模型）可用。AIoT IDE 内置模拟器中运行时自动切换"本地建议模式"（关键词匹配常见问题 + 内置建议），任何环境演示都不会中断。

## 项目结构

```
├── package.json
└── src/
    ├── app.ux                    # 应用入口
    ├── manifest.json             # 权限(service.health / velaclaw)、路由、designWidth 466
    ├── common/
    │   ├── health.js             # service.health 封装（订阅/查询/压力分级）
    │   ├── ai.js                 # velaclaw 封装 + 本地降级建议
    │   ├── breathing.js          # 呼吸模式与动画帧计算（纯函数）
    │   └── images/logo.png
    └── pages/
        ├── home/home.ux          # 压力仪表盘
        ├── breathing/breathing.ux# 呼吸训练 + 总结页
        └── assistant/assistant.ux# AI 助手
```

## 环境准备（初赛：模拟器开发）

1. 下载安装 **AIoT-IDE**：https://iot.mi.com/vela/quickapp/zh/guide/start/use-ide.html
2. 更新 IDE 插件：扩展面板中把 **`aiot-core`、`aiot-emulator`** 更新到 **1.7.22+**（否则 `service.health` 加载不到）
3. 新建模拟器：模拟器管理面板 → 新建 → 镜像版本必须选 **`vela-miwear-watch-5.0(开发者大赛)`**（只有该镜像内置 health 模块与数据回放）
4. 用 IDE「打开项目」选中本目录，选择上一步的模拟器，点「运行」

## velaclaw 端侧 AI（决赛/进阶环境）

AI 问答需要 openvela goldfish 模拟器（Ubuntu 编译，分支 `dev-ai-contest-2026`）：

1. menuconfig 开启：`CONFIG_FEATURE_SYSTEM_VELACLAW=y`、`CONFIG_EXAMPLES_AI_AGENT_VELA=y`、`CONFIG_MQ_MAXMSGSIZE=4096`（改配置后先 `rm -rf cmake_out/...` 再编译）
2. 启动模拟器后，在 NSH 串口终端运行 `ai_agent`，`vela>` 提示符下配置大模型：
   `set_llm https://token-plan-cn.xiaomimimo.com/v1 <model> tp-你的KEY`
3. `Ctrl+C` 退出后后台启动 `ai_agent &`，再 `vapp hap://app/com.vela.breathcoach`

详细步骤见官方教程《openvela 快应用调用端侧 AI Agent（@system.velaclaw）教程》。

## 模拟器踩坑 & 一次跑通

**先读 [docs/模拟器踩坑与启动指南.md](docs/模拟器踩坑与启动指南.md)**——包括：两份 adb 互杀、guest 崩溃识别与恢复、预览面板黑屏 ≠ 应用没起来、手动拉起模拟器/手动部署 rpk 的完整命令、排障速查表、功能验收清单。

## 打包提交

- 开发调试：IDE「打包」→ `dist/xxx.debug.rpk`
- 参赛提交：IDE「发布」生成签名 → 打出 **`release.rpk`**，连同源码工程、作品介绍文档（按官方模板）、演示视频（≤5 分钟）、AI Coding 日志一起放入专属仓
- 截止时间：**2026-09-20**

## 两周冲刺计划（9.6 → 9.20）

| 时间 | 目标 |
| --- | --- |
| 9.6–9.7 | 环境搭建，跑通官方 health-demo，确认模拟器健康数据正常 |
| 9.8–9.10 | 本项目骨架联调：三个页面在模拟器中跑通，数据订阅正常 |
| 9.11–9.14 | UI 打磨：圆形表盘适配、呼吸动画手感、配色统一；增加 4-7-8 助眠模式切换 |
| 9.15–9.16 | （可选）Ubuntu 编译 goldfish 模拟器，接通 velaclaw 真实 AI；同步开始写作品介绍文档 |
| 9.17–9.18 | 录制演示视频（压力上升→训练→压力下降→AI 建议 的完整故事线）；导出 AI 日志；沉淀 1 个 Skill |
| 9.19–9.20 | release 打包、自测编译运行、提 PR 到专属仓，留 1 天缓冲 |

## 已知事项 / 待完善

- [x] 呼吸模式切换（calm / sleep）——首页双胶囊入口 + 训练页按模式定轮数（calm 6 组 / sleep 4 组），9.12 已实现并复验通过
- [x] 压力趋势迷你曲线（首页，最近 22 次采样彩色柱状图），9.12 已实现并复验通过
- [x] 圆屏排版修复（9.12）：首页纵向布局压缩至 398px、训练总结页压缩至 ~406px 适配 466 圆屏（按钮/胶囊不再溢出表圈，按 AI 文案最长 4 行的最坏情况算账）；助手页气泡与输入行收紧；两处 AI 文案加 4~5 行硬上限防超长文本顶飞按钮
- [ ] 真机验证（决赛阶段申请样机）
- [ ] 模拟器 guest 偶发崩溃（goldfish 内核 backtrace，与 App 无关，出现时重启模拟器即可）

## License

本项目基于 [Apache-2.0](LICENSE) 协议开源。
