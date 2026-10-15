#!/usr/bin/env python3
# bbc_logo_fix.py  (pip install UnityPy Pillow)
#
# Inspect only:
#   python bbc_logo_fix.py --apk bb.apk --obb main.obb --inspect
# Patch (PSL pngs named AS.png, AS_big.png, ... are optional;
# without --logos it refits the pixels already in the textures):
#   python bbc_logo_fix.py --apk bb.apk --obb main.obb --logos ./psl --out ./patched
#   add --skip HH,HH_big to leave Quetta untouched
import argparse, os, shutil, tempfile, zipfile
import UnityPy
from UnityPy.enums import TextureFormat
from PIL import Image

TEAMS = ["AS", "BH", "HH", "MR", "MS", "PS", "SS", "ST"]
NAMES = set(TEAMS) | {t + "_big" for t in TEAMS}
SIZES = {(90, 80), (256, 213)}   # only touch sprites with these rect sizes
MARGIN = 0.04
DATA = "assets/bin/Data/"


def fit(img, cw, ch):
    img = img.convert("RGBA")
    bb = img.getchannel("A").getbbox()
    if bb:
        img = img.crop(bb)
    s = min(cw * (1 - 2 * MARGIN) / img.width, ch * (1 - 2 * MARGIN) / img.height)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    out.alpha_composite(img, ((cw - img.width) // 2, (ch - img.height) // 2))
    return out


def do_sprite(obj, a, logos, changed):
    t = obj.read_typetree()
    name = t["m_Name"]
    if name not in NAMES:
        return
    r, rd = t["m_Rect"], t["m_RD"]
    tr, off = rd["textureRect"], rd["textureRectOffset"]
    print(f"  Sprite {name}: rect=({r['x']},{r['y']},{r['width']},{r['height']}) "
          f"textureRect=({tr['x']},{tr['y']},{tr['width']},{tr['height']}) "
          f"offset=({off['x']},{off['y']}) pivot=({t['m_Pivot']['x']},{t['m_Pivot']['y']})")
    if (round(r["width"]), round(r["height"])) not in SIZES:
        print("    skip: rect is not 90x80 / 256x213")
        return
    if name in a.skip:
        print("    skip: --skip")
        return
    tex_obj = obj.read().m_RD.texture.deref()
    tex = tex_obj.read()
    if (tex.m_Width, tex.m_Height) != (round(r["width"]), round(r["height"])):
        print(f"    skip: atlas-packed ({tex.m_Width}x{tex.m_Height}), needs manual handling")
        return
    if a.inspect:
        return
    src = logos.get(name)
    img = Image.open(src) if src else tex.image
    canvas = fit(img, tex.m_Width, tex.m_Height)
    try:
        tex.set_image(canvas, target_format=TextureFormat.RGBA32, mipmap_count=1)
    except TypeError:
        tex.image = canvas
    tex.save()
    tr.update(x=r["x"], y=r["y"], width=r["width"], height=r["height"])  # full frame
    off.update(x=0.0, y=0.0)                                              # no trim offset
    obj.save_typetree(t)
    changed.update({obj.assets_file, tex_obj.assets_file})
    print("    patched")


def go_name(sf, tree):
    return sf.objects[tree["m_GameObject"]["m_PathID"]].read().m_Name


def do_clublogo(sf, a, changed):
    for o in list(sf.objects.values()):
        if o.type.name != "GameObject":
            continue
        go = o.read()
        if go.m_Name != "ClubLogo":
            continue
        print(f"  GameObject ClubLogo (path_id {o.path_id}) in {sf.name}")
        for c in go.m_Components:
            try:
                co = getattr(c, "component", c).deref()
                kind = co.type.name
                t = co.read_typetree()
                if kind == "RectTransform":
                    print(f"    RectTransform sizeDelta={t['m_SizeDelta']} anchorMin={t['m_AnchorMin']} "
                          f"anchorMax={t['m_AnchorMax']} pos={t['m_AnchoredPosition']} pivot={t['m_Pivot']}")
                    fid = t["m_Father"]["m_PathID"]
                    if fid:
                        ft = sf.objects[fid].read_typetree()
                        print(f"    parent={go_name(sf, ft)}, children:")
                        for ch in ft["m_Children"]:
                            ct = sf.objects[ch["m_PathID"]].read_typetree()
                            print(f"      {go_name(sf, ct)}: sizeDelta={ct['m_SizeDelta']} pos={ct['m_AnchoredPosition']}")
                elif kind == "MonoBehaviour" and "m_PreserveAspect" in t:
                    print(f"    Image m_Type={t.get('m_Type')} m_PreserveAspect={t['m_PreserveAspect']} sprite={t.get('m_Sprite')}")
                    if not a.inspect:
                        t["m_PreserveAspect"] = True
                        co.save_typetree(t)
                        changed.add(sf)
                        print("    -> m_PreserveAspect = 1")
            except Exception as e:
                print(f"    component skipped ({type(e).__name__}: {e})")


def process(path, a, logos, outdir):
    print(f"\n== {path}")
    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp, [n for n in z.namelist() if n.startswith(DATA) and not n.endswith("/")])
        env = UnityPy.load(os.path.join(tmp, DATA))
        changed = set()
        for sf in env.assets:
            for o in list(sf.objects.values()):
                if o.type.name == "Sprite":
                    do_sprite(o, a, logos, changed)
            do_clublogo(sf, a, changed)
        for sf in changed:
            dest = os.path.join(outdir, DATA + os.path.basename(sf.name))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(sf.save())
            print("WROTE", dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apk")
    ap.add_argument("--obb")
    ap.add_argument("--logos")
    ap.add_argument("--out", default="patched")
    ap.add_argument("--skip", default="")
    ap.add_argument("--inspect", action="store_true")
    a = ap.parse_args()
    a.skip = set(filter(None, a.skip.split(",")))
    logos = {}
    if a.logos:
        for f in os.listdir(a.logos):
            n, e = os.path.splitext(f)
            if e.lower() == ".png":
                logos[n] = os.path.join(a.logos, f)
    if a.apk:
        process(a.apk, a, logos, os.path.join(a.out, "apk"))
    if a.obb:
        process(a.obb, a, logos, os.path.join(a.out, "obb"))


if __name__ == "__main__":
    main()
