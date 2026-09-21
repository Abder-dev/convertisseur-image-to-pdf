"""Convertir des images en un PDF avec une interface Tkinter."""

from pathlib import Path
import os
import tempfile
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageOps

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_DISPONIBLE = True
except ImportError:
    HEIC_DISPONIBLE = False


def preparer_page(image, format_a4):
    """Corriger la rotation et remplacer la transparence par du blanc."""
    image = ImageOps.exif_transpose(image)
    rgba = image.convert("RGBA")
    page = Image.new("RGB", rgba.size, "white")
    page.paste(rgba, mask=rgba.getchannel("A"))
    if format_a4:
        # A4 à 150 points par pouce, avec une marge de 10 mm environ.
        feuille = Image.new("RGB", (1240, 1754), "white")
        page.thumbnail((1122, 1636), Image.Resampling.LANCZOS)
        position = ((1240 - page.width) // 2, (1754 - page.height) // 2)
        feuille.paste(page, position)
        page.close()
        return feuille
    return page


def convertir_images(chemins, destination, format_a4=True):
    """Une page par image ; toutes les pages des TIFF sont conservées."""
    if not chemins:
        raise ValueError("Ajoute au moins une image.")
    destination = Path(destination).resolve()
    if destination in [Path(p).resolve() for p in chemins]:
        raise ValueError("Le PDF ne peut pas remplacer une image source.")
    pages = []
    temporaire = None
    try:
        for chemin in chemins:
            try:
                with Image.open(chemin) as image:
                    # Les GIF/WebP animés donnent seulement leur première image.
                    nombre = getattr(image, "n_frames", 1) if image.format == "TIFF" else 1
                    for index in range(nombre):
                        image.seek(index)
                        pages.append(preparer_page(image, format_a4))
            except Exception as erreur:
                raise ValueError(
                    f"Impossible de lire « {Path(chemin).name} ».\n"
                    "Format non pris en charge, image trop grande ou fichier abîmé.\n"
                    f"Détail : {erreur}"
                ) from erreur

        # Écrire d'abord un fichier temporaire : un échec ne détruit pas
        # un éventuel PDF déjà présent à la destination.
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".pdf", delete=False) as fichier:
            temporaire = Path(fichier.name)
        pages[0].save(temporaire, "PDF", save_all=True, append_images=pages[1:],
                      resolution=150.0, quality=95)
        os.replace(temporaire, destination)
        return len(pages)
    finally:
        for page in pages:
            page.close()
        if temporaire is not None:
            temporaire.unlink(missing_ok=True)


