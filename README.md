# 2026 首届 openvela AI 硬件开发者大赛

## 团队信息

- 团队名称：你不在这队
- 队伍编号：490
- 参赛赛道：
  - [ ] 新硬件平台适配
  - [ ] AI硬件产品创新
  - [x] 手表应用创新

## 项目简介

**静息（breathcoach）** —— AI 压力呼吸教练。

> 持续监测腕上压力与心率，压力偏高时引导你完成科学节奏的呼吸训练，训练后展示前后对比并给出 AI 恢复建议。

**解决的用户痛点**：现有智能手表的健康能力普遍「只监测、不干预」——压力值偏高之后没有下文；手机端呼吸/冥想类 App 又需要主动掏出手机、依赖网络、干扰强。静息把手表的「常驻、被动感知」特性变成「感知即干预」的闭环，全程离线完成。

**核心亮点**：

- **监测—干预—复盘完整闭环**：实时压力仪表盘（1Hz 刷新 + 等级变色圆环 + 脉搏涟漪）→ 双模式呼吸训练（4-2-6 平复 / 4-7-8 助眠，圆环随节律缩放）→ 训练前后压力/心率对比（数字滚动）→ AI 个性化恢复建议
- **端侧 AI + 全环境降级架构**：AI 问答基于 `@system.velaclaw`，采用软加载 + 4 秒超时兜底 + 关键词匹配本地建议的三级降级，端侧 AI 不可用时功能不缺席、演示不中断
- **液态玻璃视觉体系**：用 Python 脚本离线预渲染肥皂泡虹彩/玻璃折射材质序列帧，在引擎不支持 `backdrop-filter` 的约束下实现玻璃质感（脚本随仓库开源：`docs/gen_*.py`）
- **严肃的圆屏适配**：所有 UI 按「圆心安全圆 + 弦宽」约束逐页算账，466 圆屏无元素溢出表圈

## 项目演示

> 演示视频：【待录制后补充链接（B 站 / 网盘）】

故事线：压力偏高 → 选择模式 → 呼吸训练 → 前后对比 → AI 建议 → AI 助手问答。分镜脚本见 [docs/演示视频脚本.md](docs/演示视频脚本.md)。

## 快速开始

### 环境准备（初赛：AIoT IDE + 模拟器开发）

1. 下载安装 **AIoT-IDE**：https://iot.mi.com/vela/quickapp/zh/guide/start/use-ide.html
2. 扩展面板更新 **`aiot-core`、`aiot-emulator`** 至 **1.7.22+**（否则 `service.health` 加载不到）
3. 模拟器管理面板新建虚拟设备，镜像必须选 **`vela-miwear-watch-5.0(开发者大赛)`**（只有该镜像内置 health 模块与数据回放）
4. IDE「打开项目」选中本仓库根目录，选择上一步的模拟器，点「调试/运行」

### 命令行构建（免 IDE）

```bash
npm install        # 安装 aiot-toolkit
npx aiot build     # 调试构建 → dist/com.vela.breathcoach.debug.*.rpk
npx aiot release   # 发布构建（sign/release 证书签名）→ dist/com.vela.breathcoach.release.*.rpk
```

模拟器手动部署（adb push + pm install）、崩溃恢复与完整踩坑指南见 [docs/模拟器踩坑与启动指南.md](docs/模拟器踩坑与启动指南.md)。

## 目录结构

```
├── README.md
├── LICENSE                            # Apache-2.0
├── package.json
├── skills/
│   └── vela-emulator/SKILL.md        # AI 沉淀 Skill：Vela 模拟器启停与手动部署
├── docs/
│   ├── 模拟器踩坑与启动指南.md        # 16 条踩坑记录 + 路线 A/B 完整复现指南
│   ├── 作品介绍文档-草稿.md
│   ├── 演示视频脚本.md
│   └── gen_*.py                      # 液态玻璃材质离线渲染脚本
└── src/
    ├── app.ux                        # 应用入口
    ├── manifest.json                 # 权限(service.health / velaclaw)、路由、designWidth 466
    ├── common/
    │   ├── health.js                 # service.health 封装（订阅/查询/压力分级）
    │   ├── ai.js                     # velaclaw 封装 + 本地降级建议
    │   ├── breathing.js              # 呼吸模式与动画帧计算（纯函数）
    │   └── images/                   # 肥皂泡序列帧 / 光晕 / logo
    └── pages/
        ├── home/home.ux              # 压力仪表盘
        ├── breathing/breathing.ux    # 呼吸训练 + 训练总结
        └── assistant/assistant.ux    # AI 助手
```

## 更多文档

- [Vela 模拟器踩坑记录 & 一次跑通指南](docs/模拟器踩坑与启动指南.md)
- [作品介绍文档](docs/作品介绍文档-草稿.md)
- [演示视频脚本](docs/演示视频脚本.md)
- [AI 沉淀 Skill：vela-emulator](skills/vela-emulator/SKILL.md)

## LICENSE

该项目基于 Apache-2.0 license 开源（见 [LICENSE](LICENSE)）。

---

## 附录 A：velaclaw 端侧 AI（决赛/进阶环境）

AI 问答需要 openvela goldfish 模拟器（Ubuntu 编译，分支 `dev-ai-contest-2026`）：

1. menuconfig 开启：`CONFIG_FEATURE_SYSTEM_VELACLAW=y`、`CONFIG_EXAMPLES_AI_AGENT_VELA=y`、`CONFIG_MQ_MAXMSGSIZE=4096`（改配置后先 `rm -rf cmake_out/...` 再编译）
2. 启动模拟器后，在 NSH 串口终端运行 `ai_agent`，`vela>` 提示符下配置大模型：
   `set_llm https://token-plan-cn.xiaomimimo.com/v1 <model> tp-你的KEY`
3. `Ctrl+C` 退出后后台启动 `ai_agent &`，再 `vapp hap://app/com.vela.breathcoach`

未配置 velaclaw 的环境下应用自动进入本地建议模式，全部功能可用。

## 附录 B：开发历程与已知事项

两周冲刺计划（9.6 → 9.20）执行记录：

| 时间 | 目标 | 状态 |
| --- | --- | --- |
| 9.6–9.7 | 环境搭建，跑通官方 health-demo | ✅ |
| 9.8–9.10 | 三页面骨架联调，数据订阅正常 | ✅ |
| 9.11–9.14 | UI 打磨：圆屏适配、呼吸动画、4-7-8 助眠模式、趋势曲线 | ✅ |
| 9.13 | git 建仓、release 包构建、模拟器冒烟验证、提交材料起草 | ✅ |
| 9.14–9.17 | 演示视频录制、作品文档定稿、AI 日志导出 | 🔄 进行中 |
| 9.18–9.20 | PR 走查、压缩包提交，留 1 天缓冲 | ⏳ |

已知事项：

- [ ] 真机验证（决赛阶段申请样机）
- [ ] 模拟器 guest 偶发崩溃（goldfish 内核 backtrace，与 App 无关，重启即可恢复）
- [x] 呼吸模式切换（calm / sleep）、压力趋势迷你曲线、圆屏排版修复
- [x] release 包构建与模拟器安装冒烟验证（9.13）
