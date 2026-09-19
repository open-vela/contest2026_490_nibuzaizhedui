# -*- coding: utf-8 -*-
"""
渲染"肥皂泡薄膜干涉"呼吸泡泡序列帧（soap_0.png ~ soap_7.png，384x384 RGBA）。
物理近似：薄膜厚度 d(x,y) 用几组行波叠加表示，颜色经干涉色板映射
（淡粉 -> 青 -> 金 -> 浅紫 循环），alpha 极低体现"极薄高度透明"。
每帧推进相位 -> 运行时轮播即"彩虹流转变幻"。
固定元素：左上明亮白色高光点 + 柔光晕、边缘折射亮圈与淡彩虹晕。
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
import os

_DOC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_DOC_DIR)
IMG_DIR = os.path.join(_PROJECT_DIR, "src", "common", "images")

S = 384
C = S / 2
R = S / 2 - 3
N_FRAMES = 8

yy, xx = np.mgrid[0:S, 0:S].astype(np.float64)
dx = xx - C + 18   # 膜厚扰动中心略偏，让纹路不那么对称
dy = yy - C - 14
r = np.sqrt(dx * dx + dy * dy) / R          # 0(中心) -> 1(边缘)
theta = np.arctan2(dy, dx)
inside = (r <= 1.0).astype(np.float64)

# 干涉色板：淡粉 -> 青 -> 金 -> 浅紫（柔和高明度低饱和）
PALETTE = np.array([
    [255, 196, 210],   # 淡粉
    [154, 232, 240],   # 青
    [255, 226, 158],   # 金
    [206, 184, 252],   # 浅紫
], dtype=np.float64)

def film_color(t):
    """t: ndarray in [0,1) -> (S,S,3)，在色板上循环插值"""
    n = PALETTE.shape[0]
    x = t * n
    i = np.floor(x).astype(int) % n
    j = (i + 1) % n
    f = (x - np.floor(x))[:, :, None]
    return PALETTE[i] * (1 - f) + PALETTE[j] * f

frames = []
for k in range(N_FRAMES):
    p = k / N_FRAMES * 2 * math.pi
    # 膜厚场：三组不同频率/方向的行波叠加 -> 流动的彩虹纹
    w = (np.sin(theta * 2 + r * 9 - p) +
         0.65 * np.sin(theta * 3 - r * 13 + p * 0.7) +
         0.4 * np.sin(r * 18 + theta + p * 1.3))
    t = (w + 2.05) / 4.1                       # 归一化到 [0,1]
    t = np.clip(t, 0, 0.9999)

    col = film_color(t)                        # (S,S,3)
    # 薄膜着色强度：中心弱、中带强、边缘再增强（边缘折射）
    band = np.exp(-((r - 0.62) ** 2) / 0.10)   # 中带虹彩
    rim = np.exp(-((r - 0.97) ** 2) / 0.004)   # 边缘折射虹
    strength = (0.34 * band + 0.85 * rim) * inside

    alpha = np.clip(strength * 150, 0, 120)    # 整体极透明
    rgb = np.dstack([col, alpha]).astype(np.uint8)
    frame = Image.fromarray(rgb, "RGBA")

    # 背后极淡的整体膜面（让泡泡"存在感"有一点点，alpha ~7%）
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.ellipse([C - R, C - R, C + R, C + R], fill=(220, 240, 250, 18))
    frame = Image.alpha_composite(body, frame)

    # 边缘亮圈（折射白线，柔焦）
    rim_line = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim_line)
    rd.ellipse([C - R + 2, C - R + 2, C + R - 2, C + R - 2],
               outline=(255, 255, 255, 90), width=2)
    rim_line = rim_line.filter(ImageFilter.GaussianBlur(1.2))
    frame = Image.alpha_composite(frame, rim_line)

    # 左上明亮白色高光点 + 柔光晕（肥皂泡的灵魂高光）
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hld = ImageDraw.Draw(hl)
    hx, hy = C - R * 0.42, C - R * 0.46
    hld.ellipse([hx - 26, hy - 26, hx + 26, hy + 26], fill=(255, 255, 255, 60))
    hl = hl.filter(ImageFilter.GaussianBlur(14))
    frame = Image.alpha_composite(frame, hl)
    core = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    cd.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=(255, 255, 255, 235))
    core = core.filter(ImageFilter.GaussianBlur(2.5))
    frame = Image.alpha_composite(frame, core)

    # 圆外裁剪
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([C - R, C - R, C + R, C + R], fill=255)
    frame.putalpha(Image.composite(frame.split()[3], Image.new("L", (S, S), 0), mask))

    out = os.path.join(IMG_DIR, f"soap_{k}.png")
    frame.save(out)
    frames.append(frame)
    print("saved", out)

# 预览图：4 帧拼一行，深色底
prev = Image.new("RGB", (S * 4, S), (11, 18, 32))
for i, fr in enumerate(frames):
    prev.paste(fr, (i * S, 0), fr)
prev.save(os.path.join(_DOC_DIR, "soap_preview_v1_pastel.png"))
print("preview saved")
