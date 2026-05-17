# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from kivy.tools.packaging.pyinstaller_hooks import get_deps_all, hookspath, runtime_hooks
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

app_script = 'particle-distortion-analysis.py'

# copy_metadata ensures importlib.metadata.version() works at runtime for these packages
extra_datas = [
    ('resources/*', 'resources'),
    ('*.kv', '.'),
    ('*.txt', '.'),
] + copy_metadata('imageio') + copy_metadata('moviepy')

deps = get_deps_all()
deps['datas'] = deps.get('datas', []) + extra_datas
deps['hiddenimports'] = deps.get('hiddenimports', []) + [
    'plyer.platforms.macosx.filechooser',
    'moviepy.video.io.ffmpeg_reader',
    'moviepy.video.io.ffmpeg_tools',
    'moviepy.video.io.VideoFileClip',
    'nptdms',
    'pandas',
] + collect_submodules('kivy_deps')

a = Analysis(
    [app_script],
    pathex=['.'],
    binaries=deps.get('binaries', []),
    datas=deps['datas'],
    hiddenimports=deps['hiddenimports'],
    hookspath=hookspath(),
    runtime_hooks=runtime_hooks(),
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    exclude_binaries=True,
    name='PDA',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='PDA',
)

app = BUNDLE(
    coll,
    name='PDA.app',
    icon='resources/icon.icns',
    bundle_identifier='org.haig.particledistortionanalysis',
    info_plist={
        'CFBundleName': 'PDA',
        'CFBundleDisplayName': 'Particle Distortion Analysis',
        'CFBundleIdentifier': 'org.haig.particledistortionanalysis',
        'CFBundleVersion': '1.0.3',
        'CFBundleExecutable': 'PDA',
    },
)
