# -*- coding: utf-8 -*-
"""
肥皂泡 v2「暗底虹彩」序列帧（soap_0..7.png, 384x384 RGBA）。

物理内核沿用 v1（Shadertoy "Physically-Based Soap Bubble" 的薄膜干涉思路），
v2 针对手表圆屏可读性重做美术方向：
  1. 深蓝玻璃球体基底（近不透明），与表盘 #0b1220 融为一体，室外强光下相位文字可读；
  2. 虹彩只出现在中带/边缘的薄膜高光（真实皂膜油膜反光的形态），中心区让位给文字；
  3. 粉彩化 + 饱和度硬上限 S<=0.59、明度上限 V<=0.88，杜绝"气象图"式全谱荧光；
  4. 中心烘焙径向暗化（scrim），保证相位标签（#e6fffb）对比度 >= 4.5:1。
注意：v1 的 HSV 后处理走 PIL convert("HSV") 会丢 alpha（帧变实心圆盘），v2 改为
numpy 内按公式钳制 S/V，RGB/alpha 全程分离。
输出：../src/common/images/soap_0..7.png + ./soap_preview.png（4x2 预览）
数值验收：./check_bubble_contrast.py
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 384
C = S / 2
R = S / 2 - 3
N_FRAMES = 8
N = 1.33

_DOC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_DOC_DIR)
IMG_DIR = os.path.join(_PROJECT_DIR, "src", "common", "images")

yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
dx = xx - C
dy = yy - C
r = np.sqrt(dx * dx + dy * dy) / R
theta = np.arctan2(dy, dx).astype(np.float32)
inside = (r <= 1.0)

sin_i = np.clip(r, 0, 0.95).astype(np.float32)
cos_t = np.sqrt(1.0 - (sin_i / N) ** 2)

yn = (-dy / R).astype(np.float32)
d_base = 40.0 + (400.0 - 40.0) * (1 - yn) / 2.0

lam = np.linspace(400, 700, 48).astype(np.float32)
wR = np.exp(-((lam - 610) / 65) ** 2)
wG = np.exp(-((lam - 545) / 65) ** 2)
wB = np.exp(-((lam - 465) / 55) ** 2)
W = np.stack([wR, wG, wB], axis=1)
W /= W.sum(axis=0, keepdims=True)

r1 = (1 - N) / (1 + N)
r2 = (N - 1) / (N + 1)
base_r = r1 * r1 + r2 * r2
cross = 2 * r1 * r2

SWIRL = 25.0

# v2 视觉参数
S_MAX = 0.58        # 饱和度硬上限（气象图防线）
V_MAX = 225.0       # 明度硬上限 (0.88)
S_BOOST = 1.7       # 色带提饱和系数（提完仍被 S_MAX 封顶）
CENTER_CUT0 = 0.32  # 中心无虹彩区（文字让位），0.32~0.50 渐入

# v1 粉彩色板：淡粉 -> 青 -> 金 -> 浅紫（五彩的来源，与 AI 助手气泡同色板）
PALETTE = np.array([
    [255, 196, 210],
    [154, 232, 240],
    [255, 226, 158],
    [206, 184, 252]
], dtype=np.float32)


def palette_color(t_norm):
    """膜厚相位 -> 粉彩色板循环插值 (S,S,3)"""
    n = PALETTE.shape[0]
    x = (t_norm % 1.0) * n
    i = np.floor(x).astype(np.int32) % n
    j = (i + 1) % n
    f = (x - np.floor(x))[:, :, None]
    return PALETTE[i] * (1 - f) + PALETTE[j] * f


def clamp_sv(rgb, s_ceiling=S_MAX):
    """矢量版 S/V 钳制（不经过 PIL，保住 alpha）"""
    V = rgb.max(axis=2, keepdims=True)
    Ssat = (V - rgb.min(axis=2, keepdims=True)) / np.maximum(V, 1e-6)
    f = np.where(Ssat > s_ceiling, s_ceiling / np.maximum(Ssat, 1e-6), 1.0)
    rgb = V - (V - rgb) * f
    scale = np.where(V > V_MAX, V_MAX / np.maximum(V, 1e-6), 1.0)
    return rgb * scale


def boost_sat(rgb):
    """提饱和：S' = min(S*BOOST, S_MAX)（往灰轴反向拉）"""
    V = rgb.max(axis=2, keepdims=True)
    Ssat = (V - rgb.min(axis=2, keepdims=True)) / np.maximum(V, 1e-6)
    k = np.minimum(S_BOOST, S_MAX / np.maximum(Ssat, 1e-6))
    return V - (V - rgb) * k


