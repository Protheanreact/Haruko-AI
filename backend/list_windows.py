import pygetwindow as gw

print("Scanning windows...")
windows = gw.getAllTitles()
for w in windows:
    if w.strip():
        print(f"Window: '{w}'")
