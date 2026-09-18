---
name: vela-emulator
description: 启停 Vela 手表模拟器（Vela_Virtual_Device）并用 adb 手动部署、启动快应用 rpk；排查模拟器黑屏、guest 崩溃、adb 设备消失、IDE 预览转圈、覆盖安装静默失败等问题。当用户要求运行/调试 Vela 快应用、启动模拟器、安装 rpk，或报告模拟器异常时使用。
---

# Vela 模拟器启停与手动部署

## 环境常量（Windows + Git Bash）

- **唯一允许命令行使用的 adb**：`C:\Users\LAINXIANG\.aiot-ide\extensions\vela.aiot-emulator-1.7.22\dist\bin\win\adb.exe`（下称 `$ADB`）。IDE 调试期间绝不在命令行运行其他版本 adb 或 `adb kill-server`——两份 adb 会互杀 server，导致 IDE 预览 gRPC 粘性失败。
- 模拟器可执行文件：`C:\Users\LAINXIANG\.vela\sdk\emulator\windows-x86_64\emulator.exe`
- 虚拟设备目录：`C:\Users\LAINXIANG\.vela\vvd`（`ANDROID_AVD_HOME` 必须指向此处）
- 设备号：Vela 实例占 `emulator-5554` 或 `emulator-5556`（MuMu 安卓模拟器开着时占 5554）。区分方法：`shell "ps"` 输出为 NuttX 风格（FIFO/POLICY/Task 列头）才是 Vela。

## 启动模拟器

```bash
cd "C:\Users\LAINXIANG\.vela\vvd" && \
ANDROID_AVD_HOME="C:\Users\LAINXIANG\.vela\vvd" \
"C:\Users\LAINXIANG\.vela\sdk\emulator\windows-x86_64\emulator.exe" \
  -vela -avd Vela_Virtual_Device -show-kernel \
  -qemu -device virtio-snd,bus=virtio-mmio-bus.2 -allow-host-audio -semihosting -smp 2 \
  > /tmp/emu.log 2>&1 &
```

- 不加 `-qt-hide-window` 才有可见表盘窗口；`-show-kernel` 把 guest 内核日志写入 /tmp/emu.log（排查崩溃全靠它）。
- boot 需 40–60 秒。就绪标准：`"$ADB" -s emulator-XXXX shell "ps" | grep health_mock`。
- 启动前先清残留：`taskkill //F //IM qemu-system-armel.exe`（Git Bash 双斜杠）。

## 部署与启动应用

```bash
export MSYS_NO_PATHCONV=1   # 关键：防止 Git Bash 把 /data 路径改写成 Windows 路径
"$ADB" -s emulator-XXXX push app.rpk /data/app/pkg.rpk
"$ADB" -s emulator-XXXX shell "pm install /data/app/pkg.rpk"
"$ADB" -s emulator-XXXX shell "am start com.example.pkg"
```

- 同版本覆盖安装疑似静默失败（push 成功但进程起不来）：先 `pm uninstall <pkg>` 再 install。
- 应用安装在持久盘，模拟器重启后无需重装，直接 `am start`。
- `pm` 仅支持 install/uninstall 子命令；`am start` 成功时无回显，验证要看 `ps`。

## 崩溃恢复（guest 内核偶发 backtrace，与 App 无关）

1. 症状：qemu 窗口消失 / `adb devices` 变空 / `am start` 报 `error: closed`。
2. 证据：`/tmp/emu.log` 中出现 `sched_dumpstack: backtrace`。
3. 恢复：`taskkill //F //IM qemu-system-armel.exe` → 重跑启动命令 → 等 boot → `am start`（应用还在盘上）。

## 速查表

| 症状 | 处置 |
| --- | --- |
| `adb devices` 变空 | qemu 大概率崩了，按「崩溃恢复」流程重启 |
| IDE 预览面板转圈/黑屏 | 面板只是镜像；以 qemu 窗口或 `shell "ps"` 判断应用是否活着 |
| qemu 窗口点了 A 命中 B | 触摸坐标有 ~25px 垂直偏移；先点已知目标校准，或改用 IDE 预览面板点击 |
| 应用进程在但画面黑 | guest 屏幕休眠，点一下表盘窗口 |
| 圆屏角落元素找不到 | 角点超出圆屏半径被表圈裁掉，UI 必须放在半径 ~215px 安全圆内 |

完整 16 条踩坑记录见仓库 `docs/模拟器踩坑与启动指南.md`。