def render_frame(k):
    p = k / N_FRAMES * 2 * math.pi
    swirl = (np.sin(theta * 2 + r * 4 + p) * 0.55 +
             np.sin(theta * 3 - r * 6 - p * 0.7) * 0.30 +
             np.sin(theta * 1 + r * 2 + p * 1.4) * 0.35)
    d = d_base + swirl.astype(np.float32) * SWIRL * (0.4 + 0.6 * (1 - yn))
    d = np.clip(d, 8.0, 900.0)

    accum = np.zeros((S, S, 3), dtype=np.float32)
    for li in range(len(lam)):
        delta = (4 * math.pi * N * d * cos_t / lam[li]).astype(np.float32) + math.pi
        refl = base_r + cross * np.cos(delta)
        refl = np.clip(refl, 0, 0.08)
        for ch in range(3):
            accum[:, :, ch] += refl * W[li, ch]

    phys = accum.mean(axis=2) / 0.08
    hue = accum / (accum.max(axis=2)[:, :, None] + 1e-9)

    # 五彩来源：物理干涉色 与 粉彩色板（膜厚相位驱动循环）55:45 混合
    # ×1.8：实际膜厚范围只覆盖归一化区间的前 ~55%，放大让淡粉也进循环
    t_norm = (d - 8.0) / (900.0 - 8.0) * 1.8
    pal = palette_color(t_norm)
    rgb = np.clip(hue, 0, 1) * 255 * 0.55 + pal * 0.45
    rgb = boost_sat(rgb)
    rgb = clamp_sv(rgb)

    # 虹彩只在中带 + 边缘出现；中心为文字让位
    band = 0.30 + 0.70 * np.exp(-((r - 0.62) ** 2) / 0.09)
    rim_glow = 0.55 * np.exp(-((r - 0.93) ** 2) / 0.008)
    center_cut = np.clip((r - CENTER_CUT0) / 0.18, 0, 1) ** 1.1
    vis = (band + rim_glow) * center_cut

    alpha = (np.clip(phys, 0, 1) ** 0.85) * 190 * vis * inside

    irid = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8),
                      np.clip(alpha, 0, 255).astype(np.uint8)])
    frame = Image.fromarray(irid, "RGBA").filter(ImageFilter.GaussianBlur(1.2))

    # 深蓝玻璃球基底：近不透明，中心略深边缘略亮的径向渐变
    t = np.clip(r, 0, 1)[:, :, None]
    body_rgb = (np.array([13, 21, 36]) * (1 - t) + np.array([27, 41, 66]) * t)
    body_a = (240 - 16 * np.clip(r, 0, 1)) * inside
    body = Image.fromarray(np.dstack([body_rgb.astype(np.uint8),
                                      body_a.astype(np.uint8)]), "RGBA")
    frame = Image.alpha_composite(body, frame)

    # 中心烘焙暗化（scrim）：文字底布直接进贴图
    scrim_a = (190 * np.clip((0.68 - r) / 0.52, 0, 1) ** 1.25 * inside).astype(np.uint8)
    scrim = Image.fromarray(np.dstack([np.full((S, S), 11, np.uint8),
                                       np.full((S, S), 18, np.uint8),
                                       np.full((S, S), 32, np.uint8), scrim_a]), "RGBA")
    frame = Image.alpha_composite(frame, scrim)

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
    hld.ellipse([hx - 26, hy - 26, hx + 26, hy + 26], fill=(255, 255, 255, 50))
    hl = hl.filter(ImageFilter.GaussianBlur(14))
    frame = Image.alpha_composite(frame, hl)
    core = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    cd.ellipse([hx - 9, hy - 9, hx + 9, hx + 9], fill=(255, 255, 255, 220))
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
    out = os.path.join(IMG_DIR, f"soap_{k}.png")
    fr.save(out)
    frames.append(fr)
    print("saved", out)

prev = Image.new("RGB", (S * 4, S * 2), (11, 18, 32))
for i, fr in enumerate(frames):
    prev.paste(fr, ((i % 4) * S, (i // 4) * S), fr)
prev.save(os.path.join(_DOC_DIR, "soap_preview.png"))
print("preview saved")
