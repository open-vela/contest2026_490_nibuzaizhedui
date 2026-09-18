# -*- coding: utf-8 -*-
"""
离线渲染 liquid glass 圆形气泡材质（512x512 RGBA PNG）。
运行时引擎不支持 backdrop-filter，把模糊/折射/高光全部烤进这张图：
  - 内部：极淡的径向透光雾（backdrop blur 的"朦胧感"来源）
  - 顶部偏左：微弱的弧形白色高光（光源折射）
  - 边缘内侧：1px 白色 40% 描边（玻璃厚度）
  - 右下边缘内侧：微弱暗弧（玻璃厚度造成的阴影）
整体保持通透：除描边外所有元素 alpha <= 15%。
"""
from PIL import Image, ImageDraw, ImageFilter
import math

SIZE = 512
CENTER = SIZE / 2
R = SIZE / 2 - 2  # 留 2px 防描边被裁

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

# ---------- 1. 内部透光雾（伪造 backdrop blur 的底） ----------
# 圆形蒙版内铺一层极淡的白雾，中心略偏左上（光源方向），向边缘衰减
haze = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
hd = ImageDraw.Draw(haze)
for radius, alpha in [(R, 5), (int(R * 0.72), 8), (int(R * 0.45), 10)]:
    hd.ellipse(
        [CENTER - radius - 30, CENTER - radius - 40, CENTER + radius - 30, CENTER + radius - 40],
        fill=(255, 255, 255, alpha),
    )
haze = haze.filter(ImageFilter.GaussianBlur(60))
img = Image.alpha_composite(img, haze)

# ---------- 2. 顶部/左上弧形高光（微弱渐变，模拟折射） ----------
# 沿内边缘画一条粗弧，再高斯模糊成柔和高光
hl = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
hld = ImageDraw.Draw(hl)
# 左上弧：角度 180°~315°（PIL 角度顺时针，0° 在 3 点钟方向）
hl_bbox = [CENTER - R + 6, CENTER - R + 6, CENTER + R - 6, CENTER + R - 6]
hld.arc(hl_bbox, start=185, end=330, fill=(255, 255, 255, 42), width=14)
hl = hl.filter(ImageFilter.GaussianBlur(9))
img = Image.alpha_composite(img, hl)

# 高光弧内侧再加一条更窄更淡的，形成"渐变"层次
hl2 = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
hl2d = ImageDraw.Draw(hl2)
hl2_bbox = [CENTER - R + 22, CENTER - R + 22, CENTER + R - 22, CENTER + R - 22]
hl2d.arc(hl2_bbox, start=200, end=310, fill=(255, 255, 255, 22), width=8)
hl2 = hl2.filter(ImageFilter.GaussianBlur(12))
img = Image.alpha_composite(img, hl2)

# ---------- 3. 右下内侧暗弧（玻璃厚度阴影） ----------
dk = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
dkd = ImageDraw.Draw(dk)
dk_bbox = [CENTER - R + 4, CENTER - R + 4, CENTER + R - 4, CENTER + R - 4]
dkd.arc(dk_bbox, start=10, end=140, fill=(8, 20, 30, 36), width=10)
dk = dk.filter(ImageFilter.GaussianBlur(7))
img = Image.alpha_composite(img, dk)

# ---------- 4. 裁回正圆（防止高光模糊溢出圆外） ----------
mask = Image.new("L", (SIZE, SIZE), 0)
md = ImageDraw.Draw(mask)
md.ellipse([CENTER - R, CENTER - R, CENTER + R, CENTER + R], fill=255)
img.putalpha(Image.composite(img.split()[3], Image.new("L", (SIZE, SIZE), 0), mask))

# ---------- 5. 1px 白色 40% 内描边（最后画，保持锐利） ----------
edge = ImageDraw.Draw(img)
edge.ellipse([CENTER - R + 1, CENTER - R + 1, CENTER + R - 1, CENTER + R - 1],
             outline=(255, 255, 255, 102), width=2)

out = r"C:\Users\LAINXIANG\Desktop\小米\breathcoach\src\common\images\glass.png"
img.save(out)
print("saved:", out)

# ---------- 6. 背景漂移光斑（柔和径向光晕，供玻璃圆"透光"用） ----------
def make_glow(rgb, out_path):
    S = 256
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    # 同心多层 + 高斯模糊 = 柔和径向衰减
    for radius, alpha in [(50, 70), (80, 46), (110, 24), (128, 10)]:
        gd.ellipse([S/2 - radius, S/2 - radius, S/2 + radius, S/2 + radius],
                   fill=rgb + (alpha,))
    g = g.filter(ImageFilter.GaussianBlur(28))
    g.save(out_path)
    print("saved:", out_path)

make_glow((45, 212, 191), r"C:\Users\LAINXIANG\Desktop\小米\breathcoach\src\common\images\glow_teal.png")
make_glow((79, 195, 247), r"C:\Users\LAINXIANG\Desktop\小米\breathcoach\src\common\images\glow_blue.png")

# 顺便输出一张放大 2 倍的深底预览图，方便肉眼检查
prev = Image.new("RGB", (SIZE, SIZE), (11, 18, 32))
prev.paste(img, (0, 0), img)
prev = prev.resize((1024, 1024), Image.NEAREST)
prev.save(r"C:\Users\LAINXIANG\Desktop\小米\breathcoach\docs\glass_preview.png")
print("preview saved")
