IMPORTANT: You need to download the Python Embeddable Package and place it here.

1. Download "Windows embeddable package (64-bit)" from https://www.python.org/downloads/windows/
   (e.g., python-3.11.x-embed-amd64.zip)

2. Extract all files from the zip into this folder (d:\Wand\python_env).
   You should see 'python.exe' directly in this folder.

3. Locate the file 'python3xx._pth' (e.g., python311._pth) in this folder.
   Open it with a text editor and uncomment the line 'import site' (remove the #).
   This is required to install and use third-party packages.

4. Install pip (optional but recommended for installing requirements):
   - Download get-pip.py: https://bootstrap.pypa.io/get-pip.py
   - Run: .\python.exe get-pip.py

5. Install your project requirements:
   - Run: .\python.exe -m pip install -r ..\src\backend\requirements.txt -t .\Lib\site-packages
   (Note: You might need to create the 'Lib\site-packages' folder manually if it doesn't exist, or pip might create it inside 'Lib' or directly in root depending on config. 
    Ideally, for embeddable python, installing to a subfolder and adding it to .pth or sys.path is cleaner, 
    but simply running pip install -r ... -t . (current dir) also works for simple setups.)
