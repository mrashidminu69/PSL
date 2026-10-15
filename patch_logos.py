#!/usr/bin/env python3
"""
UNTESTED - mere paas aapki files nahi thi. Hamesha COPY par chalao.

  python patch_logos.py <in_file> <out_file> <logos_dir> [--dry]

<logos_dir>/<TextureName>.png  (naam bilkul Texture2D ke naam jaisa, jaise Quetta.png)

Kya karta hai:
  1. Har matching Texture2D ki ASLI width x height aur format padhta hai.
  2. Aapka logo bina stretch kiye, transparent canvas par CENTER me baithata hai (letterbox) -> aspect same, cropping nahi.
  3. Texture ko ORIGINAL format me hi encode karta hai (ASTC ho to ASTC). Format badalta nahi.
  4. Har object ke bytes ki length pehle/baad print karta hai - same size = in-place jaisa safe patch.
"""
import os
import sys

import UnityPy
from PIL import Image


def letterbox(img, w, h):
    img = img.convert("RGBA")
    s = min(w / img.width, h / img.height)
    nw, nh = max(1, round(img.width * s)), max(1, round(img.height * s))
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(img, ((w - nw) // 2, (h - nh) // 2), img)
    return canvas


def main(src, dst, logos, dry):
    env = UnityPy.load(src)
    changed = 0
    for obj in env.objects:
        if obj.type.name != "Texture2D":
            continue
        t = obj.read()
        png = os.path.join(logos, t.m_Name + ".png")
        if not os.path.exists(png):
            continue
        before = len(obj.get_raw_data())
        fmt_before = t.m_TextureFormat
        sd = getattr(t, "m_StreamData", None)
        print("%s  %dx%d  fmt=%s  mips=%s  stream_size=%s  bytes=%d"
              % (t.m_Name, t.m_Width, t.m_Height, fmt_before, t.m_MipCount,
                 getattr(sd, "size", None), before))
        if dry:
            continue
        t.image = letterbox(Image.open(png), t.m_Width, t.m_Height)
        try:
            t.save()
        except Exception as e:  # ASTC encoder na ho to yahan aayega
            print("   !! save fail: %r\n   ASTC encoder (astc-encoder-py) Termux Python 3.14 pe shayad na mile -> "
                  "ye script GitHub Actions (ubuntu) pe chalao." % (e,))
            continue
        after = len(obj.get_raw_data())
        print("   -> bytes %d -> %d  fmt %s -> %s %s"
              % (before, after, fmt_before, t.m_TextureFormat,
                 "(SAME size)" if before == after else "(SIZE BADLA - file layout badlega)"))
        changed += 1
    if dry:
        return
    print("changed:", changed)
    with open(dst, "wb") as f:
        f.write(env.file.save())  # agar AttributeError aaye: list(env.assets)[0].save()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3], "--dry" in sys.argv)
