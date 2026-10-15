import UnityPy
import os
import zipfile
import gdown

# ====== FILES ======
LEVEL_FILES = ["level1.split0", "level1.split1"]
NEW_SIZE = (320.0, 320.0)  # Naya frame size
TARGET_PATH_IDS = [6751, 6757, 8604]  # ClubLogo ke RectTransform
OUTPUT_ZIP = "patched_level1.zip"
# ===================

def main():
    print("[*] Frame edit shuru...")
    print(f"[*] Naya size: {NEW_SIZE}")

    patched_files = []

    for fname in LEVEL_FILES:
        if not os.path.exists(fname):
            print(f"[!] Nahi mili: {fname}")
            continue

        try:
            env = UnityPy.load(fname)
        except Exception as e:
            print(f"[!] Load fail: {fname} - {e}")
            continue

        count = 0
        for obj in env.objects:
            if obj.type.name == "RectTransform":
                try:
                    d = obj.read()
                    if obj.path_id in TARGET_PATH_IDS:
                        old_size = d.m_SizeDelta
                        d.m_SizeDelta = NEW_SIZE
                        d.save()
                        count += 1
                        print(f"[+] {fname}: {obj.path_id}  {old_size.x}x{old_size.y} -> {NEW_SIZE[0]}x{NEW_SIZE[1]}")
                except Exception as e:
                    pass

        patched = f"patched_{fname}"
        with open(patched, 'wb') as f:
            f.write(env.file.save())
        patched_files.append(patched)
        print(f"[✓] Save: {patched}  ({count} changes)\n")

    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_STORED) as z:
        for f in patched_files:
            z.write(f, os.path.basename(f))
            print(f"[+] ZIP: {f}")

    print(f"\n[✓] Output: {OUTPUT_ZIP}")

if __name__ == "__main__":
    main()
