import UnityPy
import os
import zipfile
from PIL import Image

# ====== FILES ======
MERGED = "sharedassets2_merged.assets"
NEW_PNG = "diff_HH_Uniform_209.png"
TARGET = "diff_HH_Uniform"
OUTPUT_ZIP = "patched_160_parts.zip"
PART_SIZE = 1048576  # 1 MB (1024 * 1024)
# ===================

def main():
    print("[*] Shuru...")

    # Nayi PNG load karo
    new_img = Image.open(NEW_PNG).convert("RGBA")
    print(f"[*] PNG: {new_img.size}\n")

    # Merged file load karo
    print(f"[*] Loading: {MERGED}")
    env = UnityPy.load(MERGED)

    count = 0
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            try:
                data = obj.read()
                if TARGET in data.m_Name:
                    print(f"[+] Replacing: {data.m_Name}  (format={data.m_TextureFormat})")
                    data.image = new_img
                    data.save()
                    count += 1
            except Exception as e:
                print(f"[!] Error: {e}")

    if count == 0:
        print("[!] Koi texture nahi mili")
        return

    # Nayi merged file save karo
    patched_merged = "sharedassets2_merged_patched.assets"
    with open(patched_merged, 'wb') as f:
        f.write(env.file.save())
    print(f"\n[✓] Patched merged: {patched_merged}")
    print(f"[✓] Size: {os.path.getsize(patched_merged)} bytes")

    # 160 parts mein todo
    print(f"\n[*] 160 parts bana rahe hain...")
    with open(patched_merged, 'rb') as f:
        data = f.read()

    total_size = len(data)
    num_parts = (total_size + PART_SIZE - 1) // PART_SIZE
    print(f"[*] Total size: {total_size} bytes")
    print(f"[*] Parts: {num_parts}")

    parts_dir = "parts"
    os.makedirs(parts_dir, exist_ok=True)

    for i in range(num_parts):
        start = i * PART_SIZE
        end = min(start + PART_SIZE, total_size)
        part_data = data[start:end]
        part_name = f"sharedassets2.assets.split{i}"
        with open(os.path.join(parts_dir, part_name), 'wb') as f:
            f.write(part_data)

    # ZIP banao
    print(f"\n[*] ZIP bana rahe hain...")
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_STORED) as z:
        for fname in sorted(os.listdir(parts_dir)):
            z.write(os.path.join(parts_dir, fname), fname)

    print(f"\n[✓] ZIP: {OUTPUT_ZIP}")
    print(f"[✓] Size: {os.path.getsize(OUTPUT_ZIP)} bytes")

if __name__ == "__main__":
    main()
