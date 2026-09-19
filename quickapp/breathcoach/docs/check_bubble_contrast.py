# -*- coding: utf-8 -*-
"""
泡泡贴图数值验收：对比度 + 饱和度硬指标。

模拟引擎的真实叠层：页面底 #0b1220 -> soap_k.png -> 相位 tint（全盘覆盖）。
指标：
  1. 对比度：取最坏的「吸气」tint rgba(45,212,191,0.12) 参与合成（最坏亮度情况），
     文字区（中心 r<=0.40 圆盘）p95 相对亮度 与 相位文字色 #e6fffb 的
     WCAG 对比度 >= 4.5
  2. 饱和度：贴图本体在页面底上的合成（不含相位 tint——tint 是功能色设计，
     不属于贴图验收范围）。HSV 饱和度只统计 V>=0.5 的亮部像素——深海军蓝底色
     本身 S 就有 ~0.66（深色蓝 V 低 B 高），"气象图感"来自又亮又艳的像素，
     暗部不构成风险。亮部 S_max <= 0.60
"""
import os
import numpy as np
from PIL import Image

_DOC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_DOC_DIR)
IMG_DIR = os.path.join(_PROJECT_DIR, "src", "common", "images")

S = 384
C = S / 2
R = S / 2 - 3
BG = np.array([11, 18, 32], dtype=np.float32)          # 页面底色 #0b1220
TINT = np.array([45, 212, 191], dtype=np.float32)       # 吸气 tint
TINT_A = 0.12
TEXT = np.array([230, 255, 251], dtype=np.float32)      # #e6fffb

yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
r = np.sqrt((xx - C) ** 2 + (yy - C) ** 2) / R
disc = r <= 1.0
text_zone = r <= 0.40


def srgb_to_lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def rel_lum(rgb):
    l = srgb_to_lin(rgb)
    return 0.2126 * l[..., 0] + 0.7152 * l[..., 1] + 0.0722 * l[..., 2]


L_text = float(rel_lum(TEXT[None, None])[0, 0])

ok_all = True
print(f"文字色 L={L_text:.3f}  指标: 对比度>=4.5, S<=0.60\n--")
for k in range(8):
    img = np.array(Image.open(os.path.join(IMG_DIR, f"soap_{k}.png")).convert("RGBA"),
                   dtype=np.float32)
    a = img[..., 3:4] / 255.0
    comp = img[..., :3] * a + BG * (1 - a)              # 页面底上合成
    comp_tint = comp * (1 - TINT_A) + TINT * TINT_A     # 相位 tint 全盘覆盖（查对比度用）

    zone = comp_tint[text_zone]
    lums = np.sort(rel_lum(zone))
    p95 = float(lums[int(len(lums) * 0.95) - 1])
    ratio = (L_text + 0.05) / (p95 + 0.05)

    dpx = comp[disc]                                    # 贴图本体饱和度（不含 tint）
    dV = dpx.max(axis=1)
    bright = dV >= 128.0                                # 只查亮部：暗底天然 S 高但不是风险
    dB = dpx[bright]
    Vb = dB.max(axis=1)
    Ssat_b = (Vb - dB.min(axis=1)) / np.maximum(Vb, 1e-6)
    smax = float(Ssat_b.max()) if len(Ssat_b) else 0.0

    ok = ratio >= 4.5 and smax <= 0.60
    ok_all = ok_all and ok
    print(f"soap_{k}: 对比度={ratio:5.2f} ({'PASS' if ratio >= 4.5 else 'FAIL'})"
          f"  S_max={smax:.3f} ({'PASS' if smax <= 0.60 else 'FAIL'})")

print("--\nRESULT:", "ALL PASS" if ok_all else "FAIL")
raise SystemExit(0 if ok_all else 1)
