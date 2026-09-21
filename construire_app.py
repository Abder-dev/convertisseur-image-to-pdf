"""Créer une application Mac autonome, sans compilateur ni outils Apple."""

from pathlib import Path
import plistlib
import shutil
import sys
import sysconfig


projet = Path(__file__).resolve().parent
application = projet / "dist" / "Images vers PDF.app"
if application.exists():
    raise SystemExit("Une application existe déjà dans dist : déplace-la avant de reconstruire.")

contenu = application / "Contents"
ressources = contenu / "Resources"
executables = contenu / "MacOS"
executables.mkdir(parents=True)
ressources.mkdir()

# Le Python fourni ici est une distribution autonome et déplaçable.
base = Path(sys.base_prefix)
runtime = ressources / "python"
version = f"python{sys.version_info.major}.{sys.version_info.minor}"
shutil.copytree(base / "lib", runtime / "lib",
                ignore=shutil.ignore_patterns("site-packages", "__pycache__", "*.a", "pkgconfig"))
(runtime / "bin").mkdir()
shutil.copy2(base / "bin" / version, runtime / "bin" / version)

# Copier seulement les bibliothèques utilisées par le convertisseur.
paquets = Path(sysconfig.get_paths()["purelib"])
destination = runtime / "lib" / version / "site-packages"
destination.mkdir()
for motif in ["PIL", "pillow.libs", "pillow_heif", "pillow_heif.libs", "_pillow_heif*.so"]:
    for source in paquets.glob(motif):
        if source.is_dir():
            shutil.copytree(source, destination / source.name,
                            ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, destination / source.name)
shutil.copy2(projet / "convertisseur.py", ressources / "convertisseur.py")
shutil.copy2(projet / "assets" / "icone.icns", ressources / "icone.icns")

lanceur = executables / "Images vers PDF"
lanceur.write_text(f'''#!/bin/sh
set -eu
ressources="$(cd "$(dirname "$0")/../Resources" && pwd)"
export TCL_LIBRARY="$ressources/python/lib/tcl9.0"
export TK_LIBRARY="$ressources/python/lib/tk9.0"
exec "$ressources/python/bin/{version}" -I "$ressources/convertisseur.py"
''')
lanceur.chmod(0o755)

with (contenu / "Info.plist").open("wb") as fichier:
    plistlib.dump({
        "CFBundleName": "Images vers PDF",
        "CFBundleDisplayName": "Images vers PDF",
        "CFBundleExecutable": "Images vers PDF",
        "CFBundleIdentifier": "fr.local.imagesverspdf",
        "CFBundleIconFile": "icone.icns",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0",
        "CFBundleVersion": "1",
        "NSHighResolutionCapable": True,
    }, fichier)
print(f"Application créée : {application}")
