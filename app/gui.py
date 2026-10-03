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
    "background": "#060807",
    "surface": "#111714",
    "surface_alt": "#0D100F",
    "row": "#0A0D0C",
    "row_hover": "#171E1B",
    "border": "#202A25",
    "text": "#E8ECE9",
    "muted": "#8B9690",
    "subtle": "#626D67",
    "lime": "#84CC16",
    "lime_hover": "#A3E635",
    "olive": "#365A27",
    "cyan": "#34D399",
    "cyan_light": "#6EE7B7",
    "cyan_deep": "#059669",
    "amber": "#FBBF24",
    "amber_dark": "#62420F",
    "coral": "#FB7185",
    "coral_dark": "#571F2C",
    "track": "#252D29",
    "selection": "#12382E",
}


def asset_path(filename):
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return bundle_root / "assets" / filename


class GestionadorArchivosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gestionador de archivos")
        self.geometry("1080x780")
        self.minsize(900, 640)
        self.configure(fg_color=COLORS["background"])

        self.folder = ""
        self.songs = []
        self.duplicates = []
        self.possible_duplicates = []
        self.issues = []
        self._scan_running = False
        self._last_progress_percent = None
        self._active_filter = "all"
        self._search_query = ""
        self._active_sort = "Artista"
        self.selected_song_paths = set()
        self._visible_songs = {}

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.set_application_icon()

        self.create_widgets()

    def set_application_icon(self):
        icon_path = asset_path("gestionador_archivos.ico")
        logo_path = asset_path("gestionador_archivos.png")

        if logo_path.is_file():
            self._application_icon = tk.PhotoImage(file=str(logo_path)).subsample(16, 16)
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
            window._application_icon = tk.PhotoImage(file=str(logo_path)).subsample(16, 16)
            window.iconphoto(True, window._application_icon)
        if icon_path.is_file():
            try:
                window.iconbitmap(default=str(icon_path))
            except tk.TclError:
                if not logo_path.is_file():
                    raise

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(
            self, fg_color=COLORS["surface"], corner_radius=10,
            border_width=1, border_color=COLORS["border"],
        )
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.pack(side="left", padx=8, pady=4)
        self._logo_image = tk.PhotoImage(
            file=str(asset_path("gestionador_archivos.png"))
        ).subsample(28, 28)
        tk.Label(
            header_left,
            image=self._logo_image,
            bg=COLORS["surface"],
            bd=0,
            highlightthickness=0,
        ).pack(side="left")
        brand = ctk.CTkFrame(header_left, fg_color="transparent")
        brand.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(
            brand,
            text="Gestionador de archivos",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Tus carpetas ordenadas en un clic. Olvídate de limpiar a mano",
            font=ctk.CTkFont(size=8),
            text_color=COLORS["cyan"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Música  ·  Versión 1.3.0",
            text_color=COLORS["cyan"],
            fg_color=COLORS["surface_alt"],
            corner_radius=12,
            padx=10,
            pady=4,
            font=ctk.CTkFont(size=9),
        ).pack(side="left", padx=(18, 6))
        self.active_directory = ctk.CTkLabel(
            header,
            text="▣  Directorio activo:  —",
            text_color=COLORS["muted"],
            fg_color=COLORS["surface_alt"],
            width=280,
            wraplength=260,
            corner_radius=14,
            padx=12,
            pady=6,
            font=ctk.CTkFont(size=10),
        )
        self.active_directory.pack(side="right", padx=12, pady=8)

        folder_row = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
            border_width=1,
        )
        folder_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 5))
        self.folder_entry = ctk.CTkEntry(
            folder_row,
            placeholder_text="▱  Selecciona una carpeta de música...",
            fg_color=COLORS["row"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            height=32,
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(8, 5), pady=6)
        self.choose_button = ctk.CTkButton(
            folder_row,
            text="▱  Elegir carpeta",
            command=self.choose_folder,
            fg_color=COLORS["cyan_deep"],
            hover_color="#047857",
            text_color=COLORS["text"],
            height=30,
        )
        self.choose_button.pack(side="left", padx=3, pady=5)

        action_row = folder_row
        self.scan_button = ctk.CTkButton(
            action_row,
            text="▣  Analizar todo",
            command=self.start_scan,
            fg_color=COLORS["lime"],
            hover_color=COLORS["lime_hover"],
            text_color=COLORS["background"],
            height=30,
        )
        self.scan_button.pack(side="left", padx=3, pady=5)
        self.duplicates_button = ctk.CTkButton(
            action_row,
            text="◉  Duplicados",
            command=self.show_duplicates,
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["row_hover"],
            text_color=COLORS["amber"],
            height=30,
        )
        self.duplicates_button.pack(side="left", padx=3, pady=5)
        self.issues_button = ctk.CTkButton(
            action_row,
            text="ⓘ  Ver incidencias",
            command=self.show_issues,
            state="disabled",
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["row_hover"],
            text_color=COLORS["coral"],
            height=30,
        )
        self.issues_button.pack(side="left", padx=3, pady=5)
        ctk.CTkButton(
            action_row,
            text="⚒  Limpiar y organizar",
            command=self.organize_music,
            fg_color=COLORS["lime"],
            hover_color=COLORS["lime_hover"],
            text_color=COLORS["background"],
            height=30,
        ).pack(side="left", padx=3, pady=5)

        filter_row = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=8)
        filter_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 6))
        self.filter_buttons = {}
        for filter_name, label in (
            ("all", "Todos"),
            ("music", "Música y Audio"),
            ("duplicates", "Duplicados"),
            ("untagged", "Sin etiquetas"),
        ):
            button = ctk.CTkButton(
                filter_row,
                text=label,
                command=lambda name=filter_name: self.set_song_filter(
                    "all" if name == "music" else name
                ),
                height=26,
                fg_color="transparent",
                hover_color=COLORS["row_hover"],
                text_color=COLORS["text"],
            )
            button.pack(side="left", padx=3, pady=4)
            self.filter_buttons[filter_name] = button
        for label in ("Videos", "Fotos", "Documentos", "Sin carátula", "Listas para renombrar"):
            ctk.CTkLabel(
                filter_row,
                text=label,
                text_color=COLORS["subtle"],
                fg_color="transparent",
                padx=7,
                font=ctk.CTkFont(size=10),
            ).pack(side="left")
        self.search_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="⌕  Filtrar por artista, álbum...",
            width=190,
            height=26,
            fg_color=COLORS["row"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.search_entry.pack(side="right", padx=8, pady=4)
        self.search_entry.bind("<KeyRelease>", self.update_search)

        workspace = ctk.CTkFrame(
            self,
            fg_color=COLORS["background"],
            border_color=COLORS["border"],
            border_width=1,
        )
        workspace.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 6))
        workspace.grid_rowconfigure(0, weight=1)
        workspace.grid_columnconfigure(1, weight=1)

        sidebar = ctk.CTkFrame(
            workspace,
            width=166,
            corner_radius=0,
            fg_color=COLORS["surface"],
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        ctk.CTkLabel(
            sidebar,
            text="CATEGORÍAS",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(16, 7))
        self.library_count = ctk.CTkButton(
            sidebar,
            text="▣  Todos los archivos       0",
            anchor="w",
            command=lambda: self.set_song_filter("all"),
            fg_color=COLORS["selection"],
            hover_color=COLORS["olive"],
            text_color=COLORS["lime"],
            height=34,
        )
        self.library_count.pack(fill="x", padx=7, pady=2)
        for label in ("♫  Música y Audio", "▸  Videos y Películas", "▧  Fotos e Imágenes", "▤  Documentos", "◉  Sin destinatario"):
            ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                command=lambda: None,
                fg_color="transparent",
                hover_color=COLORS["row_hover"],
                text_color=COLORS["muted"],
                height=29,
            ).pack(fill="x", padx=7, pady=1)
        ctk.CTkFrame(
            sidebar, height=1, fg_color=COLORS["border"]
        ).pack(fill="x", padx=10, pady=(9, 5))

        ctk.CTkLabel(
            sidebar,
            text="DIAGNÓSTICO Y SALUD",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(5, 5))
        ctk.CTkButton(
            sidebar,
            text="⚠  Duplicados",
            anchor="w",
            command=self.show_duplicates,
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["amber"],
            height=30,
        ).pack(fill="x", padx=7, pady=1)
        ctk.CTkButton(
            sidebar,
            text="!  Sin metadatos / tags",
            anchor="w",
            command=lambda: self.set_song_filter("untagged"),
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["coral"],
            height=30,
        ).pack(fill="x", padx=7, pady=1)
        ctk.CTkButton(
            sidebar,
            text="ⓘ  Sin app asociada",
            anchor="w",
            command=lambda: None,
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["muted"],
            height=30,
        ).pack(fill="x", padx=7, pady=1)
        ctk.CTkButton(
            sidebar,
            text="⌁  Temporales / Basura",
            anchor="w",
            command=lambda: self.set_song_filter("flac"),
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["muted"],
            height=30,
        ).pack(fill="x", padx=7, pady=1)
        rule_card = ctk.CTkFrame(
            sidebar,
            fg_color=COLORS["surface_alt"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=7,
        )
        rule_card.pack(side="bottom", fill="x", padx=8, pady=8)
        ctk.CTkLabel(
            rule_card,
            text="Regla de orden",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=9),
        ).pack(anchor="w", padx=8, pady=(5, 1))
        ctk.CTkLabel(
            rule_card,
            text="{Artista}/{Álbum}/...",
            text_color=COLORS["cyan"],
            font=ctk.CTkFont(size=9),
        ).pack(anchor="w", padx=8, pady=(0, 5))

        table_panel = ctk.CTkFrame(workspace, fg_color=COLORS["background"])
        table_panel.grid(row=0, column=1, sticky="nsew")
        table_panel.grid_rowconfigure(1, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)
        table_header = ctk.CTkFrame(table_panel, fg_color="transparent")
        table_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 3))
        self.select_all_button = ctk.CTkButton(
            table_header,
            text="☑  Seleccionar todos",
            command=self.toggle_select_all_visible,
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["cyan"],
            width=145,
            height=28,
        )
        self.select_all_button.pack(side="left", padx=(0, 4))
        self.table_summary = ctk.CTkLabel(
            table_header,
            text="0 mostrados  |  0 archivos listos para organizar",
            text_color=COLORS["cyan"],
            anchor="w",
        )
        self.table_summary.pack(side="left", fill="x", expand=True)
        table_tools = ctk.CTkFrame(table_panel, fg_color="transparent")
        table_tools.grid(row=0, column=1, sticky="e", padx=(0, 10), pady=(8, 5))
        ctk.CTkLabel(table_tools, text="☷ Ordenar:", text_color=COLORS["muted"]).pack(
            side="left", padx=4
        )
        self.sort_menu = ctk.CTkOptionMenu(
            table_tools,
            values=["Artista", "Canción", "Álbum"],
            command=self.set_song_sort,
            width=100,
            height=26,
            fg_color=COLORS["surface"],
            button_color=COLORS["surface_alt"],
            button_hover_color=COLORS["row_hover"],
            text_color=COLORS["muted"],
        )
        self.sort_menu.set("Artista")
        self.sort_menu.pack(side="left")

        table_frame = ctk.CTkFrame(
            table_panel,
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
            border_width=1,
        )
        table_frame.grid(
            row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0, 8)
        )
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
            rowheight=37,
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
        table_style.configure(
            "Vertical.TScrollbar",
            background=COLORS["surface_alt"],
            troughcolor=COLORS["background"],
            bordercolor=COLORS["border"],
            arrowcolor=COLORS["muted"],
            lightcolor=COLORS["surface_alt"],
            darkcolor=COLORS["surface_alt"],
            relief="flat",
        )
        table_style.configure(
            "Horizontal.TScrollbar",
            background=COLORS["surface_alt"],
            troughcolor=COLORS["background"],
            bordercolor=COLORS["border"],
            arrowcolor=COLORS["muted"],
            lightcolor=COLORS["surface_alt"],
            darkcolor=COLORS["surface_alt"],
            relief="flat",
        )
        columns = (
            "selected", "title", "artist", "album", "genre", "format", "duration", "state"
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "selected": "✓",
            "title": "CANCIÓN",
            "artist": "ARTISTA",
            "album": "ÁLBUM",
            "genre": "GÉNERO",
            "format": "FORMATO",
            "duration": "DURACIÓN",
            "state": "ESTADO / DIAGNÓSTICO",
        }
        widths = {
            "selected": 30,
            "title": 180,
            "artist": 125,
            "album": 130,
            "genre": 85,
            "format": 65,
            "duration": 65,
            "state": 125,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                minwidth=28 if column == "selected" else 60,
                anchor="center" if column == "selected" else "w",
            )
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
        self.tree.bind("<Button-1>", self.handle_song_click, add=True)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        footer = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        footer.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.status = ctk.CTkLabel(
            footer,
            text="◉  0 analizados  ·  0 repetidas  ·  0 incidencias",
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.status.pack(side="left", padx=14, pady=10)
        self.log_button = ctk.CTkButton(
            footer,
            text="▤  Registro",
            command=self.show_issues,
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["muted"],
            width=90,
            height=26,
        )
        self.log_button.pack(side="right", padx=(2, 8), pady=6)
        self.rules_button = ctk.CTkButton(
            footer,
            text="☷  Reglas",
            command=self.open_organization_rules,
            fg_color="transparent",
            hover_color=COLORS["row_hover"],
            text_color=COLORS["muted"],
            width=75,
            height=26,
        )
        self.rules_button.pack(side="right", padx=2, pady=6)
        self.progress = ctk.CTkProgressBar(
            footer,
            progress_color=COLORS["lime"],
            fg_color=COLORS["track"],
            width=200,
        )
        self.progress_percent = ctk.CTkLabel(
            footer,
            text="0%",
            width=42,
            text_color=COLORS["lime"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.progress_percent.pack(side="right", pady=10)
        self.progress.pack(side="right", padx=(8, 12), pady=13)
        self.progress.set(0)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Selecciona una carpeta de música")

        if folder:
            self.folder = folder
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            display_folder = folder if len(folder) <= 48 else f"...{folder[-45:]}"
            self.active_directory.configure(
                text=f"▣  Directorio activo:  {display_folder}"
            )
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
        self.selected_song_paths = {song.path for song in self.songs}
        self.duplicates = duplicates
        self.possible_duplicates = possible_duplicates
        self.set_issues(result.issues)
        self.render_songs()
        exact_duplicate_count = sum(len(group) for group in duplicates)
        self.library_count.configure(text=f"▣  Todos los archivos       {len(self.songs):,}")
        self.duplicates_button.configure(
            text=f"◉  Ver repetidas  {exact_duplicate_count}"
        )
        self.filter_buttons["all"].configure(text=f"Todos ({len(self.songs):,})")
        self.filter_buttons["duplicates"].configure(
            text=f"●  Repetidas ({exact_duplicate_count})"
        )
        untagged_count = sum(
            any(
                value.casefold() in {"desconocido", "unknown"}
                for value in (song.title, song.artist, song.album, song.genre)
            )
            for song in self.songs
        )
        self.filter_buttons["untagged"].configure(
            text=f"●  Sin etiquetas ID3 ({untagged_count})"
        )

        self.status.configure(
            text=f"◉  {len(self.songs):,} analizados  ·  "
            f"{exact_duplicate_count} repetidas  ·  "
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

    def update_search(self, _event=None):
        self._search_query = self.search_entry.get().strip().casefold()
        self.render_songs()

    def set_song_sort(self, sort_name):
        self._active_sort = sort_name
        self.render_songs()

    def render_songs(self):
        self.clear_table()
        self._visible_songs = {}
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
        elif self._active_filter == "flac":
            songs = [song for song in self.songs if song.path.suffix.casefold() == ".flac"]
        else:
            songs = self.songs

        query = self._search_query
        if query:
            songs = [
                song for song in songs
                if query in " ".join((song.title, song.artist, song.album)).casefold()
            ]
        sort_key = {
            "Canción": lambda song: song.title.casefold(),
            "Álbum": lambda song: song.album.casefold(),
        }.get(self._active_sort, lambda song: song.artist.casefold())
        songs = sorted(songs, key=sort_key)

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
                iid=str(song.path),
                values=(
                    "☑" if song.path in self.selected_song_paths else "☐",
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
            self._visible_songs[str(song.path)] = song

        visible_paths = {song.path for song in songs}
        all_visible_selected = bool(songs) and visible_paths.issubset(
            self.selected_song_paths
        )
        self.select_all_button.configure(
            text="☑  Seleccionar todos" if all_visible_selected
            else "☐  Seleccionar todos"
        )

        if hasattr(self, "table_summary"):
            self.table_summary.configure(
                text=f"{len(songs):,} mostrados  |  "
                f"{len(visible_paths & self.selected_song_paths):,} archivos listos para organizar"
            )
        if hasattr(self, "library_count"):
            self.library_count.configure(text=f"♫  Toda la música       {len(self.songs):,}")

    def toggle_select_all_visible(self):
        visible_paths = {song.path for song in self._visible_songs.values()}
        if visible_paths.issubset(self.selected_song_paths):
            self.selected_song_paths.difference_update(visible_paths)
        else:
            self.selected_song_paths.update(visible_paths)
        self.render_songs()

    def handle_song_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":
            return

        item = self.tree.identify_row(event.y)
        song = self._visible_songs.get(item)
        if song is None:
            return
        if song.path in self.selected_song_paths:
            self.selected_song_paths.remove(song.path)
        else:
            self.selected_song_paths.add(song.path)
        self.render_songs()
        return "break"

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

    def open_organization_rules(self):
        if not self.songs:
            messagebox.showinfo("Reglas", "Analiza una carpeta para configurar sus reglas.")
            return
        self.choose_organization_options()

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
        selected_songs = [
            song for song in self.songs if song.path in self.selected_song_paths
        ]
        if not selected_songs:
            messagebox.showinfo("Información", "Primero analiza una carpeta.")
            return

        options = self.choose_organization_options()
        if options is None:
            return

        operations = preview_organization(self.folder, selected_songs, **options)

        if not operations:
            messagebox.showinfo(
                "Organizar",
                "Las canciones ya están organizadas según sus metadatos."
            )
            return

        issues = validate_organization(self.folder, selected_songs, **options)
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
            result = organize(self.folder, selected_songs, **options)
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
