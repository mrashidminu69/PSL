import UnityPy
import os
import zipfile
from PIL import Image

# ====== FILES ======
ZIP_FILE = "160.zip"
NEW_PNG = "diff_HH_Uniform_209.png"
TARGET = "diff_HH_Uniform"
OUTPUT_ZIP = "patched_160.zip"
# ===================

def main():
    print("[*] Shuru...")

    # ZIP extract karo
    extract_dir = "extracted"
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(ZIP_FILE, 'r') as z:
        z.extractall(extract_dir)
    print(f"[*] ZIP extract ho gayi: {extract_dir}")

    # Saari split files dhoondo
    splits = sorted([f for f in os.listdir(extract_dir) if f.startswith("sharedassets2.assets.split")])
    print(f"[*] Total splits: {len(splits)}\n")

    # Nayi PNG load karo
    new_img = Image.open(NEW_PNG).convert("RGBA")
    print(f"[*] Nayi PNG: {new_img.size}\n")

    # Har split mein replace karo
    total = 0
    for fname in splits:
        fpath = os.path.join(extract_dir, fname)
        try:
            env = UnityPy.load(fpath)
        except:
            continue

        replaced_in_file = 0
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                try:
                    data = obj.read()
                    if TARGET in data.m_Name:
                        img = new_img
                        if img.size != (data.m_Width, data.m_Height):
                            img = img.resize((data.m_Width, data.m_Height))

                        raw_data = img.tobytes()
                        data.m_TextureFormat = 47
                        data.m_Width = img.size[0]
                        data.m_Height = img.size[1]
                        data.m_CompleteImageSize = len(raw_data)
                        data.m_MipMap = False
                        data.m_MipCount = 1
                        data.m_IsReadable = True

                        if hasattr(data, 'm_TextureData'):
                            data.m_TextureData = raw_data

                        data.save()
                        replaced_in_file += 1
                except Exception as e:
                    pass

        if replaced_in_file > 0:
            with open(fpath, 'wb') as f:
                f.write(env.file.save())
            print(f"[+] {fname}: {replaced_in_file} replace")
            total += replaced_in_file

    # Nayi ZIP banao
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_STORED) as z:
        for fname in splits:
            z.write(os.path.join(extract_dir, fname), fname)

    print(f"\n[✓] Total replaced: {total}")
    print(f"[✓] Nayi ZIP: {OUTPUT_ZIP}")

if __name__ == "__main__":
    main()
