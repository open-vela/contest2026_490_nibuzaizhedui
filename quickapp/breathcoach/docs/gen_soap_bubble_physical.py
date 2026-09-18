# -*- coding: utf-8 -*-
"""
物理正确的肥皂泡薄膜干涉序列帧（soap_0..7.png, 384x384）。
移植自 Shadertoy "Physically-Based Soap Bubble" (XtKyRK) 的物理思路：
  R(λ) = r1² + r2² + 2·r1·r2·cos(4π·n·d·cosθt/λ + π)
  - 皂膜折射率 n=1.33，r1=(1-n)/(1+n)（含 π 相位突变），r2=(n-1)/(n+1)
  - 膜厚随高度排流变薄：顶部 ~40nm（薄到出现"黑膜"->透明），底部 ~600nm
  - 入射角随半径增大（边缘掠射），cosθt = sqrt(1 - (sinθi/n)²)
  - 48 个波长采样（400-700nm）按 RGB 敏感度加权积分出颜色
艺术化处理：反射率物理上仅 ~4%，暗背景下不可见，整体增益 ×5；
叠加轻微涡流扰动让膜厚场流动（帧间推进相位）。
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math

S = 384
C = S / 2
R = S / 2 - 3
N_FRAMES = 8
N = 1.33

yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
dx = xx - C
dy = yy - C
r = np.sqrt(dx * dx + dy * dy) / R
theta = np.arctan2(dy, dx).astype(np.float32)
inside = (r <= 1.0)

# 掠射角：中心正入射，边缘接近掠射
sin_i = np.clip(r, 0, 0.95).astype(np.float32)
cos_t = np.sqrt(1.0 - (sin_i / N) ** 2)          # 折射角余弦

# 排流膜厚：顶部薄（yn=+1）底部厚；含 4π/n 无量纲化：D = n·d·cosθt 直接以 nm 计
yn = (-dy / R).astype(np.float32)                 # 顶部 +1
d_base = 40.0 + (400.0 - 40.0) * (1 - yn) / 2.0   # 40..400 nm：条纹更少更柔

# 波长采样与 RGB 敏感度
lam = np.linspace(400, 700, 48).astype(np.float32)
wR = np.exp(-((lam - 610) / 65) ** 2)
wG = np.exp(-((lam - 545) / 65) ** 2)
wB = np.exp(-((lam - 465) / 55) ** 2)
W = np.stack([wR, wG, wB], axis=1)                # (48,3)
W /= W.sum(axis=0, keepdims=True)

r1 = (1 - N) / (1 + N)                            # -0.142
r2 = (N - 1) / (N + 1)                            # +0.142
base_r = r1 * r1 + r2 * r2                        # 0.0401
cross = 2 * r1 * r2                               # -0.0401

GAIN_HUE = 3.0    # 色相分离度（只影响颜色方向，不影响透明度）
SWIRL = 25.0      # 涡流扰动幅度 (nm)：排流条纹为主，涡流只做轻微扰动

def render_frame(k):
    p = k / N_FRAMES * 2 * math.pi
    # 涡流：慢速表面流让膜厚场不是死板的水平条纹
    swirl = (np.sin(theta * 2 + r * 4 + p) * 0.55 +
             np.sin(theta * 3 - r * 6 - p * 0.7) * 0.30 +
             np.sin(theta * 1 + r * 2 + p * 1.4) * 0.35)
    d = d_base + swirl.astype(np.float32) * SWIRL * (0.4 + 0.6 * (1 - yn))
    d = np.clip(d, 8.0, 900.0)

    # 光程差相位：δ = 4π·n·d·cosθt/λ，r1 带 π 突变并入 cross 符号
    accum = np.zeros((S, S, 3), dtype=np.float32)
    for li in range(len(lam)):
        delta = (4 * math.pi * N * d * cos_t / lam[li]).astype(np.float32) + math.pi
        refl = base_r + cross * np.cos(delta)      # R(λ) ∈ [0, 0.08]
        refl = np.clip(refl, 0, 0.08)
        for ch in range(3):
            accum[:, :, ch] += refl * W[li, ch]

    # 物理反射率 0..0.08 -> 相对值 0..1；平滑曲线：相消处真透明，不硬裁
    phys = accum.mean(axis=2) / 0.08
    hue = accum / (accum.max(axis=2)[:, :, None] + 1e-9)        # 最大通道归一
    hue = hue * 0.78 + 1.0 * 0.22                                # 粉彩化：向白混 22%
    alpha = (np.clip(phys, 0, 1) ** 0.8) * 175 * inside
    rgb = (np.clip(hue, 0, 1) * 255).astype(np.uint8)
    out = np.dstack([rgb, alpha.astype(np.uint8)])
    frame = Image.fromarray(out, "RGBA")
    # 后期：HSV 饱和度增强（干涉宽带色偏灰，摄影后期同款手法）
    hsv = np.array(frame.convert("HSV"), dtype=np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.7, 0, 255)
    frame = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGBA")
    # 柔焦：去掉 λ 积分的带状硬边，更像微距摄影的景深
    frame = frame.filter(ImageFilter.GaussianBlur(1.2))

    # 极淡膜面本体
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.ellipse([C - R, C - R, C + R, C + R], fill=(215, 238, 250, 16))
    frame = Image.alpha_composite(body, frame)

    # 边缘折射白线（柔焦）
    rim_line = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim_line)
    rd.ellipse([C - R + 2, C - R + 2, C + R - 2, C + R - 2],
               outline=(255, 255, 255, 80), width=2)
    rim_line = rim_line.filter(ImageFilter.GaussianBlur(1.2))
    frame = Image.alpha_composite(frame, rim_line)

    # 左上高光点 + 柔光晕
    hx, hy = C - R * 0.42, C - R * 0.46
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hld = ImageDraw.Draw(hl)
    hld.ellipse([hx - 26, hy - 26, hx + 26, hy + 26], fill=(255, 255, 255, 55))
    hl = hl.filter(ImageFilter.GaussianBlur(14))
    frame = Image.alpha_composite(frame, hl)
    core = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    cd.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=(255, 255, 255, 230))
    core = core.filter(ImageFilter.GaussianBlur(2.5))
    frame = Image.alpha_composite(frame, core)

    # 圆外裁剪
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([C - R, C - R, C + R, C + R], fill=255)
    frame.putalpha(Image.composite(frame.split()[3], Image.new("L", (S, S), 0), mask))
    return frame

frames = []
for k in range(N_FRAMES):
    fr = render_frame(k)
    out = rf"C:\Users\LAINXIANG\Desktop\小米\breathcoach\src\common\images\soap_{k}.png"
    fr.save(out)
    frames.append(fr)
    print("saved", out)

prev = Image.new("RGB", (S * 4, S * 2), (11, 18, 32))
for i, fr in enumerate(frames):
    prev.paste(fr, ((i % 4) * S, (i // 4) * S), fr)
prev.save(r"C:\Users\LAINXIANG\Desktop\小米\breathcoach\docs\soap_preview.png")
print("preview saved")
