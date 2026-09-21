# Images vers PDF

Application locale en Python, avec une fenêtre Tkinter. Les images ne sont jamais envoyées sur Internet.

## Application Mac prête à utiliser

L'application autonome est installée dans `~/Applications/Images vers PDF.app`.
Ouvrir **Images vers PDF** depuis Spotlight (⌘ + Espace) ou depuis le dossier
Applications du compte utilisateur. Pour la garder dans le Dock : clic droit
sur son icône ouverte, puis **Options → Garder dans le Dock**.

Cette copie contient Python, Tk et les bibliothèques d'images. Elle fonctionne
sans VS Code et sans le dossier du projet. Elle a été construite pour ce Mac
Apple Silicon ; sa compatibilité avec d'autres Mac n'a pas été testée.

Pour reconstruire après une modification du code : déplacer l'ancienne copie
de `dist/Images vers PDF.app`, puis lancer `.venv/bin/python construire_app.py`.
Le script utilise la distribution Python autonome actuelle et Tk 9 ; ce n'est
pas un outil générique pour toutes les installations de Python.
La nouvelle copie dans `dist` doit ensuite remplacer l'application installée,
une fois celle-ci fermée. Modifier le code du projet ne met pas automatiquement
à jour l'application déjà installée.

## Installation et lancement

Python 3.10 ou plus récent, avec Tkinter, est nécessaire. Dans le dossier du projet :

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python convertisseur.py
```

Sous Windows, activer l'environnement avec `.venv\Scripts\activate` et utiliser `python` à la place de `python3`.

### Lancement dans VS Code sur ce Mac

L'environnement `.venv` du projet utilise maintenant Python 3.12 et Tk 9.0.4.
L'ancien Python 3.10 avec Tk 8.6.12 présentait des problèmes de clics sur ce Mac.
Fermer toute ancienne fenêtre du convertisseur, puis appuyer sur **F5** et choisir
**Lancer le convertisseur**, ou exécuter `.venv/bin/python convertisseur.py` dans
un nouveau terminal du projet. Il n'est pas nécessaire de refaire l'installation.

Cet environnement s'appuie sur le Python local fourni dans le cache des outils
Codex. Si ce runtime est supprimé, recréer `.venv` avec une installation récente
de Python et de Tk. L'ancien environnement est conservé dans `.venv-python310`.

1. Cliquer sur **Ajouter des images** et sélectionner plusieurs fichiers.
2. Utiliser **Monter**, **Descendre** ou **Retirer** pour préparer la liste.
3. Garder l'option A4 pour imprimer, ou la décocher pour conserver les proportions et une taille de page liée à l'image (150 pixels par pouce).
4. Cliquer sur **Créer le PDF…** puis choisir l'emplacement.

## Formats et limites

- JPEG/JPG, PNG, WebP, GIF, BMP, TIFF, ICO, AVIF et HEIC/HEIF, ainsi que d'autres formats reconnus par Pillow. Certains décodeurs dépendent de l'installation et de la plateforme.
- HEIC/HEIF utilise `pillow-heif`, inclus dans les dépendances.
- Les TIFF multipages produisent plusieurs pages. Pour les GIF, WebP animés et les autres conteneurs, seule la première image est utilisée.
- La rotation EXIF est corrigée ; la transparence est remplacée par du blanc.
- Les images ne sont pas déformées ni recadrées. En A4, les grandes images sont réduites pour tenir sur la feuille.
- Les formats vectoriels SVG/AI, les fichiers RAW des appareils photo et les projets de logiciels de dessin ne sont pas pris en charge de manière générale. Les exporter en PNG ou JPEG avant conversion.
- Les pages sont gardées en mémoire pendant la conversion : pour de très gros lots, faire plusieurs PDF. Le PDF emploie une compression JPEG de qualité 95 : ce n'est pas une conservation sans perte.
- Un fichier illisible interrompt l'export avec son nom. Aucun fichier source n'est modifié et un PDF existant est remplacé seulement après une conversion réussie.

## Comprendre le code

`preparer_page` corrige l'orientation et prépare le fond blanc. `convertir_images` ouvre les fichiers dans l'ordre et rassemble les pages dans le PDF. La classe `Convertisseur` regroupe les boutons et les actions de la fenêtre. Un seul calcul en arrière-plan évite de bloquer la fenêtre pendant la conversion ; Tkinter reste piloté depuis le programme principal.

Documentation : [formats Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html) et [extension HEIF](https://pillow-heif.readthedocs.io/en/stable/pillow-plugin.html).
