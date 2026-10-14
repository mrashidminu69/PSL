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

    # Merged file dhoondo (global variable use NA karo)
    merged_file = MERGED
    if not os.path.exists(merged_file):
        for f in os.listdir('.'):
            if f.endswith('.assets'):
                print(f"[!] {MERGED} nahi mila, lekin {f} mila")
                merged_file = f
                break
        else:
            print("[X] Merged file nahi mili!")
            return

    print(f"[✓] Merged: {merged_file} ({os.path.getsize(merged_file)} bytes)")

    # Logos extract
    logos_dir = "logos"
    os.makedirs(logos_dir, exist_ok=True)
    with zipfile.ZipFile(LOGOS_ZIP, 'r') as z:
        z.extractall(logos_dir)

    logos = [f for f in os.listdir(logos_dir) if f.lower().endswith('.png')]
    print(f"[*] Logos: {len(logos)}")

    # Load
    env = UnityPy.load(merged_file)

    # Textures ki list
    textures = []
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            try:
                data = obj.read()
                textures.append(data.m_Name)
            except:
                pass

    print(f"[*] Total textures: {len(textures)}")
    print("[*] Pehli 30 textures:")
    for t in textures[:30]:
        print(f"    - {t}")

    # Replace
    count = 0
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            try:
                data = obj.read()
                name = data.m_Name

                for logo in logos:
                    logo_base = os.path.splitext(logo)[0]
                    if logo_base in name:
                        png_path = os.path.join(logos_dir, logo)
                        new_img = Image.open(png_path).convert("RGBA")
                        if new_img.size != (data.m_Width, data.m_Height):
                            new_img = new_img.resize((data.m_Width, data.m_Height))

                        print(f"[+] Replacing: {name}  <-  {logo}")
                        try:
                            data.image = new_img
                            data.save()
                            count += 1
                        except Exception as e:
                            print(f"[!] Save error: {e}")
                        break
            except Exception as e:
                print(f"[!] Error: {e}")

    print(f"\n[*] Total replaced: {count}")

    if count == 0:
        print("[!] Koi logo nahi mila")
        return

    # Save
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
