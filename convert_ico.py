from PIL import Image
import sys
import os

def convert_to_ico(png_path, ico_path):
    img = Image.open(png_path)
    # Resize to common icon sizes
    icon_sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"Icone salvo em: {ico_path}")

if __name__ == "__main__":
    png = sys.argv[1]
    ico = sys.argv[2]
    convert_to_ico(png, ico)
鼓
