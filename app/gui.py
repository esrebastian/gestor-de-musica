import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from .scanner import find_duplicates, find_possible_duplicates, scan_folder
from .organizer import (
    organize,
    preview_organization,
    process_duplicates,
    validate_organization,
)


COLORS = {
    "background": "#0B0F0E",
    "surface": "#111715",
    "surface_alt": "#161F1C",
    "row": "#1C2622",
    "row_hover": "#24332D",
    "border": "#273832",
    "text": "#F3F4F6",
    "muted": "#9CA3AF",
    "subtle": "#6B7280",
    "lime": "#84E010",
    "lime_hover": "#99F018",
    "olive": "#4D7C0F",
    "cyan": "#22D3EE",
    "cyan_light": "#67E8F9",
    "cyan_deep": "#0891B2",
    "amber": "#F59E0B",
    "amber_dark": "#78350F",
    "coral": "#F87171",
    "coral_dark": "#7F1D1D",
    "track": "#273832",
    "selection": "#365314",
}


def asset_path(filename):
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return bundle_root / "assets" / filename


class GestionadorArchivosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gestionador de archivos")
        self.geometry("1080x700")
        self.minsize(780, 520)
        self.configure(fg_color=COLORS["background"])

        self.folder = ""
        self.songs = []
        self.duplicates = []
        self.possible_duplicates = []
        self.issues = []
        self._scan_running = False
        self._last_progress_percent = None
        self._active_filter = "all"

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.set_application_icon()

        self.create_widgets()

    def set_application_icon(self):
        icon_path = asset_path("gestionador_archivos.ico")
        logo_path = asset_path("gestionador_archivos.png")

        if logo_path.is_file():
            self._application_icon = tk.PhotoImage(file=str(logo_path)).subsample(8, 8)
            self.iconphoto(True, self._application_icon)
        if icon_path.is_file():
            try:
                self.iconbitmap(default=str(icon_path))
            except tk.TclError:
                if not logo_path.is_file():
                    raise

    def set_window_icon(self, window):
        icon_path = asset_path("gestionador_archivos.ico")
        logo_path = asset_path("gestionador_archivos.png")
        if logo_path.is_file():
            window._application_icon = tk.PhotoImage(file=str(logo_path)).subsample(8, 8)
            window.iconphoto(True, window._application_icon)
        if icon_path.is_file():
            try:
                window.iconbitmap(default=str(icon_path))
            except tk.TclError:
                if not logo_path.is_file():
                    raise

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0)
        header.pack(fill="x")
        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.pack(side="left", padx=18, pady=10)
        self._logo_image = tk.PhotoImage(
            file=str(asset_path("gestionador_archivos.png"))
        ).subsample(8, 8)
        ctk.CTkLabel(header_left, text="", image=self._logo_image).pack(side="left")
        brand = ctk.CTkFrame(header_left, fg_color="transparent")
        brand.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(
            brand,
            text="Gestionador de archivos",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Tus carpetas ordenadas en un clic. Olvídate de limpiar a mano",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["lime"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="MODO MÚSICA  ·  OTRAS CATEGORÍAS PRÓXIMAMENTE",
            text_color=COLORS["cyan"],
            fg_color=COLORS["surface_alt"],
            corner_radius=12,
            padx=12,
            pady=7,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(side="right", padx=18, pady=18)

        folder_row = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
            border_width=1,
        )
        folder_row.pack(fill="x", padx=16, pady=(12, 5))
        self.folder_entry = ctk.CTkEntry(
            folder_row,
            placeholder_text="Selecciona una carpeta...",
            fg_color=COLORS["row"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            height=36,
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(10, 8), pady=9)
        self.choose_button = ctk.CTkButton(
            folder_row,
            text="Elegir carpeta",
            command=self.choose_folder,
            fg_color=COLORS["cyan_deep"],
            hover_color=COLORS["cyan"],
            text_color=COLORS["background"],
            height=36,
        )
        self.choose_button.pack(side="left", padx=(0, 10), pady=9)

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(4, 7))
        self.scan_button = ctk.CTkButton(
            action_row,
            text="Analizar todo",
            command=self.start_scan,
            fg_color=COLORS["lime"],
            hover_color=COLORS["lime_hover"],
            text_color=COLORS["background"],
            height=36,
        )
        self.scan_button.pack(side="left", padx=(0, 7))
        ctk.CTkButton(
            action_row,
            text="Duplicados",
            command=self.show_duplicates,
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["row_hover"],
            text_color=COLORS["amber"],
            height=36,
        ).pack(side="left", padx=7)
        self.issues_button = ctk.CTkButton(
            action_row,
            text="Ver incidencias",
            command=self.show_issues,
            state="disabled",
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["row_hover"],
            text_color=COLORS["coral"],
            height=36,
        )
        self.issues_button.pack(side="left", padx=7)
        ctk.CTkButton(
            action_row,
            text="Limpiar y organizar",
            command=self.organize_music,
            fg_color=COLORS["lime"],
            hover_color=COLORS["lime_hover"],
            text_color=COLORS["background"],
            height=36,
        ).pack(side="right", padx=(7, 0))

        filter_row = ctk.CTkFrame(self, fg_color=COLORS["surface_alt"])
        filter_row.pack(fill="x", padx=16, pady=(0, 10))
        self.filter_buttons = {}
        for filter_name, label in (
            ("all", "Toda la música"),
            ("duplicates", "Repetidas"),
            ("untagged", "Sin etiquetas"),
        ):
            button = ctk.CTkButton(
                filter_row,
                text=label,
                command=lambda name=filter_name: self.set_song_filter(name),
                height=30,
                fg_color="transparent",
                hover_color=COLORS["row_hover"],
                text_color=COLORS["text"],
            )
            button.pack(side="left", padx=3, pady=4)
            self.filter_buttons[filter_name] = button
        for label in ("Videos", "Imágenes", "Documentos"):
            ctk.CTkLabel(
                filter_row,
                text=label,
                text_color=COLORS["subtle"],
                fg_color="transparent",
                padx=9,
            ).pack(side="left")

        workspace = ctk.CTkFrame(
            self,
            fg_color=COLORS["background"],
            border_color=COLORS["border"],
            border_width=1,
        )
        workspace.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        workspace.grid_rowconfigure(0, weight=1)
        workspace.grid_columnconfigure(1, weight=1)

        sidebar = ctk.CTkFrame(
            workspace,
            width=190,
            corner_radius=0,
            fg_color=COLORS["surface"],
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        ctk.CTkLabel(
            sidebar,
            text="BIBLIOTECAS",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(16, 7))
        self.library_count = ctk.CTkButton(
            sidebar,
            text="♫  Toda la música       0",
            anchor="w",
            command=lambda: self.set_song_filter("all"),
            fg_color=COLORS["selection"],
            hover_color=COLORS["olive"],
            text_color=COLORS["lime"],
            height=34,
        )
        self.library_count.pack(fill="x", padx=8, pady=2)
        for label in ("Artistas", "Álbumes", "Géneros"):
            ctk.CTkLabel(
                sidebar,
                text=f"   {label}",
                text_color=COLORS["muted"],
                anchor="w",
                height=28,
            ).pack(fill="x", padx=8)

        ctk.CTkLabel(
            sidebar,
            text="PRÓXIMAMENTE",
            text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(18, 6))
        for label in ("Videos y películas", "Imágenes y diseños", "Documentos"):
            ctk.CTkLabel(
                sidebar,
                text=f"   {label}",
                text_color=COLORS["subtle"],
                anchor="w",
                height=27,
            ).pack(fill="x", padx=8)

        ctk.CTkLabel(
            sidebar,
            text="DIAGNÓSTICO",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(18, 6))
        ctk.CTkButton(
            sidebar,
            text="⚠  Repetidas",
            anchor="w",
            command=self.show_duplicates,
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["amber"],
            height=30,
        ).pack(fill="x", padx=8, pady=1)
        ctk.CTkButton(
            sidebar,
            text="!  Sin etiquetas ID3",
            anchor="w",
            command=lambda: self.set_song_filter("untagged"),
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["coral"],
            height=30,
        ).pack(fill="x", padx=8, pady=1)

        table_panel = ctk.CTkFrame(workspace, fg_color=COLORS["background"])
        table_panel.grid(row=0, column=1, sticky="nsew")
        table_panel.grid_rowconfigure(1, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)
        self.table_summary = ctk.CTkLabel(
            table_panel,
            text="Selecciona una carpeta y analiza la música.",
            text_color=COLORS["cyan"],
            anchor="w",
        )
        self.table_summary.grid(row=0, column=0, sticky="ew", padx=12, pady=10)

        table_frame = ctk.CTkFrame(
            table_panel,
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
            border_width=1,
        )
        table_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        table_style = ttk.Style(self)
        table_style.theme_use("clam")
        table_style.configure(
            "Treeview",
            background=COLORS["row"],
            fieldbackground=COLORS["row"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            rowheight=36,
            font=("Segoe UI", 9),
        )
        table_style.configure(
            "Treeview.Heading",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
            relief="flat",
            font=("Segoe UI", 8, "bold"),
        )
        table_style.map(
            "Treeview",
            background=[("selected", COLORS["selection"])],
            foreground=[("selected", COLORS["text"])],
        )
        columns = ("title", "artist", "album", "genre", "format", "duration", "state")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "title": "NOMBRE DE CANCIÓN",
            "artist": "ARTISTA",
            "album": "ÁLBUM",
            "genre": "GÉNERO",
            "format": "FORMATO",
            "duration": "DURACIÓN",
            "state": "ESTADO / ACCIÓN",
        }
        widths = {
            "title": 205,
            "artist": 145,
            "album": 145,
            "genre": 100,
            "format": 75,
            "duration": 80,
            "state": 145,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], minwidth=60, anchor="w")
        self.tree.tag_configure("duplicate", foreground=COLORS["amber"])
        self.tree.tag_configure("untagged", foreground=COLORS["coral"])
        self.tree.tag_configure("ready", foreground=COLORS["text"])
        scrollbar_y = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        scrollbar_x = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        footer = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0)
        footer.pack(fill="x")
        self.status = ctk.CTkLabel(
            footer,
            text="Listo para analizar música.",
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.status.pack(side="left", padx=14, pady=10)
        self.progress = ctk.CTkProgressBar(
            footer,
            progress_color=COLORS["lime"],
            fg_color=COLORS["track"],
            width=200,
        )
        self.progress.pack(side="right", padx=(8, 12), pady=13)
        self.progress.set(0)
        self.progress_percent = ctk.CTkLabel(
            footer,
            text="0%",
            width=42,
            text_color=COLORS["lime"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.progress_percent.pack(side="right", pady=10)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Selecciona una carpeta de música")

        if folder:
            self.folder = folder
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.status.configure(text="Carpeta seleccionada. Pulsa Analizar para comenzar.")

    def start_scan(self):
        if self._scan_running:
            return
        if not self.folder:
            messagebox.showwarning("Aviso", "Primero selecciona una carpeta.")
            return

        self._scan_running = True
        self._last_progress_percent = None
        self.choose_button.configure(state="disabled")
        self.scan_button.configure(state="disabled")
        self.progress.start()
        self.progress_percent.configure(text="—")
        self.status.configure(text="Buscando archivos de música...")
        self.set_issues([])
        self.songs = []
        self.duplicates = []
        self.possible_duplicates = []
        self.clear_table()

        thread = threading.Thread(target=self.scan, args=(self.folder,), daemon=True)
        thread.start()

    def scan(self, folder):
        try:
            result = scan_folder(folder, progress_callback=self.report_scan_progress)
            duplicates = find_duplicates(result.songs)
            possible_duplicates = find_possible_duplicates(result.songs)

            self.after(
                0,
                lambda: self.scan_finished(result, duplicates, possible_duplicates),
            )
        except Exception as error:
            self.after(0, lambda error=error: self.scan_error(error))

    def report_scan_progress(self, phase, completed, total):
        self.after(
            0,
            lambda: self.update_scan_progress(phase, completed, total),
        )

    def update_scan_progress(self, phase, completed, total):
        if phase == "listing":
            self.status.configure(text="Buscando archivos de música...")
            self.progress_percent.configure(text="—")
            return

        if self._last_progress_percent is None:
            self.progress.stop()
            self.progress.set(0)
            self._last_progress_percent = 0

        percent = 100 if total == 0 else min(100, int(completed * 100 / total))
        self.progress.set(percent / 100)
        self.progress_percent.configure(text=f"{percent}%")
        self.status.configure(text=f"Analizando música... {percent}%")
        self._last_progress_percent = percent

    def scan_finished(self, result, duplicates, possible_duplicates):
        self.progress.stop()
        self.progress.set(1)
        self.progress_percent.configure(text="100%")
        self._scan_running = False
        self.choose_button.configure(state="normal")
        self.scan_button.configure(state="normal")

        self.songs = result.songs
        self.duplicates = duplicates
        self.possible_duplicates = possible_duplicates
        self.set_issues(result.issues)
        self.render_songs()
        self.library_count.configure(text=f"♫  Toda la música       {len(self.songs):,}")

        self.status.configure(
            text=f"{len(self.songs):,} canciones analizadas  ·  "
            f"{len(duplicates)} grupos duplicados  ·  "
            f"{len(result.issues)} incidencias"
        )

    def set_song_filter(self, filter_name):
        self._active_filter = filter_name
        self.render_songs()
        for name, button in self.filter_buttons.items():
            button.configure(
                fg_color=COLORS["selection"] if name == filter_name else "transparent",
                text_color=COLORS["lime"] if name == filter_name else COLORS["muted"],
            )

    def render_songs(self):
        self.clear_table()
        duplicate_paths = {
            song.path
            for group in self.duplicates + self.possible_duplicates
            for song in group
        }
        if self._active_filter == "duplicates":
            songs = [song for song in self.songs if song.path in duplicate_paths]
        elif self._active_filter == "untagged":
            songs = [
                song for song in self.songs
                if any(
                    value.casefold() in {"desconocido", "unknown"}
                    for value in (song.title, song.artist, song.album, song.genre)
                )
            ]
        else:
            songs = self.songs

        for song in songs:
            untagged = any(
                value.casefold() in {"desconocido", "unknown"}
                for value in (song.title, song.artist, song.album, song.genre)
            )
            duplicate = song.path in duplicate_paths
            state = (
                "Duplicado"
                if duplicate
                else "Faltan etiquetas"
                if untagged
                else "Listo para organizar"
            )
            tag = "duplicate" if duplicate else "untagged" if untagged else "ready"
            self.tree.insert(
                "",
                "end",
                values=(
                    song.title,
                    song.artist,
                    song.album,
                    song.genre,
                    song.path.suffix.lstrip(".").upper(),
                    song.duration_text,
                    state,
                ),
                tags=(tag,),
            )

        if hasattr(self, "table_summary"):
            self.table_summary.configure(
                text=f"{len(songs):,} canciones mostradas  ·  "
                f"{len(self.songs):,} en total  ·  "
                f"{sum(len(group) for group in self.duplicates)} duplicados"
            )

    def scan_error(self, error):
        self.progress.stop()
        self.progress.set(0)
        self.progress_percent.configure(text="0%")
        self._scan_running = False
        self.choose_button.configure(state="normal")
        self.scan_button.configure(state="normal")
        messagebox.showerror("Error", str(error))
        self.status.configure(text="Ocurrió un error durante el análisis.")

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def set_issues(self, issues):
        self.issues = issues
        self.issues_button.configure(
            state="normal" if self.issues else "disabled"
        )

    def show_issues(self):
        if not self.issues:
            return

        window = ctk.CTkToplevel(self)
        window.title("Incidencias")
        window.geometry("850x450")
        self.set_window_icon(window)

        textbox = ctk.CTkTextbox(window)
        textbox.pack(fill="both", expand=True, padx=15, pady=15)
        details = "\n\n".join(
            f"{issue.path}\n{issue.message}" for issue in self.issues
        )
        textbox.insert("1.0", details)
        textbox.configure(state="disabled")

    def show_duplicates(self):
        if not self.songs:
            messagebox.showinfo("Información", "Primero analiza una carpeta.")
            return

        if not self.duplicates and not self.possible_duplicates:
            messagebox.showinfo("Repetidas", "No se encontraron archivos repetidos.")
            return

        window = ctk.CTkToplevel(self)
        window.title("Canciones repetidas")
        window.geometry("850x540")
        window.minsize(650, 420)
        window.transient(self)
        self.set_window_icon(window)

        duplicate_count = sum(len(group) for group in self.duplicates)
        possible_count = sum(len(group) for group in self.possible_duplicates)
        ctk.CTkLabel(
            window,
            text=f"COPIAS EXACTAS: {duplicate_count} | POSIBLES: {possible_count}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(18, 10))

        tree_frame = ctk.CTkFrame(window)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=8)
        duplicates_tree = ttk.Treeview(tree_frame, columns=("path",), show="tree headings")
        duplicates_tree.heading("#0", text="Archivo")
        duplicates_tree.heading("path", text="Ubicación")
        duplicates_tree.column("#0", width=240, anchor="w")
        duplicates_tree.column("path", width=500, anchor="w")
        duplicate_scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=duplicates_tree.yview
        )
        duplicates_tree.configure(yscrollcommand=duplicate_scrollbar.set)
        duplicates_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        duplicate_scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        exact_section = duplicates_tree.insert(
            "", "end", text="COPIAS EXACTAS (mismo contenido)", open=True
        )
        for number, group in enumerate(self.duplicates, start=1):
            group_item = duplicates_tree.insert(
                exact_section, "end", text=f"Grupo {number}: {group[0].title}", open=True
            )
            for index, song in enumerate(group):
                duplicates_tree.insert(
                    group_item,
                    "end",
                    text=("Conservar: " if index == 0 else "Copia adicional: ")
                    + song.filename,
                    values=(str(song.path),),
                )

        possible_section = duplicates_tree.insert(
            "", "end", text="POSIBLES REPETIDOS (mismos metadatos)", open=True
        )
        for number, group in enumerate(self.possible_duplicates, start=1):
            group_item = duplicates_tree.insert(
                possible_section,
                "end",
                text=f"Posible {number}: {group[0].title}",
                open=True,
            )
            for song in group:
                duplicates_tree.insert(
                    group_item, "end", text=song.filename, values=(str(song.path),)
                )

        ctk.CTkLabel(window, text="Acción para las copias adicionales:").pack(
            anchor="w", padx=20, pady=(6, 0)
        )
        action_menu = ctk.CTkOptionMenu(
            window,
            values=[
                "No hacer nada",
                "Mover a Duplicados",
                "Enviar a la Papelera",
            ],
        )
        action_menu.set("No hacer nada")
        action_menu.pack(anchor="w", padx=20, pady=(6, 10))

        buttons = ctk.CTkFrame(window, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkButton(
            buttons,
            text="Cerrar",
            fg_color="transparent",
            border_width=1,
            command=window.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            buttons,
            text="Vista previa de acción",
            command=lambda: self.confirm_duplicate_action(action_menu.get(), window),
        ).pack(side="right")

        window.grab_set()

    def confirm_duplicate_action(self, selected_action, window):
        action_by_label = {
            "Mover a Duplicados": "move",
            "Enviar a la Papelera": "trash",
        }
        action = action_by_label.get(selected_action)
        if action is None:
            window.destroy()
            return

        duplicates = [song for group in self.duplicates for song in group[1:]]
        preview_lines = []
        for group in self.duplicates:
            preview_lines.append(f"Se conserva: {group[0].path}")
            preview_lines.extend(
                f"Se procesa: {song.path}" for song in group[1:]
            )
        preview_paths = "\n".join(preview_lines[:12])
        if len(duplicates) > 8:
            preview_paths += f"\n... y {len(duplicates) - 8} copias adicionales más."
        destination_note = (
            "Se moverán a Musica_y_Audio\\Duplicados dentro de la carpeta elegida."
            if action == "move"
            else "Los archivos se enviarán a la Papelera de Windows y podrán restaurarse."
        )

        confirmed = messagebox.askyesno(
            "Confirmar acción sobre repetidos",
            f"Solo se procesarán copias exactas; se conservará una por grupo.\n"
            f"Se procesarán {len(duplicates)} archivos adicionales.\n\n"
            f"{destination_note}\n\n{preview_paths}\n\n¿Continuar?",
            parent=window,
        )
        if not confirmed:
            return

        window.destroy()
        result = process_duplicates(self.folder, self.duplicates, action)
        self.set_issues(result.issues)

        if result.issues:
            self.status.configure(
                text=f"Se procesaron {len(result.processed)} copias; "
                     f"{len(result.issues)} tuvieron errores."
            )
            messagebox.showwarning(
                "Acción parcial",
                f"Se procesaron {len(result.processed)} archivos y "
                f"{len(result.issues)} tuvieron errores. Consulta 'Ver incidencias'.",
            )
        else:
            messagebox.showinfo(
                "Acción completada",
                f"Se procesaron {len(result.processed)} copias adicionales.",
            )

        if result.processed:
            self.start_scan()

    def organize_music(self):
        if not self.songs:
            messagebox.showinfo("Información", "Primero analiza una carpeta.")
            return

        options = self.choose_organization_options()
        if options is None:
            return

        operations = preview_organization(self.folder, self.songs, **options)

        if not operations:
            messagebox.showinfo(
                "Organizar",
                "Las canciones ya están organizadas según sus metadatos."
            )
            return

        issues = validate_organization(self.folder, self.songs, **options)
        if issues:
            self.set_issues(issues)
            self.status.configure(
                text=f"Organización cancelada: {len(issues)} problemas de acceso."
            )
            messagebox.showwarning(
                "No se puede organizar",
                "Se detectaron problemas de acceso. No se movió ningún archivo. "
                "Consulta 'Ver incidencias'."
            )
            return

        if not self.confirm_organization(operations):
            return

        try:
            result = organize(self.folder, self.songs, **options)
            self.set_issues(result.issues)

            if result.issues:
                self.status.configure(
                    text=f"Se movieron {len(result.moved)} archivos; "
                         f"{len(result.issues)} no se pudieron mover."
                )
                messagebox.showwarning(
                    "Organización parcial",
                    f"Se movieron {len(result.moved)} archivos y "
                    f"{len(result.issues)} fallaron. Consulta 'Ver incidencias'."
                )
                self.show_issues()
            else:
                messagebox.showinfo(
                    "Completado",
                    f"Se organizaron {len(result.moved)} archivos."
                )

            if result.moved:
                self.start_scan()
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo organizar:\n{error}")

    def confirm_organization(self, operations):
        window = ctk.CTkToplevel(self)
        window.title("Vista previa de organización")
        window.geometry("760x560")
        window.minsize(600, 420)
        window.transient(self)
        self.set_window_icon(window)

        heading = ctk.CTkLabel(
            window,
            text=f"SE VAN A ORGANIZAR {len(operations)} CANCIONES",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        heading.pack(anchor="w", padx=20, pady=(18, 10))

        tree_frame = ctk.CTkFrame(window)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=8)

        preview_tree = ttk.Treeview(tree_frame, columns=("destination",), show="tree headings")
        preview_tree.heading("#0", text="Canción")
        preview_tree.heading("destination", text="Destino")
        preview_tree.column("#0", width=230, anchor="w")
        preview_tree.column("destination", width=430, anchor="w")
        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=preview_tree.yview
        )
        preview_tree.configure(yscrollcommand=scrollbar.set)
        preview_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        folders = {}
        for source, destination in operations:
            relative = destination.relative_to(self.folder)
            parent = ""
            accumulated = ()
            for folder_name in relative.parts[:-1]:
                accumulated += (folder_name,)
                if accumulated not in folders:
                    folders[accumulated] = preview_tree.insert(
                        parent, "end", text=folder_name, open=True
                    )
                parent = folders[accumulated]
            preview_tree.insert(
                parent,
                "end",
                text=source.name,
                values=(str(destination),),
            )

        duplicate_count = sum(max(0, len(group) - 1) for group in self.duplicates)
        summary = ctk.CTkLabel(
            window,
            text=f"Copias exactas encontradas: {duplicate_count}",
            anchor="w",
        )
        summary.pack(fill="x", padx=20, pady=(4, 10))

        result = {"confirmed": False}
        buttons = ctk.CTkFrame(window, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=(0, 18))

        cancel_button = ctk.CTkButton(
            buttons,
            text="Cancelar",
            fg_color="transparent",
            border_width=1,
            command=window.destroy,
        )
        cancel_button.pack(side="left")

        continue_button = ctk.CTkButton(
            buttons,
            text="Continuar",
            command=lambda: self._confirm_preview(window, result),
        )
        continue_button.pack(side="right")

        window.grab_set()
        self.wait_window(window)
        return result["confirmed"]

    def choose_organization_options(self):
        window = ctk.CTkToplevel(self)
        window.title("Formato de organización")
        window.geometry("420x300")
        window.resizable(False, False)
        window.transient(self)
        self.set_window_icon(window)

        ctk.CTkLabel(
            window,
            text="Organizar la música por",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=22, pady=(22, 12))

        artist_var = tk.BooleanVar(value=True)
        album_var = tk.BooleanVar(value=True)
        genre_var = tk.BooleanVar(value=False)

        ctk.CTkCheckBox(window, text="Artista", variable=artist_var).pack(
            anchor="w", padx=24, pady=7
        )
        ctk.CTkCheckBox(window, text="Álbum", variable=album_var).pack(
            anchor="w", padx=24, pady=7
        )
        ctk.CTkCheckBox(window, text="Género", variable=genre_var).pack(
            anchor="w", padx=24, pady=7
        )

        result = {"options": None}
        buttons = ctk.CTkFrame(window, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=(20, 16))
        ctk.CTkButton(
            buttons,
            text="Cancelar",
            fg_color="transparent",
            border_width=1,
            command=window.destroy,
        ).pack(side="left")

        def continue_to_preview():
            if not (artist_var.get() or album_var.get() or genre_var.get()):
                messagebox.showwarning(
                    "Formato incompleto",
                    "Selecciona al menos un criterio de organización.",
                    parent=window,
                )
                return

            result["options"] = {
                "organize_artist": artist_var.get(),
                "organize_album": album_var.get(),
                "organize_genre": genre_var.get(),
            }
            window.destroy()

        ctk.CTkButton(
            buttons, text="Vista previa", command=continue_to_preview
        ).pack(side="right")

        window.grab_set()
        self.wait_window(window)
        return result["options"]

    @staticmethod
    def _confirm_preview(window, result):
        result["confirmed"] = True
        window.destroy()
