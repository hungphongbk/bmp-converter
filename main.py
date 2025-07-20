import os
from PIL import Image
from tkinter import Tk, filedialog

def select_folder():
    root = Tk()
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(title='Select Folder')
    return folder_selected

def convert_bmp_to_tiff(root_folder):
    for subdir, _, files in os.walk(root_folder):
        for filename in files:
            if filename.lower().endswith('.bmp'):
                bmp_path = os.path.join(subdir, filename)
                tiff_path = os.path.splitext(bmp_path)[0] + '.tiff'
                with Image.open(bmp_path) as img:
                    # Save as TIFF; Pillow uses lossless compression for TIFF by default
                    img.save(tiff_path, format='TIFF', compression='none')
                print(f'Converted: {bmp_path} -> {tiff_path}')

if __name__ == '__main__':
    folder_path = select_folder()
    if folder_path:
        convert_bmp_to_tiff(folder_path)
    else:
        print('No folder selected.')