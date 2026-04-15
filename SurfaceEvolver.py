#-------------------------------------------
# Surface Evolver Conversion
# 
# Converts .ps files to .png then to a gif 
# using GhostScript and Pillow.
#-------------------------------------------

import os
import subprocess
from PIL import Image

# --------- PATHS (EDIT THESE) ---------
ps_folder = r"C:\Scranton\2025-2026\Surface_Evolver\ps_folder"  # Location of .ps files
gs_exe = r"C:\Scranton\2025-2026\Surface_Evolver\gs10.07.0\bin\gswin32c.exe" # Location of PIL
output_gif = os.path.join(ps_folder, "animation.gif") # Output location

# --------- Convert PS → PNG ---------
png_files = []

ps_files = sorted([f for f in os.listdir(ps_folder) if f.endswith(".ps")]) # Alphabetical sorting

for ps_file in ps_files:
    ps_path = os.path.join(ps_folder, ps_file)
    png_path = os.path.join(ps_folder, ps_file.replace(".ps", ".png"))

    cmd = [
        gs_exe,
        "-sDEVICE=pngalpha",
        "-r400",
        "-dGraphicsAlphaBits=4",
        "-dTextAlphaBits=4",
        "-o", png_path,
        ps_path
    ]

    print(f"Converting {ps_file} → PNG...")
    subprocess.run(cmd, check=True)

    png_files.append(png_path)

# --------- Create GIF ---------
images = [Image.open(png).convert("RGBA") for png in png_files]

# Convert to palette mode
frames = [img.convert("P", palette=Image.ADAPTIVE) for img in images]

frames[0].save(
    output_gif,
    save_all=True,
    append_images=frames[1:],
    duration=80,
    loop=0,
    disposal=2
)

print(f"\nGIF created: {output_gif}")