class Convertisseur:
    def __init__(self, fenetre):
        self.fenetre = fenetre
        fenetre.report_callback_exception = self.afficher_erreur
        self.chemins = []
        self.travail = None
        # Le calcul s'effectue en arrière-plan pour garder la fenêtre réactive.
        self.executeur = ThreadPoolExecutor(max_workers=1)
        fenetre.title("Images vers PDF")
        fenetre.geometry("780x530")
        fenetre.minsize(640, 460)
        fenetre.protocol("WM_DELETE_WINDOW", self.fermer)

        cadre = ttk.Frame(fenetre, padding=24)
        cadre.pack(fill="both", expand=True)
        ttk.Label(cadre, text="Images vers PDF", font=("Helvetica", 24, "bold")).pack(anchor="w")
        ttk.Label(cadre, text="Ajoute tes images, choisis leur ordre, puis crée ton PDF.").pack(anchor="w", pady=(6, 16))
        formats = "JPEG, PNG, WebP, GIF, BMP, TIFF, ICO, AVIF"
        formats += " et HEIC/HEIF" if HEIC_DISPONIBLE else " — HEIC : installer pillow-heif"
        ttk.Label(cadre, text=formats, wraplength=690).pack(anchor="w", pady=(0, 10))

        ligne = ttk.Frame(cadre)
        ligne.pack(fill="both", expand=True)
        self.liste = tk.Listbox(ligne, selectmode=tk.EXTENDED, exportselection=False,
                                font=("Helvetica", 12), height=10)
        self.liste.pack(side="left", fill="both", expand=True)
        barre = ttk.Scrollbar(ligne, command=self.liste.yview)
        barre.pack(side="right", fill="y")
        self.liste.configure(yscrollcommand=barre.set)

        actions = ttk.Frame(cadre)
        actions.pack(fill="x", pady=12)
        self.boutons = []
        for texte, commande in [("Ajouter des images", self.ajouter), ("Retirer", self.retirer),
                                ("Monter", lambda: self.deplacer(-1)),
                                ("Descendre", lambda: self.deplacer(1))]:
            bouton = ttk.Button(actions, text=texte, command=commande)
            bouton.pack(side="left", padx=(0, 8))
            self.boutons.append(bouton)

        self.a4 = tk.BooleanVar(value=True)
        self.option = ttk.Checkbutton(cadre, text="Pages A4 avec marges (sinon : taille proportionnelle à l’image)", variable=self.a4)
        self.option.pack(anchor="w", pady=(0, 6))
        ttk.Label(cadre, text="GIF animés : première image • TIFF : toutes les pages • Traitement 100 % local",
                  wraplength=690).pack(anchor="w")
        self.etat = tk.StringVar(value="Aucune image sélectionnée.")
        ttk.Label(cadre, textvariable=self.etat).pack(anchor="w", pady=10)
        self.exporter = ttk.Button(cadre, text="Créer le PDF…", command=self.export)
        self.exporter.pack(anchor="e")
        fenetre.after(200, self.activer_fenetre)

    def activer_fenetre(self):
        self.fenetre.lift()
        self.fenetre.focus_force()

    def afficher_erreur(self, type_erreur, erreur, trace):
        """Rendre visible une erreur de bouton, au lieu de sembler ne rien faire."""
        traceback.print_exception(type_erreur, erreur, trace)
        messagebox.showerror("Erreur", str(erreur), parent=self.fenetre)

    def actualiser(self):
        self.liste.delete(0, tk.END)
        for index, chemin in enumerate(self.chemins, start=1):
            self.liste.insert(tk.END, f"{index}. {Path(chemin).name}")
        self.etat.set(f"{len(self.chemins)} image(s) sélectionnée(s).")

    def ajouter(self):
        chemins = filedialog.askopenfilenames(parent=self.fenetre, title="Choisir des images", filetypes=[("Tous les fichiers", "*")])
        for chemin in chemins:
            if chemin not in self.chemins:
                self.chemins.append(chemin)
        self.actualiser()

    def retirer(self):
        if not self.liste.curselection():
            self.etat.set("Sélectionne une image dans la liste pour la retirer.")
            return
        for index in reversed(self.liste.curselection()):
            del self.chemins[index]
        self.actualiser()

    def deplacer(self, direction):
        selection = self.liste.curselection()
        if len(selection) != 1:
            self.etat.set("Sélectionne une seule image pour la déplacer.")
            return
        index = selection[0]
        voisin = index + direction
        if 0 <= voisin < len(self.chemins):
            self.chemins[index], self.chemins[voisin] = self.chemins[voisin], self.chemins[index]
            self.actualiser()
            self.liste.selection_set(voisin)
            self.liste.see(voisin)

    def export(self):
        if not self.chemins:
            messagebox.showinfo("Aucune image", "Ajoute au moins une image.", parent=self.fenetre)
            return
        destination = filedialog.asksaveasfilename(parent=self.fenetre, title="Enregistrer le PDF", defaultextension=".pdf",
                                                   initialfile="mes_images.pdf", filetypes=[("Document PDF", "*.pdf")])
        if not destination:
            return
        self.destination = destination
        for bouton in self.boutons + [self.exporter, self.option]:
            bouton.configure(state="disabled")
        self.etat.set("Conversion en cours…")
        self.travail = self.executeur.submit(convertir_images, self.chemins.copy(), destination, self.a4.get())
        self.fenetre.after(100, self.verifier_conversion)

    def verifier_conversion(self):
        if not self.travail.done():
            self.fenetre.after(100, self.verifier_conversion)
            return
        for bouton in self.boutons + [self.exporter, self.option]:
            bouton.configure(state="normal")
        try:
            nombre = self.travail.result()
            self.etat.set(f"PDF créé : {nombre} page(s).")
            messagebox.showinfo("Conversion terminée", f"{nombre} page(s) enregistrée(s) dans :\n{self.destination}", parent=self.fenetre)
        except Exception as erreur:
            self.etat.set("Échec de la conversion. Tes images sont conservées.")
            messagebox.showerror("Conversion impossible", str(erreur), parent=self.fenetre)
        self.travail = None

    def fermer(self):
        if self.travail is not None:
            messagebox.showinfo("Conversion en cours", "Attends la fin de la conversion avant de fermer.", parent=self.fenetre)
            return
        self.executeur.shutdown(wait=False)
        self.fenetre.destroy()


if __name__ == "__main__":
    fenetre = tk.Tk()
    Convertisseur(fenetre)
    fenetre.mainloop()
