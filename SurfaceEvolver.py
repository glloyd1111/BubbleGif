import os
import subprocess
from PIL import Image

# --------- PATHS (EDIT THESE) ---------
ps_folder = r"C:\Scranton\2025-2026\Surface_Evolver\Evolver"
gs_exe = r"C:\Scranton\2025-2026\Surface_Evolver\gs10070w32.exe"
output_gif = os.path.join(ps_folder, "animation.gif")

# --------- STEP 1: Convert PS → PNG ---------
png_files = []

ps_files = sorted([f for f in os.listdir(ps_folder) if f.endswith(".ps")])

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

# --------- STEP 2: Create GIF ---------
images = [Image.open(png) for png in png_files]

images[0].save(
    output_gif,
    save_all=True,
    append_images=images[1:],
    duration=80,  # milliseconds per frame
    loop=0
)

print(f"\nGIF created: {output_gif}")