# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew, gstreamer  # Kivy imports

block_cipher = None


a = Analysis(
    ['particle-distortion-analysis.py'],
    pathex=['.'],
    binaries=[],
    datas=[('*.kv', '.'), ('*.txt', '.'), ('*.ico', '.')],
    hiddenimports=['plyer.platforms.win.filechooser', 'matplotlib.backends.backend_svg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.datas += [('icon.png','.\\resources\\icon.png','DATA'),
            ('icon_128x128.png','.\\resources\\icon_128x128.png','DATA'),
            ('icon.ico','.\\resources\\icon.ico','DATA'),
            ('axis_overlay.png','.\\resources\\axis_overlay.png','DATA'),
            ('example_image.png','.\\resources\\example_image.png','DATA'),
            ('example_image_0.png','.\\resources\\example_image_0.png','DATA'),
            ('export.png','.\\resources\\export.png','DATA'),
            ('masp_diagram.png','.\\resources\\masp_diagram.png','DATA'),
            ('open_folder.png','.\\resources\\open_folder.png','DATA'),
            ('reset_btn.png','.\\resources\\reset_btn.png','DATA'),
            ('scroll_shift.png','.\\resources\\scroll_shift.png','DATA'),
            ('scroll.png','.\\resources\\scroll.png','DATA'),
            ('wasd_shift.png','.\\resources\\wasd_shift.png','DATA'),
            ('wasd.png','.\\resources\\wasd.png','DATA'),
            ('white_circle.png','.\\resources\\white_circle.png','DATA'),
            ('DejaVuSans.ttf','.\\resources\\DejaVuSans.ttf','DATA'),
            ('Inter.ttf','.\\resources\\Inter.ttf','DATA'),
            ('info_page_text.txt','.\\resources\\info_page_text.txt','DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],  # Kivy binaries
    [],
    name='PCT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='.\\resources\\icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
