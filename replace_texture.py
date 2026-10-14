import UnityPy
from PIL import Image
import os

# ====== FILES ======
SPLIT_FILE = "sharedassets2.assets.split0"
NEW_PNG = "diff_HH_Uniform_209.png"
TARGET = "diff_HH_Uniform"
OUTPUT = "patched_split0"
# ===================

def main():
    print("[*] Texture replace shuru...")
    print(f"[*] Split file: {SPLIT_FILE}")
    print(f"[*] Nayi PNG: {NEW_PNG}")
    print(f"[*] Target: {TARGET}\n")

    # Nayi PNG load karo
    new_img = Image.open(NEW_PNG).convert("RGBA")
    print(f"[*] PNG size: {new_img.size}")
    print(f"[*] PNG mode: {new_img.mode}\n")

    # Split file load karo
    env = UnityPy.load(SPLIT_FILE)

    count = 0
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            try:
                data = obj.read()
                if TARGET in data.m_Name:
                    print(f"[+] Mil gayi: {data.m_Name}")
                    print(f"    Purani size: {data.m_Width}x{data.m_Height}")
                    print(f"    Purani format: {data.m_TextureFormat}")

                    # Image resize karo (agar zaroorat ho)
                    img = new_img
                    if img.size != (data.m_Width, data.m_Height):
                        img = img.resize((data.m_Width, data.m_Height))
                        print(f"    Resize: {img.size}")

                    # Raw RGBA data
                    raw_data = img.tobytes()
                    print(f"    Raw data: {len(raw_data)} bytes")

                    # Format ko ASTC (47) rakho
                    data.m_TextureFormat = 47  # ASTC
                    data.m_Width = img.size[0]
                    data.m_Height = img.size[1]
                    data.m_CompleteImageSize = len(raw_data)
                    data.m_MipMap = False
                    data.m_MipCount = 1
                    data.m_IsReadable = True

                    # Direct data set karo
                    if hasattr(data, 'm_TextureData'):
                        data.m_TextureData = raw_data

                    data.save()
                    count += 1
                    print(f"    [✓] Replace ho gaya")
            except Exception as e:
                print(f"[!] Error: {e}")

    if count > 0:
        with open(OUTPUT, 'wb') as f:
            f.write(env.file.save())
        print(f"\n[✓] File save: {OUTPUT}")
        print(f"[✓] Size: {os.path.getsize(OUTPUT)} bytes")
    else:
        print(f"\n[!] Koi texture nahi mili")

if __name__ == "__main__":
    main()
