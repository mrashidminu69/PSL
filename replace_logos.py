import UnityPy
import os
import zipfile
from PIL import Image

# ====== FILES ======
MERGED = "sharedassets0_merged.assets"
LOGOS_ZIP = "logos.zip"
OUTPUT_ZIP = "patched_sharedassets0.zip"
PART_SIZE = 1048576  # 1 MB
# ===================

def main():
    print("[*] Shuru...")

    # Logos ZIP extract karo
    logos_dir = "logos"
    os.makedirs(logos_dir, exist_ok=True)
    with zipfile.ZipFile(LOGOS_ZIP, 'r') as z:
        z.extractall(logos_dir)
    print(f"[*] Logos extract: {logos_dir}")

    # Saare logos ki list
    logos = [f for f in os.listdir(logos_dir) if f.lower().endswith('.png')]
    print(f"[*] Total logos: {len(logos)}\n")

    # Merged file load karo
    print(f"[*] Loading: {MERGED}")
    env = UnityPy.load(MERGED)

    count = 0
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            try:
                data = obj.read()
                name = data.m_Name

                # Har logo ke saath match karo
                for logo in logos:
                    logo_base = os.path.splitext(logo)[0]

                    if logo_base in name:
                        png_path = os.path.join(logos_dir, logo)
                        new_img = Image.open(png_path).convert("RGBA")

                        # Resize (agar zaroorat ho)
                        if new_img.size != (data.m_Width, data.m_Height):
                            new_img = new_img.resize((data.m_Width, data.m_Height))

                        print(f"[+] Replacing: {name}  <-  {logo}")
                        data.image = new_img
                        data.save()
                        count += 1
                        break
            except Exception as e:
                print(f"[!] Error: {e}")

    if count == 0:
        print("[!] Koi logo nahi mila")
        return

    # Nayi merged file save karo
    patched = "sharedassets0_merged_patched.assets"
    with open(patched, 'wb') as f:
        f.write(env.file.save())
    print(f"\n[✓] Patched: {patched}")
    print(f"[✓] Size: {os.path.getsize(patched)} bytes")

    # 25 parts banao
    print(f"\n[*] Parts bana rahe hain...")
    with open(patched, 'rb') as f:
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
        part_name = f"sharedassets0.assets.split{i}"
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
