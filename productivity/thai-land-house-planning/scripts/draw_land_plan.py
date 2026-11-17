# -*- coding: utf-8 -*-
"""วาดผังแบ่งโซนที่ดิน 2 ไร่ (40x80ม.) — บ้านแพตตี้ โป่งผา แม่สาย (v2, proven 2026-08-25)
Run: PYTHONPATH=/opt/data/pylibs python3 draw_land_plan.py   (fallback: profile venv)
Requires Thai font: /opt/data/fonts/NotoSansThai.ttf (download if missing):
  curl -sL -o /opt/data/fonts/NotoSansThai.ttf "https://github.com/google/fonts/raw/main/ofl/notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf"
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1720, 1080
img = Image.new("RGB", (W, H), (10, 14, 26))
d = ImageDraw.Draw(img)

FONT_PATHS = [
    "/opt/data/fonts/NotoSansThai.ttf",
    "/opt/data/fonts/NotoSansThai-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
def F(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

f_title = F(32); f_zone = F(24); f_small = F(19); f_tiny = F(16); f_leg = F(18)

def box(x, y, w, h, fill, outline, ow=2, radius=8):
    d.rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=fill, outline=outline, width=ow)

def ctext(cx, y, text, font, fill, anchor="mm"):
    d.text((cx, y), text, font=font, fill=fill, anchor=anchor)

# ---- ผัง: 40m x 80m @ 9px/m ----
PX = 9
PX0, PY0 = 110, 190          # plot top-left (เหลือที่หัวข้อด้านบน)
PW, PH = 360, 720            # 40m x 80m
X0, X1 = PX0, PX0+PW
Y0, Y1 = PY0, PY0+PH

hA, hB = 180, 270            # A=20m(180px) B=30m(270px) C=30m(270px)
yC0 = PY0; yB0 = PY0+hB; yA0 = PY0+hB+hA

# พื้นหลังโซน
box(PX0, yC0, PW, hB, (16, 48, 30), (52, 122, 82), ow=2)          # C ป่า
box(PX0, yB0, PW, hB, (20, 66, 40), (86, 150, 100), ow=2)         # B สวนผลไม้
box(PX0, yA0, PW, hA, (88, 74, 48), (196, 168, 110), ow=2)        # A หิน+ผ้าดำ

# รั้วรอบ 2 ไร่
d.rectangle((X0, Y0, X1, Y1), outline=(210, 220, 235), width=3)
d.line([(X0, yA0), (X1, yA0)], fill=(255, 220, 120), width=2)     # รั้วโซน A

# ---- โซน A: บ้าน + สวน + ลานจอด ----
hx, hy = 140, 95
house_x, house_y = X0 + 115, yA0 + 45
box(house_x, house_y, hx, hy, (245, 240, 225), (70, 70, 70), ow=3, radius=4)
ctext(house_x+hx/2, house_y+hy/2-6, "บ้าน 2 ชั้น", F(20), (40, 40, 40))
d.text((house_x+hx/2, house_y+hy/2+22), "นีโอคลาสสิก", font=f_tiny, fill=(90, 90, 90), anchor="mm")

# สวนหน้าบ้าน + น้ำพุ
fx, fy = X0+42, yA0+45
d.ellipse((fx, fy, fx+62, fy+62), outline=(180, 200, 160), width=2)
d.ellipse((fx+18, fy+18, fx+44, fy+44), outline=(150, 175, 130), width=2)
ctext(fx+31, fy+76, "น้ำพุ", F(17), (210, 230, 190))

# ทางเดินจากประตูถึงบ้าน
d.line([(X0+PW/2, Y1), (X0+PW/2, yA0+hy+16)], fill=(225, 210, 180), width=9)
d.line([(X0+PW/2, yA0+hy+16), (house_x+hx/2, yA0+hy+16)], fill=(225, 210, 180), width=9)

# ลานจอดรถ
box(X1-85, yA0+118, 62, 40, (70, 70, 75), (150, 150, 160), ow=2)
ctext(X1-54, yA0+138, "จอดรถ", F(16), (230, 230, 230))

# ประตูหลักทิศใต้
d.rectangle((X0+PW/2-16, Y1-6, X0+PW/2+16, Y1+2), fill=(255, 200, 90))
ctext(X0+PW/2, Y1+22, "ประตูหลัก (ทิศใต้)", F(17), (255, 210, 120))
# ประตูคนเดิน
d.rectangle((X0+28, Y1-5, X0+40, Y1+1), fill=(160, 170, 190))

# ---- โซน B: สวนผลไม้ ----
tree = [(X0+55, yB0+55), (X0+180, yB0+50), (X0+290, yB0+110),
        (X0+95, yB0+160), (X0+240, yB0+205), (X0+315, yB0+35)]
labels = ["กล้วย", "มะม่วง", "มะพร้าว", "กล้วย", "ขนุน", "มะม่วง"]
for (tx, ty), lb in zip(tree, labels):
    d.ellipse((tx-18, ty-18, tx+18, ty+18), fill=(70, 150, 80), outline=(140, 210, 150), width=2)
    d.text((tx, ty), lb, font=f_tiny, fill=(220, 240, 210), anchor="mm")

# ---- โซน C: ป่า ----
for i in range(6):
    cx = X0 + 55 + (i % 3) * 125
    cy = yC0 + 45 + (i // 3) * 105
    d.ellipse((cx-24, cy-24, cx+24, cy+24), fill=(28, 80, 45), outline=(110, 180, 120), width=2)
    d.ellipse((cx-9, cy-9, cx+9, cy+9), fill=(45, 100, 55))

# ---- ป้ายโซน (อยู่เหนือเส้นแบ่ง) ----
ctext(X0+PW/2, yA0-14, "โซน A · บ้าน + สวนหิน (งาน 0)", f_zone, (255, 220, 140))
ctext(X0+PW/2, yB0-14, "โซน B · สวนผลไม้ (ปีละ 4 ครั้ง)", f_zone, (170, 230, 170))
ctext(X0+PW/2, yC0-14, "โซน C · ป่ารกดีแล้ว (ปีละ 1 ครั้ง)", f_zone, (140, 200, 150))

# ทิศเหนือ (วางเหนือโซน C, ในช่องว่างด้านบน)
nx, ny = X1+45, Y0+10
d.line([(nx, ny+40), (nx, ny-10)], fill=(255, 255, 255), width=3)
d.polygon([(nx-9, ny-5), (nx+9, ny-5), (nx, ny-24)], fill=(255, 255, 255))
ctext(nx, ny+56, "ทิศเหนือ", F(17), (255, 255, 255))

# ---- ด้านขวา: ข้อมูล (คอลัมน์แยกชัด x=600) ----
LX = 640
ctext(LX, 70, "ผังแบ่งโซนที่ดิน 2 ไร่ (80 × 40 ม.)", f_title, (255, 255, 255))
ctext(LX, 112, "ตำบลโป่งผา อำเภอแม่สาย เชียงราย · ระดับสูง 405 ม.", f_small, (170, 180, 200))

# มาตราส่วน
sx = LX; sy = 158
d.line([(sx, sy), (sx+180, sy)], fill=(200, 210, 225), width=3)
for k in range(5):
    x = sx + k*45
    d.line([(x, sy-7), (x, sy+7)], fill=(200, 210, 225), width=2)
    d.text((x, sy+13), f"{k*5}ม.", font=f_tiny, fill=(180, 190, 210), anchor="mm")

items = [
    ("โซน A · บ้าน + สวนหิน (800 ตร.ม.)", (255, 220, 140),
     ["บ้าน 2 ชั้น + ลานจอด 2 คัน", "ผ้าดำคลุม + หินเกล็ด = ไม่ต้องตัดหญ้า",
      "น้ำพุหน้าบ้าน (ทิศใต้ ตามฮวงจุ้ย)", "รั้วปูนครึ่งทึบ + ประตูเหล็ก + กล้อง", "งาน: 0 ต่อสัปดาห์"]),
    ("โซน B · สวนผลไม้ (1,200 ตร.ม.)", (170, 230, 170),
     ["กล้วย / มะม่วง / มะพร้าว / ขนุน", "ไม่ต้องรดน้ำ (ฝนพอ) + ถั่วคลุมดินกันหญ้า",
      "จ้างตัดหญ้า 4 ครั้ง/ปี (~800 บาท/ครั้ง)", "เก็บผล = กินเอง + ทำคอนเทนต์", "งาน: ปีละ 4 ครั้ง"]),
    ("โซน C · ป่ารกดีแล้ว (1,200 ตร.ม.)", (140, 200, 150),
     ["ปล่อยต้นไม้เดิม / ปลูกไม้ใหญ่เพิ่ม", "กันลม + ร่มเงา + ความเป็นส่วนตัว",
      "ไม่ต้องเข้าไป = ไม่ต้องตัด", "จ้างเลื่อยกิ่งปีละ 1 ครั้ง", "งาน: ปีละ 1 ครั้ง"]),
]
yy = 240
for title, color, lines in items:
    ctext(LX, yy, title, F(22), color)
    yy += 32
    for ln in lines:
        d.text((LX, yy), "• " + ln, font=f_small, fill=(205, 212, 225), anchor="lm")
        yy += 27
    yy += 12

ctext(LX, yy+6, "ระบบช่วยแม่ (ลงทุนครั้งเดียว)", F(22), (140, 200, 255))
yy += 40
for ln in ["ระบบน้ำหยดอัตโนมัติ ~3,000-5,000 บาท", "ไฟโซลาร์เซนเซอร์ ~2,000-4,000 บาท",
           "กล้องวงจรปิด 2-4 ตัว ~3,000-6,000 บาท", "ประตูรหัส ~3,000-8,000 บาท"]:
    d.text((LX, yy), "• " + ln, font=f_small, fill=(185, 200, 230), anchor="lm")
    yy += 27

yy += 16
ctext(LX, yy, "ค่าใช้จ่ายรายปีรวม ~6,700 บาท (≈560 บาท/เดือน)", F(20), (255, 210, 120))

# เชิงอรรถด้านล่าง (ไม่ถูกตัด)
ctext(W/2, H-28, "หลัก: ยิ่งใกล้บ้านยิ่งหิน+ผ้าดำ · ยิ่งไกลยิ่งปล่อยธรรมชาติ — ดูแลง่ายสำหรับแม่คนเดียว",
      f_tiny, (140, 150, 170))

out = "/opt/data/ผังโซนที่ดิน_โป่งผา.png"
img.save(out)
print("saved", out)
