import UnityPy
import os
import zipfile
from PIL import Image

MERGED = "sharedassets0_merged.assets"
LOGOS_ZIP = "logos.zip"
OUTPUT_ZIP = "patched_sharedassets0.zip"
PART_SIZE = 1048576

def main():
    print("[*] Shuru...")

    merged_file = MERGED
    if not os.path.exists(merged_file):
        for f in os.listdir('.'):
            if f.endswith('.assets'):
                merged_file = f
                break

    print(f"[✓] Merged: {merged_file}")

    logos_dir = "logos"
    os.makedirs(logos_dir, exist_ok=True)
    with zipfile.ZipFile(LOGOS_ZIP, 'r') as z:
        z.extractall(logos_dir)

    logos = [f for f in os.listdir(logos_dir) if f.lower().endswith('.png')]
    print(f"[*] Logos: {len(logos)}")

    env = UnityPy.load(merged_file)

    count = 0
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            try:
                data = obj.read()
                tex_name = data.m_Name
                tex_w, tex_h = data.m_Width, data.m_Height

                for logo in logos:
                    logo_base = os.path.splitext(logo)[0]

                    # Match: texture ka naam logo ke naam mein hai
                    if tex_name in logo_base:
                        png_path = os.path.join(logos_dir, logo)
                        logo_img = Image.open(png_path).convert("RGBA")

                        # Nayi canvas banao (texture ke size ka)
                        canvas = Image.new("RGBA", (tex_w, tex_h), (0, 0, 0, 0))

                        # Logo ko center mein fit karo (aspect ratio maintain karte hue)
                        logo_w, logo_h = logo_img.size
                        ratio = min(tex_w / logo_w, tex_h / logo_h)
                        new_w = int(logo_w * ratio)
                        new_h = int(logo_h * ratio)
                        logo_resized = logo_img.resize((new_w, new_h), Image.LANCZOS)

                        # Center mein paste karo
                        x = (tex_w - new_w) // 2
                        y = (tex_h - new_h) // 2
                        canvas.paste(logo_resized, (x, y), logo_resized)

                        print(f"[+] Replacing: {tex_name} ({tex_w}x{tex_h})  <-  {logo} ({logo_w}x{logo_h})")

                        data.image = canvas
                        data.save()
                        count += 1
                        break
            except Exception as e:
                print(f"[!] Error: {e}")

    print(f"\n[*] Total replaced: {count}")

    if count == 0:
        print("[!] Koi logo nahi mila")
        return

    patched = "sharedassets0_merged_patched.assets"
    with open(patched, 'wb') as f:
        f.write(env.file.save())

    with open(patched, 'rb') as f:
        data = f.read()

    total_size = len(data)
    num_parts = (total_size + PART_SIZE - 1) // PART_SIZE

    parts_dir = "parts"
    os.makedirs(parts_dir, exist_ok=True)

    for i in range(num_parts):
        start = i * PART_SIZE
        end = min(start + PART_SIZE, total_size)
        with open(os.path.join(parts_dir, f"sharedassets0.assets.split{i}"), 'wb') as f:
            f.write(data[start:end])

    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_STORED) as z:
        for fname in sorted(os.listdir(parts_dir)):
            z.write(os.path.join(parts_dir, fname), fname)

    print(f"\n[✓] ZIP: {OUTPUT_ZIP}")

if __name__ == "__main__":
    main()
