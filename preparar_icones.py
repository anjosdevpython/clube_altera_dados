from PIL import Image
import os

def remove_white_background(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for item in data:
        # Se for muito próximo do branco, torna transparente
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"PNG transparente salvo em: {output_path}")

def create_ico(png_path, ico_path):
    img = Image.open(png_path)
    icon_sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"ICO salvo em: {ico_path}")

if __name__ == "__main__":
    raw_png = r"C:\Users\allan.anjos\.gemini\antigravity\brain\f8807404-9519-48d9-8db6-444231b1e356\clube_icon_transparent_1772738055827.png"
    final_png = "clube_icon.png"
    final_ico = "clube_icon.ico"
    
    remove_white_background(raw_png, final_png)
    create_ico(final_png, final_ico)
鼓
