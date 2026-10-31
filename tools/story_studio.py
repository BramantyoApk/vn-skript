#!/usr/bin/env python3
"""
Story Studio - Visual Novel Dialogue & Character Creator for Paper 26.2
Built with Tkinter (Native Python).
Allows creating characters with auto-scaling portraits (64x64, 128x128, 256x256),
authoring dialogue lines with emotion switching, and 1-click compile & sync.
"""

import os
import sys
import shutil
import copy

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

try:
    import sv_ttk
except ImportError:
    sv_ttk = None

try:
    import pywinstyles
except ImportError:
    pywinstyles = None

# Import internal compiler & processor
from compiler import (
    load_characters, load_dialogues, compile_all, sync_client_pack,
    resolve_asset_path, load_hud_config, save_hud_config,
    load_studio_config, save_studio_config, get_font_textures_dir,
    get_client_pack_dir, get_server_dir,
    CHARACTERS_DIR, DIALOGUES_DIR, STANDARD_EMOTIONS, BASE_DIR
)
from image_processor import process_portrait, TARGET_WIDTH, TARGET_HEIGHT

DIALOG_BOX_TEXTURE = os.path.abspath(os.path.join(BASE_DIR, "resourcepack/assets/minecraft/textures/font/dialogue_box.png"))
NAMEPLATE_TEXTURE = os.path.abspath(os.path.join(BASE_DIR, "resourcepack/assets/minecraft/textures/font/nameplate.png"))

# Minecraft raw ASCII character pixel widths (unpadded 8x8 font grid)
# Source: BetterHUD TextScale & TextRenderer
RAW_ASCII_WIDTHS = {
    ' ': 3, '!': 1, '"': 3, '#': 5, '$': 5, '%': 5, '&': 5, "'": 1,
    '(': 3, ')': 3, '*': 3, '+': 5, ',': 1, '-': 5, '.': 1, '/': 5,
    '0': 5, '1': 5, '2': 5, '3': 5, '4': 5, '5': 5, '6': 5, '7': 5,
    '8': 5, '9': 5, ':': 1, ';': 1, '<': 4, '=': 5, '>': 4, '?': 5,
    '@': 6, 'A': 5, 'B': 5, 'C': 5, 'D': 5, 'E': 5, 'F': 5, 'G': 5,
    'H': 5, 'I': 3, 'J': 5, 'K': 5, 'L': 5, 'M': 5, 'N': 5, 'O': 5,
    'P': 5, 'Q': 5, 'R': 5, 'S': 5, 'T': 5, 'U': 5, 'V': 5, 'W': 5,
    'X': 5, 'Y': 5, 'Z': 5, '[': 3, '\\': 5, ']': 3, '^': 5, '_': 5,
    '`': 2, 'a': 5, 'b': 5, 'c': 5, 'd': 5, 'e': 5, 'f': 4, 'g': 5,
    'h': 5, 'i': 1, 'j': 5, 'k': 4, 'l': 2, 'm': 5, 'n': 5, 'o': 5,
    'p': 5, 'q': 5, 'r': 5, 's': 5, 't': 3, 'u': 5, 'v': 5, 'w': 5,
    'x': 5, 'y': 5, 'z': 5, '{': 3, '|': 1, '}': 3, '~': 6
}

def get_betterhud_char_width(c, scale=0.46):
    """
    Bytecode-accurate BetterHUD character advance calculation:
    Space character (code 32) is constant width 4.
    Other characters: round((raw_width / 8.0) * round(8.0 * scale)) + 1.
    """
    cp = ord(c)
    if cp == 32:
        return 4
    w = RAW_ASCII_WIDTHS.get(c, 5)
    norm_h = round(8.0 * scale)
    norm_w = round((w / 8.0) * norm_h)
    return norm_w + 1

def split_dialogue_lines(text, split_width, scale=0.46, force_split=False):
    """
    Simulates BetterHUD AdventuresKt.split$parse algorithm bytecode:
    Accumulates character advances using BetterHUD scaled widths.
    When current width >= split_width, breaks at space, forced overflow (>= 1.25 * split_width),
    or forceSplit flag.
    Returns list of (line_text, unscaled_pixel_width).
    """
    if not text:
        return [("", 0)]

    max_w = round(split_width * 1.25)
    lines = []
    cur_str = []
    cur_w = 0

    for c in text:
        cp = ord(c)
        if cp == 10:  # newline '\n'
            line_text = "".join(cur_str).strip()
            lines.append((line_text, cur_w))
            cur_str = []
            cur_w = 0
            continue

        adv = get_betterhud_char_width(c, scale)
        cur_w += adv
        cur_str.append(c)

        if cur_w >= split_width:
            if cur_w >= max_w or cp == 32 or force_split:
                line_text = "".join(cur_str).strip()
                if line_text:
                    lines.append((line_text, cur_w))
                cur_str = []
                cur_w = 0

    if cur_str:
        line_text = "".join(cur_str).strip()
        if line_text:
            lines.append((line_text, cur_w))

    return lines if lines else [("", 0)]

def load_bundled_fonts():
    """Loads bundled Minecraft fonts on Windows via GDI AddFontResourceExW for process-local Tkinter use."""
    try:
        import ctypes
        fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
        if os.path.exists(fonts_dir):
            for fname in os.listdir(fonts_dir):
                if fname.lower().endswith((".ttf", ".otf")):
                    fpath = os.path.abspath(os.path.join(fonts_dir, fname))
                    # FR_PRIVATE = 0x10 makes font accessible to this process
                    ctypes.windll.gdi32.AddFontResourceExW(fpath, 0x10, 0)
    except Exception:
        pass

load_bundled_fonts()

class StoryStudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Story Studio - M-SMP Visual Novel Engine")
        self.geometry("1000x720")
        self.minsize(900, 640)

        # Retain references to PhotoImage so Garbage Collector doesn't delete them
        self._image_cache = {}
        self._hud_image_refs = {}
        self._texture_ram_cache = {}  # In-memory RAM cache for scaled PIL/PhotoImage (Fast 0ms I/O)
        self._resize_timer = None     # Debounce timer for canvas resize
        self._redraw_timer = None     # Debounce timer for HUD canvas redraw
        self._gallery_rendered = False  # Track if asset gallery already generated

        # Modern 2026 Dark Slate Theme (Strict Anti-AI Slop, Flat Solid Tokens, High Performance)
        self._setup_modern_theme()

        # Visual HUD Undo/Redo stacks & flags
        self._hud_undo_stack = []
        self._hud_redo_stack = []
        self._is_undoing_or_redoing = False
        self._group_scale_snapshot = None
        self._group_scaling_in_progress = False

        self.bind_all("<Control-z>", self._on_shortcut_undo)
        self.bind_all("<Control-Z>", self._on_shortcut_undo)
        self.bind_all("<Control-Shift-Z>", self._on_shortcut_redo)
        self.bind_all("<Control-Shift-z>", self._on_shortcut_redo)
        self.bind_all("<Control-y>", self._on_shortcut_redo)
        self.bind_all("<Control-Y>", self._on_shortcut_redo)

        self._init_data()
        self._build_ui()

    def _setup_modern_theme(self):
        # 1. Apply Sun Valley Dark Theme if available
        if sv_ttk is not None:
            try:
                sv_ttk.set_theme("dark")
            except Exception:
                pass

        # 2. Apply Windows Native Dark Titlebar (DWM Dark Mode)
        if pywinstyles is not None:
            try:
                pywinstyles.apply_style(self, "dark")
            except Exception:
                pass

        # Strict Consistent Dark Tokens (Pure Dark Modern Windows 11 / Charcoal Slate)
        COLOR_BG = "#181818"          # Base canvas & container background
        COLOR_SURFACE = "#202020"     # Card & LabelFrame surface
        COLOR_CARD = "#282828"        # Inner cards & highlights
        COLOR_BORDER = "#383838"      # Subtle border outline
        COLOR_TEXT = "#f3f3f3"        # Primary readable text
        COLOR_MUTED = "#a0a0a0"       # Secondary muted captions
        COLOR_ACCENT = "#007acc"      # Calm professional blue accent
        COLOR_ACCENT_HOVER = "#0062a3"
        COLOR_BTN = "#2b2b2b"
        COLOR_BTN_HOVER = "#363636"

        self.configure(bg=COLOR_BG)
        self.style = ttk.Style(self)

        # In case sv-ttk not present, fallback cleanly
        if sv_ttk is None:
            try:
                self.style.theme_use("clam")
            except Exception:
                pass
            self.style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 9))
            self.style.configure("TFrame", background=COLOR_BG)
            self.style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT)
            self.style.configure("TButton", background=COLOR_BTN, foreground=COLOR_TEXT, bordercolor=COLOR_BORDER, relief="solid", borderwidth=1, padding=(6, 3))
            self.style.configure("TEntry", fieldbackground="#10121a", foreground=COLOR_TEXT, bordercolor=COLOR_BORDER)
            self.style.configure("TCombobox", fieldbackground="#10121a", foreground=COLOR_TEXT)
            self.style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
            self.style.configure("TNotebook.Tab", background="#181b28", foreground=COLOR_MUTED, padding=(14, 6))

        # Modern custom component adjustments
        self.style.configure("Surface.TFrame", background=COLOR_SURFACE)
        self.style.configure("Card.TFrame", background=COLOR_CARD)
        self.style.configure("TLabelframe", bordercolor=COLOR_BORDER, relief="solid")
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"), foreground="#60cdff")

        self.style.configure("Surface.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT)
        self.style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT)
        self.style.configure("Muted.TLabel", foreground=COLOR_MUTED, font=("Segoe UI", 8))
        self.style.configure("SurfaceMuted.TLabel", foreground=COLOR_MUTED, font=("Segoe UI", 8))
        self.style.configure("Badge.TLabel", background="#1a3b5c", foreground="#60cdff", font=("Segoe UI", 8, "bold"), padding=(5, 2))

        self.style.configure("Primary.TButton", font=("Segoe UI", 9, "bold"))
        self.style.configure("Success.TButton", font=("Segoe UI", 9, "bold"))

        # Lock mousewheel scrolling on all enum / combobox / spinbox widgets globally
        def _disable_mousewheel(e):
            return "break"

        for cls in ("TCombobox", "Combobox", "TSpinbox", "Spinbox"):
            self.bind_class(cls, "<MouseWheel>", _disable_mousewheel)
            self.bind_class(cls, "<Button-4>", _disable_mousewheel)
            self.bind_class(cls, "<Button-5>", _disable_mousewheel)

    def _init_data(self):
        self.studio_cfg = load_studio_config()
        self.characters = load_characters()
        self.dialogues = load_dialogues()
        self.selected_char_id = tk.StringVar(value="")
        self.char_portrait_paths = {em: "" for em in STANDARD_EMOTIONS}
        self._preview_dialog_text = ""
        self._hud_handles = {}

    def _build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Tab 1: Character Editor
        self.tab_char = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_char, text=" Karakter & FancyNpc ")
        self._build_character_tab()

        # Tab 2: Dialogue Flow
        self.tab_dlg = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dlg, text=" Penulis Dialog ")
        self._build_dialogue_tab()

        # Tab 3: Visual HUD Designer
        self.tab_hud = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_hud, text=" Visual HUD Designer ")
        self._build_hud_tab()

        # Tab 4: Assets & Settings
        self.tab_assets = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_assets, text=" Aset & Direktori ")
        self._build_assets_tab()

        # Tab 5: Compile & Sync
        self.tab_sync = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_sync, text=" 1-Click Sync ")
        self._build_sync_tab()

        # Listen to tab change for lazy refresh
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event=None):
        try:
            sel_tab = self.notebook.select()
            if sel_tab == str(self.tab_hud):
                self._redraw_hud_canvas_debounced(delay_ms=10)
            elif sel_tab == str(self.tab_assets):
                if not getattr(self, "_gallery_rendered", False):
                    self._refresh_assets_gallery()
        except Exception:
            pass

    # =========================================================================
    # TAB 1: CHARACTER & PORTRAIT EDITOR
    # =========================================================================
    def _build_character_tab(self):
        left_frame = ttk.LabelFrame(self.tab_char, text="Daftar Karakter", width=220)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        left_frame.pack_propagate(False)

        self.char_listbox = tk.Listbox(
            left_frame,
            font=("Segoe UI", 10),
            bg="#202020",
            fg="#f3f3f3",
            selectbackground="#007acc",
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightbackground="#383838",
            activestyle="none",
            relief="flat"
        )
        self.char_listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.char_listbox.bind("<<ListboxSelect>>", self._on_select_character)

        btn_row = ttk.Frame(left_frame)
        btn_row.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(btn_row, text="+ Baru", command=self._on_new_character).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_row, text="Hapus", command=self._on_delete_character).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        right_frame = ttk.LabelFrame(self.tab_char, text="Profil Karakter & Slot Potret (Auto-Scale 64/128/256)")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        meta_frame = ttk.Frame(right_frame)
        meta_frame.pack(fill=tk.X, padx=8, pady=6)
        meta_frame.columnconfigure(1, weight=1)
        meta_frame.columnconfigure(3, weight=1)

        ttk.Label(meta_frame, text="ID Karakter (unik):").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 4))
        self.entry_char_id = ttk.Entry(meta_frame)
        self.entry_char_id.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=4)

        ttk.Label(meta_frame, text="Nama Tampilan:").grid(row=0, column=2, sticky="w", pady=4, padx=(0, 4))
        self.entry_char_speaker = ttk.Entry(meta_frame)
        self.entry_char_speaker.grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(meta_frame, text="Nama FancyNpc:").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 4))
        self.entry_char_npc = ttk.Entry(meta_frame)
        self.entry_char_npc.grid(row=1, column=1, sticky="ew", padx=(0, 16), pady=4)

        ttk.Label(meta_frame, text="Skin FancyNpc:").grid(row=1, column=2, sticky="w", pady=4, padx=(0, 4))
        self.entry_char_skin = ttk.Entry(meta_frame)
        self.entry_char_skin.grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(meta_frame, text="Custom Sound:").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 4))
        self.entry_char_sound = ttk.Entry(meta_frame)
        self.entry_char_sound.grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)
        ttk.Label(meta_frame, text="(Opsional: contoh 'minecraft:entity.villager.ambient'. Kosongkan jika tanpa suara)", style="Muted.TLabel").grid(row=3, column=1, columnspan=3, sticky="w", pady=(0, 4))

        # Emotion slots (Dynamic slot management + custom emotions)
        portraits_frame = ttk.LabelFrame(right_frame, text="Slot Potret Emosi (Bebas Tambah Emosi & Resolusi)")
        portraits_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        ctrl_row = ttk.Frame(portraits_frame)
        ctrl_row.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(ctrl_row, text="Tambah Emosi Kustom:").pack(side=tk.LEFT, padx=4)
        self.entry_new_emotion = ttk.Entry(ctrl_row, width=15)
        self.entry_new_emotion.pack(side=tk.LEFT, padx=4)
        self.entry_new_emotion.bind("<Return>", lambda event: self._on_add_custom_emotion())
        ttk.Button(ctrl_row, text="+ Tambah Slot", command=self._on_add_custom_emotion).pack(side=tk.LEFT, padx=4)

        # Scrollable container for portrait slots
        self.port_canvas_wrap = tk.Canvas(portraits_frame, bg="#202020", highlightthickness=0, height=180)
        self.port_scrollbar = ttk.Scrollbar(portraits_frame, orient=tk.HORIZONTAL, command=self.port_canvas_wrap.xview)
        self.portraits_container = ttk.Frame(self.port_canvas_wrap)
        self.portraits_container.bind("<Configure>", lambda e: self.port_canvas_wrap.configure(scrollregion=self.port_canvas_wrap.bbox("all")))
        self.port_canvas_wrap.create_window((0, 0), window=self.portraits_container, anchor="nw")
        self.port_canvas_wrap.configure(xscrollcommand=self.port_scrollbar.set)
        self.port_canvas_wrap.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self.port_scrollbar.pack(fill=tk.X, padx=4, pady=2)

        self.portrait_previews = {}
        self.portrait_labels = {}
        self._render_portrait_slots()

        bottom_row = ttk.Frame(right_frame)
        bottom_row.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(bottom_row, text="📋 Salin Command FancyNpcs", command=self._on_copy_fancynpcs_cmd).pack(side=tk.LEFT, padx=4)
        ttk.Button(bottom_row, text=" Simpan Data Karakter", command=self._on_save_character).pack(side=tk.RIGHT)

        self._refresh_character_list()
        # Default auto select first character if available
        if self.characters:
            first_char = sorted(self.characters.keys())[0]
            self.char_listbox.selection_set(0)
            self._load_character_to_form(first_char)

    def _render_portrait_slots(self):
        all_emotions = []
        for em in STANDARD_EMOTIONS:
            if em not in all_emotions:
                all_emotions.append(em)
        for em in self.char_portrait_paths.keys():
            if em and em not in all_emotions:
                all_emotions.append(em)

        # Check if we can reuse existing slot widgets without destroying them
        current_slots = getattr(self, "_active_portrait_slots", {})
        if set(current_slots.keys()) == set(all_emotions):
            # Fast in-place update (0ms widget creation overhead)
            for em in all_emotions:
                path = self.char_portrait_paths.get(em, "")
                self._update_portrait_preview(em, path)
            return

        # Full rebuild only when emotion list actually changes
        for widget in self.portraits_container.winfo_children():
            widget.destroy()

        self.portrait_previews = {}
        self.portrait_labels = {}
        self._active_portrait_slots = {}

        for i, em in enumerate(all_emotions):
            slot = ttk.Frame(self.portraits_container, relief=tk.RIDGE, padding=4)
            slot.grid(row=0, column=i, padx=6, pady=4, sticky="nw")
            self._active_portrait_slots[em] = slot

            header_frame = ttk.Frame(slot)
            header_frame.pack(fill=tk.X)
            ttk.Label(header_frame, text=em.upper(), font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

            if em not in STANDARD_EMOTIONS:
                del_btn = ttk.Button(header_frame, text="×", width=2, command=lambda e=em: self._on_delete_custom_emotion(e))
                del_btn.pack(side=tk.RIGHT)

            canv = tk.Canvas(slot, width=96, height=108, bg="#202020", highlightthickness=1, highlightbackground="#3d3d3d")
            canv.pack(pady=4)
            self.portrait_previews[em] = canv

            lbl_info = ttk.Label(slot, text="Kosong", font=("Segoe UI", 8), foreground="#888888")
            lbl_info.pack()
            self.portrait_labels[em] = lbl_info

            ttk.Button(slot, text="Pilih PNG", command=lambda e=em: self._on_browse_portrait(e)).pack(pady=2)

            path = self.char_portrait_paths.get(em, "")
            self._update_portrait_preview(em, path)

    def _on_add_custom_emotion(self):
        em = self.entry_new_emotion.get().strip().lower()
        if not em:
            return
        if em in self.char_portrait_paths:
            messagebox.showinfo("Info", f"Slot emosi '{em}' sudah ada.")
            return
        self.char_portrait_paths[em] = ""
        self.entry_new_emotion.delete(0, tk.END)
        self._render_portrait_slots()

    def _on_delete_custom_emotion(self, em):
        if em in self.char_portrait_paths:
            del self.char_portrait_paths[em]
            self._render_portrait_slots()

    def _refresh_character_list(self):
        self.char_listbox.delete(0, tk.END)
        for cid in sorted(self.characters.keys()):
            self.char_listbox.insert(tk.END, cid)
        if hasattr(self, 'combo_sample_char'):
            self._refresh_sample_chars()

    def _load_character_to_form(self, cid):
        cdata = self.characters.get(cid, {})

        self.entry_char_id.delete(0, tk.END)
        self.entry_char_id.insert(0, cid)

        self.entry_char_speaker.delete(0, tk.END)
        self.entry_char_speaker.insert(0, cdata.get("speaker_name", cid.capitalize()))

        self.entry_char_npc.delete(0, tk.END)
        self.entry_char_npc.insert(0, cdata.get("fancynpc_name", cid.capitalize()))

        self.entry_char_skin.delete(0, tk.END)
        self.entry_char_skin.insert(0, cdata.get("fancynpc_skin", cdata.get("fancynpc_name", cid.capitalize())))

        self.entry_char_sound.delete(0, tk.END)
        sound_val = cdata.get("voice", {}).get("sound", "")
        if sound_val and sound_val != "minecraft:entity.villager.ambient":
            self.entry_char_sound.insert(0, sound_val)
        elif sound_val == "minecraft:entity.villager.ambient":
            self.entry_char_sound.insert(0, sound_val)

        portraits = cdata.get("portraits", {})
        self.char_portrait_paths = {em: "" for em in STANDARD_EMOTIONS}
        for em, p in portraits.items():
            self.char_portrait_paths[em] = p or ""
        self._render_portrait_slots()

    def _on_select_character(self, event):
        sel = self.char_listbox.curselection()
        if not sel:
            return
        cid = self.char_listbox.get(sel[0])
        self._load_character_to_form(cid)

    def _on_new_character(self):
        self.entry_char_id.delete(0, tk.END)
        self.entry_char_speaker.delete(0, tk.END)
        self.entry_char_npc.delete(0, tk.END)
        self.entry_char_skin.delete(0, tk.END)
        self.entry_char_sound.delete(0, tk.END)
        self.char_portrait_paths = {em: "" for em in STANDARD_EMOTIONS}
        self._render_portrait_slots()

    def _on_copy_fancynpcs_cmd(self):
        cid = self.entry_char_id.get().strip().lower()
        if not cid:
            messagebox.showwarning("Peringatan", "Pilih atau isi ID karakter terlebih dahulu!")
            return
        npc_name = self.entry_char_npc.get().strip() or cid.capitalize()
        skin_name = self.entry_char_skin.get().strip() or npc_name

        cmds = (
            f"/npc create {npc_name}\n"
            f"/npc skin {npc_name} {skin_name}\n"
            f"/npc action add {npc_name} CMD:story interact {{player}} {cid}"
        )
        self.clipboard_clear()
        self.clipboard_append(cmds)
        messagebox.showinfo(
            "FancyNpcs Command Generator",
            f"Command berikut telah disalin ke clipboard:\n\n{cmds}\n\nTempelkan (Ctrl+V) langsung ke in-game chat atau server console!"
        )

    def _on_delete_character(self):
        sel = self.char_listbox.curselection()
        if not sel:
            return
        cid = self.char_listbox.get(sel[0])
        if messagebox.askyesno("Konfirmasi", f"Hapus karakter '{cid}'?"):
            fpath = os.path.join(CHARACTERS_DIR, f"{cid}.yml")
            if os.path.exists(fpath):
                os.remove(fpath)
            self.characters = load_characters()
            self._refresh_character_list()
            self._on_new_character()

    def _on_browse_portrait(self, emotion):
        cid = self.entry_char_id.get().strip().lower() or "temp"
        fn = filedialog.askopenfilename(
            title=f"Pilih Potret Emosi {emotion.upper()} (64x64, 128x128, 256x256)",
            filetypes=[("PNG Images", "*.png")]
        )
        if fn:
            # Copy to data/characters/<cid>/<emotion>.png
            char_folder = os.path.join(CHARACTERS_DIR, cid)
            os.makedirs(char_folder, exist_ok=True)
            local_dest = os.path.join(char_folder, f"{emotion}.png")
            
            try:
                # Keep exact native image resolution (128x128, etc.) without downscaling to 64x72
                shutil.copyfile(fn, local_dest)
                rel_path = f"data/characters/{cid}/{emotion}.png"
                self.char_portrait_paths[emotion] = rel_path
                self._update_portrait_preview(emotion, local_dest)
            except Exception as e:
                messagebox.showerror("Error Gambar", f"Gagal menyalin gambar: {e}")

    def _update_portrait_preview(self, emotion, path_str):
        canv = self.portrait_previews.get(emotion)
        lbl = self.portrait_labels.get(emotion)
        if not canv or not lbl:
            return

        canv.delete("all")
        if not path_str:
            lbl.config(text="Kosong", foreground="#888888")
            return

        real_path = resolve_asset_path(path_str)
        if not os.path.exists(real_path):
            lbl.config(text="Tidak Ditemukan", foreground="#d9534f")
            return

        try:
            with Image.open(real_path) as im:
                w, h = im.size
                lbl.config(text=f"{w}x{h} px", foreground="#5cb85c")
                
                # Proportional resize fitting inside 96x108 preview
                scale = min(96 / w, 108 / h)
                preview_w = max(1, int(w * scale))
                preview_h = max(1, int(h * scale))
                
                resample_filter = Image.Resampling.NEAREST if w <= 128 else Image.Resampling.LANCZOS
                preview_im = im.convert("RGBA").resize((preview_w, preview_h), resample_filter)
                photo = ImageTk.PhotoImage(preview_im)
                
                # Cache to prevent garbage collection
                self._image_cache[f"{emotion}_{real_path}"] = photo
                
                # Center-bottom align inside canvas
                pos_x = 48
                pos_y = 108 - (preview_h // 2)
                canv.create_image(pos_x, pos_y, image=photo)
        except Exception as e:
            lbl.config(text="Error", foreground="#d9534f")

    def _on_save_character(self):
        cid = self.entry_char_id.get().strip().lower()
        if not cid:
            messagebox.showerror("Error", "ID Karakter tidak boleh kosong!")
            return

        speaker = self.entry_char_speaker.get().strip() or cid.capitalize()
        npc_name = self.entry_char_npc.get().strip() or cid.capitalize()
        skin_name = self.entry_char_skin.get().strip() or npc_name
        sound = self.entry_char_sound.get().strip()

        cdata = {
            "id": cid,
            "name": speaker,
            "speaker_name": speaker,
            "fancynpc_name": npc_name,
            "fancynpc_skin": skin_name,
            "voice": {
                "sound": sound,
                "pitch": 1.0
            },
            "portraits": dict(self.char_portrait_paths)
        }

        os.makedirs(CHARACTERS_DIR, exist_ok=True)
        fpath = os.path.join(CHARACTERS_DIR, f"{cid}.yml")
        with open(fpath, "w", encoding="utf-8") as f:
            yaml.dump(cdata, f, default_flow_style=False, sort_keys=False)

        self.characters = load_characters()
        self._refresh_character_list()
        self.combo_dlg_char["values"] = sorted(self.characters.keys())
        messagebox.showinfo("Berhasil", f"Karakter '{cid}' berhasil disimpan!")

    # =========================================================================
    # TAB 2: DIALOGUE WRITER
    # =========================================================================
    def _build_dialogue_tab(self):
        left_frame = ttk.LabelFrame(self.tab_dlg, text="Daftar Dialog", width=240)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        left_frame.pack_propagate(False)

        self.dlg_listbox = tk.Listbox(
            left_frame,
            font=("Segoe UI", 10),
            bg="#202020",
            fg="#f3f3f3",
            selectbackground="#007acc",
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightbackground="#383838",
            activestyle="none",
            relief="flat"
        )
        self.dlg_listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.dlg_listbox.bind("<<ListboxSelect>>", self._on_select_dialogue)

        btn_row = ttk.Frame(left_frame)
        btn_row.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(btn_row, text="+ Baru", command=self._on_new_dialogue).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_row, text="Hapus", command=self._on_delete_dialogue).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        right_frame = ttk.LabelFrame(self.tab_dlg, text="Detail Alur Dialog")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        meta_frame = ttk.Frame(right_frame)
        meta_frame.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(meta_frame, text="ID Dialog:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_dlg_id = ttk.Entry(meta_frame, width=22)
        self.entry_dlg_id.grid(row=0, column=1, sticky="w", padx=6, pady=2)

        ttk.Label(meta_frame, text="Karakter:").grid(row=0, column=2, sticky="w", padx=6, pady=2)
        self.combo_dlg_char = ttk.Combobox(meta_frame, width=18, state="readonly")
        self.combo_dlg_char.grid(row=0, column=3, sticky="w", padx=6, pady=2)

        ttk.Label(meta_frame, text="Stage Dibutuhkan:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_dlg_stage = ttk.Entry(meta_frame, width=22)
        self.entry_dlg_stage.insert(0, "NOT_STARTED")
        self.entry_dlg_stage.grid(row=1, column=1, sticky="w", padx=6, pady=2)

        ttk.Label(meta_frame, text="Callback:").grid(row=1, column=2, sticky="w", padx=6, pady=2)
        self.entry_dlg_callback = ttk.Entry(meta_frame, width=22)
        self.entry_dlg_callback.grid(row=1, column=3, sticky="w", padx=6, pady=2)

        # Table of Lines
        lines_frame = ttk.LabelFrame(right_frame, text="Baris Kalimat (Urutan Klik-ke-Lanjut)")
        lines_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        columns = ("#", "Emosi", "Teks Kalimat")
        self.tree_lines = ttk.Treeview(lines_frame, columns=columns, show="headings", height=9)
        self.tree_lines.heading("#", text="#")
        self.tree_lines.column("#", width=35, anchor="center")
        self.tree_lines.heading("Emosi", text="Emosi Potret")
        self.tree_lines.column("Emosi", width=110, anchor="center")
        self.tree_lines.heading("Teks Kalimat", text="Teks Kalimat Visual Novel")
        self.tree_lines.column("Teks Kalimat", width=480, anchor="w")
        self.tree_lines.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        tree_scroll = ttk.Scrollbar(lines_frame, orient=tk.VERTICAL, command=self.tree_lines.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_lines.configure(yscrollcommand=tree_scroll.set)

        # Line input & editing form
        input_box = ttk.LabelFrame(right_frame, text="Editor Kalimat", padding=6)
        input_box.pack(fill=tk.X, padx=8, pady=4)

        row1 = ttk.Frame(input_box)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Emosi:").pack(side=tk.LEFT, padx=4)
        self.combo_line_emotion = ttk.Combobox(row1, values=STANDARD_EMOTIONS, width=12, state="normal")
        self.combo_line_emotion.set("biasa")
        self.combo_line_emotion.pack(side=tk.LEFT, padx=4)

        ttk.Label(row1, text="Teks:").pack(side=tk.LEFT, padx=4)
        self.entry_line_text = ttk.Entry(row1)
        self.entry_line_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.entry_line_text.bind("<Return>", lambda event: self._on_add_line())

        row2 = ttk.Frame(input_box)
        row2.pack(fill=tk.X, pady=(4, 2))
        ttk.Button(row2, text="+ Tambah Baris", command=self._on_add_line).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="✓ Simpan Edit Baris", command=self._on_update_line).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="▲ Naik", width=6, command=self._on_move_line_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="▼ Turun", width=6, command=self._on_move_line_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="📋 Duplikat", command=self._on_duplicate_line).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="🗑 Hapus Baris", command=self._on_remove_line).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="👁 Lihat di HUD", command=self._on_preview_line_in_hud).pack(side=tk.RIGHT, padx=2)

        self.tree_lines.bind("<<TreeviewSelect>>", self._on_select_tree_line)
        self.tree_lines.bind("<Double-1>", lambda e: self.entry_line_text.focus_set())

        bottom_row = ttk.Frame(right_frame)
        bottom_row.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(bottom_row, text="💾 Simpan Data Dialog", command=self._on_save_dialogue).pack(side=tk.RIGHT)

        self._refresh_dialogue_list()
        # Default auto select first dialogue if available
        if self.dialogues:
            first_dlg = sorted(self.dialogues.keys())[0]
            self.dlg_listbox.selection_set(0)
            self._load_dialogue_to_form(first_dlg)

    def _refresh_dialogue_list(self):
        self.dlg_listbox.delete(0, tk.END)
        for did in sorted(self.dialogues.keys()):
            self.dlg_listbox.insert(tk.END, did)
        self.combo_dlg_char["values"] = sorted(self.characters.keys())
        
        all_em = list(STANDARD_EMOTIONS)
        for cdata in self.characters.values():
            for em in cdata.get("portraits", {}).keys():
                if em and em not in all_em:
                    all_em.append(em)
        self.combo_line_emotion["values"] = all_em

    def _load_dialogue_to_form(self, did):
        ddata = self.dialogues.get(did, {})

        self.entry_dlg_id.delete(0, tk.END)
        self.entry_dlg_id.insert(0, did)

        char_id = ddata.get("character", "")
        self.combo_dlg_char.set(char_id)

        self.entry_dlg_stage.delete(0, tk.END)
        self.entry_dlg_stage.insert(0, ddata.get("trigger", {}).get("stage_required", "NOT_STARTED"))

        self.entry_dlg_callback.delete(0, tk.END)
        self.entry_dlg_callback.insert(0, ddata.get("callback", f"CALLBACK_{char_id.upper()}_{did.upper()}"))

        for item in self.tree_lines.get_children():
            self.tree_lines.delete(item)

        for i, line in enumerate(ddata.get("lines", []), start=1):
            self.tree_lines.insert("", tk.END, values=(i, line.get("emotion", "biasa"), line.get("text", "")))

    def _on_select_dialogue(self, event):
        sel = self.dlg_listbox.curselection()
        if not sel:
            return
        did = self.dlg_listbox.get(sel[0])
        self._load_dialogue_to_form(did)

    def _on_new_dialogue(self):
        self.entry_dlg_id.delete(0, tk.END)
        self.combo_dlg_char.set("")
        self.entry_dlg_stage.delete(0, tk.END)
        self.entry_dlg_stage.insert(0, "NOT_STARTED")
        self.entry_dlg_callback.delete(0, tk.END)
        for item in self.tree_lines.get_children():
            self.tree_lines.delete(item)

    def _on_delete_dialogue(self):
        sel = self.dlg_listbox.curselection()
        if not sel:
            return
        did = self.dlg_listbox.get(sel[0])
        if messagebox.askyesno("Konfirmasi", f"Hapus dialog '{did}'?"):
            fpath = os.path.join(DIALOGUES_DIR, f"{did}.yml")
            if os.path.exists(fpath):
                os.remove(fpath)
            self.dialogues = load_dialogues()
            self._refresh_dialogue_list()
            self._on_new_dialogue()

    def _renumber_lines(self):
        for i, item in enumerate(self.tree_lines.get_children(), start=1):
            vals = self.tree_lines.item(item, "values")
            self.tree_lines.item(item, values=(i, vals[1], vals[2]))

    def _on_select_tree_line(self, event=None):
        sel = self.tree_lines.selection()
        if not sel:
            return
        vals = self.tree_lines.item(sel[0], "values")
        if vals and len(vals) >= 3:
            self.combo_line_emotion.set(vals[1])
            self.entry_line_text.delete(0, tk.END)
            self.entry_line_text.insert(0, vals[2])
            self._preview_dialog_text = vals[2]

            # Sync character & emotion to HUD designer sample
            cur_char = self.combo_dlg_char.get()
            if hasattr(self, 'combo_sample_char') and cur_char in self.combo_sample_char["values"]:
                self.combo_sample_char.set(cur_char)
                self._on_sample_char_change()
                if hasattr(self, 'combo_sample_emotion') and vals[1] in self.combo_sample_emotion["values"]:
                    self.combo_sample_emotion.set(vals[1])

    def _on_add_line(self):
        em = self.combo_line_emotion.get()
        t = self.entry_line_text.get().strip()
        if not t:
            return
        idx = len(self.tree_lines.get_children()) + 1
        item = self.tree_lines.insert("", tk.END, values=(idx, em, t))
        self.tree_lines.selection_set(item)
        self._preview_dialog_text = t
        self.entry_line_text.delete(0, tk.END)

    def _on_update_line(self):
        sel = self.tree_lines.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih baris yang ingin diedit di tabel terlebih dahulu.")
            return
        em = self.combo_line_emotion.get()
        t = self.entry_line_text.get().strip()
        if not t:
            return
        vals = self.tree_lines.item(sel[0], "values")
        self.tree_lines.item(sel[0], values=(vals[0], em, t))
        self._preview_dialog_text = t

    def _on_move_line_up(self):
        sel = self.tree_lines.selection()
        if not sel:
            return
        item = sel[0]
        prev = self.tree_lines.prev(item)
        if prev:
            self.tree_lines.move(item, "", self.tree_lines.index(prev))
            self._renumber_lines()

    def _on_move_line_down(self):
        sel = self.tree_lines.selection()
        if not sel:
            return
        item = sel[0]
        nxt = self.tree_lines.next(item)
        if nxt:
            self.tree_lines.move(nxt, "", self.tree_lines.index(item))
            self._renumber_lines()

    def _on_duplicate_line(self):
        sel = self.tree_lines.selection()
        if not sel:
            return
        vals = self.tree_lines.item(sel[0], "values")
        idx = self.tree_lines.index(sel[0]) + 1
        new_item = self.tree_lines.insert("", idx, values=(vals[0], vals[1], vals[2]))
        self._renumber_lines()
        self.tree_lines.selection_set(new_item)

    def _on_remove_line(self):
        sel = self.tree_lines.selection()
        if sel:
            self.tree_lines.delete(sel[0])
            self._renumber_lines()

    def _on_preview_line_in_hud(self):
        sel = self.tree_lines.selection()
        if sel:
            vals = self.tree_lines.item(sel[0], "values")
            self._preview_dialog_text = vals[2]
            cur_char = self.combo_dlg_char.get()
            if hasattr(self, 'combo_sample_char') and cur_char in self.combo_sample_char["values"]:
                self.combo_sample_char.set(cur_char)
                self._on_sample_char_change()
                if hasattr(self, 'combo_sample_emotion') and vals[1] in self.combo_sample_emotion["values"]:
                    self.combo_sample_emotion.set(vals[1])
            self._redraw_hud_canvas()
            self.notebook.select(self.tab_hud)

    def _on_save_dialogue(self):
        did = self.entry_dlg_id.get().strip().lower()
        if not did:
            messagebox.showerror("Error", "ID Dialog tidak boleh kosong!")
            return
        char_id = self.combo_dlg_char.get().strip()
        if not char_id:
            messagebox.showerror("Error", "Pilih Karakter untuk dialog ini!")
            return

        lines = []
        for item in self.tree_lines.get_children():
            vals = self.tree_lines.item(item, "values")
            lines.append({
                "emotion": vals[1],
                "text": vals[2]
            })

        ddata = {
            "id": did,
            "character": char_id,
            "trigger": {
                "type": "fancynpc",
                "stage_required": self.entry_dlg_stage.get().strip() or "NOT_STARTED"
            },
            "lines": lines,
            "callback": self.entry_dlg_callback.get().strip()
        }

        os.makedirs(DIALOGUES_DIR, exist_ok=True)
        fpath = os.path.join(DIALOGUES_DIR, f"{did}.yml")
        with open(fpath, "w", encoding="utf-8") as f:
            yaml.dump(ddata, f, default_flow_style=False, sort_keys=False)

        self.dialogues = load_dialogues()
        self._refresh_dialogue_list()
        messagebox.showinfo("Berhasil", f"Dialog '{did}' berhasil disimpan!")

    # =========================================================================
    # TAB 3: VISUAL HUD DESIGNER (DRAG & DROP, RESIZE, INTERACTIVE CANVAS)
    # =========================================================================
    def _save_hud_snapshot(self):
        if self._is_undoing_or_redoing:
            return
        self._hud_undo_stack.append(copy.deepcopy(self.hud_cfg))
        if len(self._hud_undo_stack) > 50:
            self._hud_undo_stack.pop(0)
        self._hud_redo_stack.clear()

    def _hud_undo(self):
        if not self._hud_undo_stack:
            return
        self._is_undoing_or_redoing = True
        try:
            self._hud_redo_stack.append(copy.deepcopy(self.hud_cfg))
            self.hud_cfg = self._hud_undo_stack.pop()
            self._refresh_group_combo()
            self._update_hud_editor_fields()
            self._redraw_hud_canvas()
        finally:
            self._is_undoing_or_redoing = False

    def _hud_redo(self):
        if not self._hud_redo_stack:
            return
        self._is_undoing_or_redoing = True
        try:
            self._hud_undo_stack.append(copy.deepcopy(self.hud_cfg))
            self.hud_cfg = self._hud_redo_stack.pop()
            self._refresh_group_combo()
            self._update_hud_editor_fields()
            self._redraw_hud_canvas()
        finally:
            self._is_undoing_or_redoing = False

    def _on_shortcut_undo(self, event=None):
        try:
            if self.notebook.select() == str(self.tab_hud):
                self._hud_undo()
                return "break"
        except Exception:
            pass

    def _on_shortcut_redo(self, event=None):
        try:
            if self.notebook.select() == str(self.tab_hud):
                self._hud_redo()
                return "break"
        except Exception:
            pass

    def _build_hud_tab(self):
        # Load initial configuration and populate groups
        self.hud_cfg = load_hud_config()
        if "groups" not in self.hud_cfg or not self.hud_cfg["groups"]:
            current_elems = list(self.hud_cfg.get("elements", {}).keys())
            self.hud_cfg["groups"] = {
                "Semua Elemen (All)": list(current_elems),
                "Kotak Dialog & Teks": [k for k in ["dialog_box", "dialog_text", "counter_text"] if k in current_elems],
                "Potret & Nama": [k for k in ["portrait", "nameplate", "speaker_text"] if k in current_elems],
                "Semua Teks": [k for k in ["speaker_text", "dialog_text", "counter_text"] if k in current_elems]
            }

        pane = ttk.PanedWindow(self.tab_hud, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left Canvas Viewport - 16:9 Letterbox Container
        left_box = ttk.LabelFrame(pane, text="Pratinjau Akurat Minecraft 16:9 (Klik & Geser Elemen)", padding=6)
        pane.add(left_box, weight=3)

        # Sample Character & Emotion Bar on top of Canvas
        sample_bar = ttk.Frame(left_box, padding=(4, 2, 4, 6))
        sample_bar.pack(fill=tk.X)

        ttk.Label(sample_bar, text="Sample NPC:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(2, 4))
        self.combo_sample_char = ttk.Combobox(sample_bar, state="readonly", width=14)
        self.combo_sample_char.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_sample_char.bind("<<ComboboxSelected>>", self._on_sample_char_change)

        ttk.Label(sample_bar, text="Emosi:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(4, 4))
        self.combo_sample_emotion = ttk.Combobox(sample_bar, state="readonly", width=12)
        self.combo_sample_emotion.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_sample_emotion.bind("<<ComboboxSelected>>", lambda e: self._redraw_hud_canvas())

        self.var_show_textures = tk.BooleanVar(value=True)
        ttk.Checkbutton(sample_bar, text="Tampilkan Sprite Asli", variable=self.var_show_textures, command=self._redraw_hud_canvas).pack(side=tk.RIGHT, padx=4)

        # Interactive Test Dialogue Text Entry & Presets
        test_txt_bar = ttk.Frame(left_box, padding=(4, 2, 4, 4))
        test_txt_bar.pack(fill=tk.X)

        ttk.Label(test_txt_bar, text="Teks Uji:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(2, 4))
        self.entry_test_dialog = ttk.Entry(test_txt_bar)
        self.entry_test_dialog.insert(0, "Tapi tempat ini menyimpan hawa janggal... Tanah di sekitar sumur seolah berbisik memanggil nama asing.")
        self.entry_test_dialog.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.entry_test_dialog.bind("<KeyRelease>", self._on_test_dialog_change)

        self.btn_reset_test_txt = ttk.Button(test_txt_bar, text="Teks Panjang", width=12, command=self._load_long_preset_text)
        self.btn_reset_test_txt.pack(side=tk.RIGHT, padx=2)

        self.canvas_container = ttk.Frame(left_box)
        self.canvas_container.pack(fill=tk.BOTH, expand=True)

        self.hud_canvas = tk.Canvas(self.canvas_container, bg="#0d0d12", highlightthickness=0)
        self.hud_canvas.pack(fill=tk.BOTH, expand=True)

        # Coordinate transform states
        self.hud_view = {"scale": 1.0, "ox": 0, "oy": 0, "vw": 640, "vh": 360}
        self.canvas_container.bind("<Configure>", self._on_canvas_resize)

        # Drag & select state
        self._hud_drag_data = {"item": None, "x": 0, "y": 0, "elem_key": None, "is_group": False}
        self.hud_canvas.bind("<ButtonPress-1>", self._on_hud_canvas_click)
        self.hud_canvas.bind("<B1-Motion>", self._on_hud_canvas_drag)
        self.hud_canvas.bind("<ButtonRelease-1>", self._on_hud_canvas_release)
        self.hud_canvas.bind("<Motion>", self._on_hud_canvas_motion)

        # Canvas Keyboard Nudge bindings
        self.hud_canvas.bind("<Left>", lambda e: self._nudge(-1, 0))
        self.hud_canvas.bind("<Right>", lambda e: self._nudge(1, 0))
        self.hud_canvas.bind("<Up>", lambda e: self._nudge(0, -1))
        self.hud_canvas.bind("<Down>", lambda e: self._nudge(0, 1))
        self.hud_canvas.bind("<Shift-Left>", lambda e: self._nudge(-5, 0))
        self.hud_canvas.bind("<Shift-Right>", lambda e: self._nudge(5, 0))
        self.hud_canvas.bind("<Shift-Up>", lambda e: self._nudge(0, -5))
        self.hud_canvas.bind("<Shift-Down>", lambda e: self._nudge(0, 5))

        # Controls & Properties on the Right (Scrollable Container)
        right_container = ttk.LabelFrame(pane, text="Properti Elemen & Kontrol Ukuran", width=330, padding=4)
        pane.add(right_container, weight=1)

        self.scroll_canvas_r = tk.Canvas(right_container, bg="#181818", highlightthickness=0)
        scroll_bar_r = ttk.Scrollbar(right_container, orient=tk.VERTICAL, command=self.scroll_canvas_r.yview)
        right_box = ttk.Frame(self.scroll_canvas_r)

        right_box.bind("<Configure>", lambda e: self.scroll_canvas_r.configure(scrollregion=self.scroll_canvas_r.bbox("all")))
        win_id = self.scroll_canvas_r.create_window((0, 0), window=right_box, anchor="nw")
        self.scroll_canvas_r.bind("<Configure>", lambda e: self.scroll_canvas_r.itemconfig(win_id, width=e.width))
        self.scroll_canvas_r.configure(yscrollcommand=scroll_bar_r.set)

        self.scroll_canvas_r.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_bar_r.pack(side=tk.RIGHT, fill=tk.Y)

        # 1. Top Toolbar: Undo & Redo
        tb_frame = ttk.Frame(right_box)
        tb_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(tb_frame, text="↶ Undo (Ctrl+Z)", command=self._hud_undo).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(tb_frame, text="↷ Redo (Ctrl+Y)", command=self._hud_redo).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # 2. Group Management Section
        grp_frame = ttk.LabelFrame(right_box, text="Mode & Pemilihan Group", padding=6)
        grp_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(grp_frame, text="Pilih Group:").pack(anchor="w", pady=(0, 2))
        self.combo_hud_group = ttk.Combobox(grp_frame, state="readonly")
        self.combo_hud_group.pack(fill=tk.X, pady=(0, 4))
        self.combo_hud_group.bind("<<ComboboxSelected>>", self._on_hud_group_selected)

        grp_btn_box = ttk.Frame(grp_frame)
        grp_btn_box.pack(fill=tk.X, pady=(2, 4))
        ttk.Button(grp_btn_box, text="+ Tambah Group", command=self._on_add_hud_group).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(grp_btn_box, text="🗑 Hapus Group", command=self._on_delete_hud_group).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # Group Scale & Nudge Frame (active in group mode)
        self.frame_group_tools = ttk.Frame(grp_frame)
        ttk.Label(self.frame_group_tools, text="Skala Group (Perbesar / Perkecil):").pack(anchor="w", pady=(4, 1))
        scale_grp_row = ttk.Frame(self.frame_group_tools)
        scale_grp_row.pack(fill=tk.X, pady=(0, 4))
        self.scale_group_slider = ttk.Scale(scale_grp_row, from_=0.4, to=2.0, orient=tk.HORIZONTAL, command=self._on_group_slider_scale)
        self.scale_group_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.scale_group_slider.set(1.0)
        self.scale_group_slider.bind("<ButtonRelease-1>", self._on_group_slider_release)
        ttk.Button(scale_grp_row, text="1.0x", width=4, command=self._reset_group_scale).pack(side=tk.LEFT, padx=(4, 0))

        # 3. Single Element Selector
        elem_frame = ttk.LabelFrame(right_box, text="Properti Elemen Tunggal", padding=6)
        elem_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(elem_frame, text="Pilih Elemen:").pack(anchor="w", pady=(0, 2))
        elem_sel_row = ttk.Frame(elem_frame)
        elem_sel_row.pack(fill=tk.X, pady=(0, 4))

        self.combo_hud_elem = ttk.Combobox(
            elem_sel_row,
            state="readonly"
        )
        self.combo_hud_elem.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.combo_hud_elem.bind("<<ComboboxSelected>>", self._on_hud_elem_selected)

        self.btn_delete_hud_elem = ttk.Button(
            elem_sel_row,
            text="🗑️ Hapus",
            width=8,
            command=self._on_delete_hud_element
        )
        self.btn_delete_hud_elem.pack(side=tk.RIGHT)

        # Restore / Add Deleted Elements row
        self.frame_add_elem = ttk.Frame(elem_frame)
        self.frame_add_elem.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(self.frame_add_elem, text="➕ Tambah:", font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.combo_add_elem = ttk.Combobox(self.frame_add_elem, state="readonly", width=14)
        self.combo_add_elem.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        self.btn_add_hud_elem = ttk.Button(
            self.frame_add_elem,
            text="Tambah",
            width=7,
            command=self._on_add_hud_element
        )
        self.btn_add_hud_elem.pack(side=tk.RIGHT)

        # Tombol Custom HUD Element Builder
        self.btn_create_custom_hud = ttk.Button(
            elem_frame,
            text="+ Buat Custom HUD Dialog",
            command=self._on_create_custom_hud_dialog
        )
        self.btn_create_custom_hud.pack(fill=tk.X, pady=(2, 6))

        # Mode Ukuran Potret (64x64 vs 128x128)
        self.frame_portrait_mode = ttk.LabelFrame(elem_frame, text="Resolusi Dasar Potret", padding=4)
        self.frame_portrait_mode.pack(fill=tk.X, pady=(0, 6))
        self.var_portrait_base = tk.IntVar(value=128)
        ttk.Radiobutton(self.frame_portrait_mode, text="128x128 (Native HD)", variable=self.var_portrait_base, value=128, command=self._on_change_portrait_base).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(self.frame_portrait_mode, text="64x64 (Classic)", variable=self.var_portrait_base, value=64, command=self._on_change_portrait_base).pack(side=tk.LEFT, padx=4)

        # Coords and Scale controls
        prop_frame = ttk.Frame(elem_frame)
        prop_frame.pack(fill=tk.X, pady=4)

        ttk.Label(prop_frame, text="Posisi X:").grid(row=0, column=0, sticky="w", pady=3)
        self.spin_hud_x = ttk.Spinbox(prop_frame, from_=-400, to=800, width=8, command=self._on_hud_val_change)
        self.spin_hud_x.grid(row=0, column=1, sticky="w", padx=4, pady=3)
        self.spin_hud_x.bind("<KeyRelease>", lambda e: self._on_hud_val_change())

        ttk.Label(prop_frame, text="Posisi Y:").grid(row=1, column=0, sticky="w", pady=3)
        self.spin_hud_y = ttk.Spinbox(prop_frame, from_=-400, to=800, width=8, command=self._on_hud_val_change)
        self.spin_hud_y.grid(row=1, column=1, sticky="w", padx=4, pady=3)
        self.spin_hud_y.bind("<KeyRelease>", lambda e: self._on_hud_val_change())

        ttk.Label(prop_frame, text="Scale:").grid(row=2, column=0, sticky="w", pady=3)
        self.spin_hud_scale = ttk.Spinbox(prop_frame, from_=0.1, to=3.0, increment=0.05, width=8, command=self._on_hud_val_change)
        self.spin_hud_scale.grid(row=2, column=1, sticky="w", padx=4, pady=3)
        self.spin_hud_scale.bind("<KeyRelease>", lambda e: self._on_hud_val_change())

        ttk.Label(prop_frame, text="Layer / Z:").grid(row=3, column=0, sticky="w", pady=3)
        self.spin_hud_layer = ttk.Spinbox(prop_frame, from_=1, to=20, increment=1, width=8, command=self._on_hud_val_change)
        self.spin_hud_layer.grid(row=3, column=1, sticky="w", padx=4, pady=3)
        self.spin_hud_layer.bind("<KeyRelease>", lambda e: self._on_hud_val_change())

        # Scale slider for single element
        ttk.Label(elem_frame, text="Slider Scale Elemen:").pack(anchor="w", pady=(6, 2))
        self.scale_slider = ttk.Scale(elem_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL, command=self._on_slider_scale)
        self.scale_slider.pack(fill=tk.X, pady=(0, 4))
        self.scale_slider.bind("<ButtonRelease-1>", self._on_scale_slider_release)

        # Text property editor (Pola Teks, Spasi, Split Width)
        self.frame_text_props = ttk.LabelFrame(elem_frame, text="Pengaturan Teks", padding=4)
        self.frame_text_props.pack(fill=tk.X, pady=(4, 6))

        ttk.Label(self.frame_text_props, text="Karakter Spasi Antar-Huruf:").pack(anchor="w")
        self.spin_hud_space = ttk.Spinbox(self.frame_text_props, from_=-10, to=20, width=8, command=self._on_hud_val_change)
        self.spin_hud_space.pack(anchor="w", pady=2)
        self.spin_hud_space.bind("<KeyRelease>", lambda e: self._on_hud_val_change())

        self.lbl_hud_split_w = ttk.Label(self.frame_text_props, text="Lebar Baris Teks (Aman: 170 - 220):")
        self.spin_hud_split_w = ttk.Spinbox(self.frame_text_props, from_=50, to=320, width=8, command=self._on_hud_val_change)
        self.spin_hud_split_w.bind("<KeyRelease>", lambda e: self._on_hud_val_change())

        self.slider_split_w = ttk.Scale(self.frame_text_props, from_=50, to=320, orient=tk.HORIZONTAL, command=self._on_split_w_slider)

        self.var_hud_shadow = tk.BooleanVar(value=True)
        self.chk_hud_shadow = ttk.Checkbutton(self.frame_text_props, text="Drop Shadow (Bayangan Teks)", variable=self.var_hud_shadow, command=self._on_hud_val_change)
        self.chk_hud_shadow.pack(anchor="w", pady=(4, 2))

        # 4. Custom UI Textures Frame
        tex_frame = ttk.LabelFrame(right_box, text="Tekstur UI Kotak & Nameplate", padding=6)
        tex_frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(tex_frame, text="Tekstur Dialog Box:").pack(anchor="w", pady=(2, 1))
        self.combo_hud_box_tex = ttk.Combobox(tex_frame, state="readonly")
        self.combo_hud_box_tex.pack(fill=tk.X, pady=(0, 4))
        self.combo_hud_box_tex.bind("<<ComboboxSelected>>", self._on_hud_texture_selected)

        ttk.Label(tex_frame, text="Tekstur Nameplate:").pack(anchor="w", pady=(2, 1))
        self.combo_hud_np_tex = ttk.Combobox(tex_frame, state="readonly")
        self.combo_hud_np_tex.pack(fill=tk.X, pady=(0, 4))
        self.combo_hud_np_tex.bind("<<ComboboxSelected>>", self._on_hud_texture_selected)

        tex_btn_row = ttk.Frame(tex_frame)
        tex_btn_row.pack(fill=tk.X, pady=(2, 2))
        ttk.Button(tex_btn_row, text="+ Import Tekstur Baru", command=self._on_import_custom_texture).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(tex_btn_row, text="🔄 Refresh", width=9, command=self._refresh_hud_textures).pack(side=tk.LEFT, padx=(2, 0))

        # 5. Nudge Navigation Buttons
        nudge_frame = ttk.LabelFrame(right_box, text="Geser Halus (Nudge 1px / Shift 5px)", padding=4)
        nudge_frame.pack(fill=tk.X, pady=(0, 6))
        n_row1 = ttk.Frame(nudge_frame)
        n_row1.pack(pady=1)
        ttk.Button(n_row1, text="▲", width=3, command=lambda: self._nudge(0, -1)).pack()
        n_row2 = ttk.Frame(nudge_frame)
        n_row2.pack(pady=1)
        ttk.Button(n_row2, text="◀", width=3, command=lambda: self._nudge(-1, 0)).pack(side=tk.LEFT, padx=3)
        ttk.Button(n_row2, text="▼", width=3, command=lambda: self._nudge(0, 1)).pack(side=tk.LEFT, padx=3)
        ttk.Button(n_row2, text="▶", width=3, command=lambda: self._nudge(1, 0)).pack(side=tk.LEFT, padx=3)

        # 6. Action Buttons
        btn_grid = ttk.Frame(right_box)
        btn_grid.pack(fill=tk.X, pady=8)
        ttk.Button(btn_grid, text="💾 Simpan Layout", command=self._on_save_hud_config).pack(fill=tk.X, pady=3)
        ttk.Button(btn_grid, text="⚡ Simpan & Compile Langsung", command=self._on_save_and_compile_hud).pack(fill=tk.X, pady=3)
        ttk.Button(btn_grid, text="↺ Reset Default", command=self._on_reset_hud_config).pack(fill=tk.X, pady=3)

        hint = (
            "Panduan Interaktif:\n"
            "• Geser elemen langsung di layar atau pilih Group untuk gerak bersama.\n"
            "• Klik teks dialog untuk memunculkan Canva handle (↔ lebar, ● skala).\n"
            "• Tekan Ctrl+Z untuk Undo, Ctrl+Shift+Z / Ctrl+Y untuk Redo.\n"
            "• Gunakan tombol panah pada keyboard untuk nudge 1px (Shift + panah = 5px).\n"
            "• Ganti tekstur kotak dialog & nameplate secara instan dengan dropdown tekstur."
        )
        ttk.Label(right_box, text=hint, justify=tk.LEFT, foreground="#888888").pack(anchor="w", pady=(8, 0))

        # Load initial configuration and populate groups
        self.hud_cfg = load_hud_config()
        self._hud_canvas_items = {}
        self._refresh_group_combo()
        self._refresh_hud_elements_combo()
        self._refresh_sample_chars()
        self._refresh_hud_textures()
        self._update_hud_editor_fields()

    def _refresh_hud_elements_combo(self):
        ALL_HUD_ELEMENTS = ["bottom_cinematic_fade", "portrait", "nameplate", "dialog_box", "speaker_text", "dialog_text", "counter_text"]
        elems = self.hud_cfg.setdefault("elements", {})
        custom_elems = self.hud_cfg.setdefault("custom_elements", {})
        for ck, cv in custom_elems.items():
            if ck not in elems:
                elems[ck] = {
                    "x": cv.get("x", 0),
                    "y": cv.get("y", 0),
                    "scale": cv.get("scale", 1.0),
                    "layer": cv.get("layer", 2)
                }
        present = [k for k in ALL_HUD_ELEMENTS if k in elems]
        for k in elems.keys():
            if k not in present:
                present.append(k)

        self.combo_hud_elem["values"] = present
        cur = self.combo_hud_elem.get()
        if cur not in present:
            if present:
                self.combo_hud_elem.set(present[0])
            else:
                self.combo_hud_elem.set("")

        missing = [k for k in ALL_HUD_ELEMENTS if k not in elems]
        if hasattr(self, 'frame_add_elem') and hasattr(self, 'combo_add_elem'):
            if missing:
                self.combo_add_elem["values"] = missing
                self.combo_add_elem.set(missing[0])
                self.frame_add_elem.pack(fill=tk.X, pady=(0, 6))
            else:
                self.frame_add_elem.pack_forget()

    def _on_delete_hud_element(self):
        cur = self.combo_hud_elem.get()
        if not cur:
            messagebox.showinfo("Informasi", "Pilih elemen yang ingin dihapus terlebih dahulu.")
            return

        elems = self.hud_cfg.setdefault("elements", {})
        if cur not in elems:
            return

        elem_name_map = {
            "bottom_cinematic_fade": "Cinematic Fade (Dasar)",
            "portrait": "Potret Karakter",
            "nameplate": "Pelat Nama",
            "dialog_box": "Kotak Dialog",
            "speaker_text": "Teks Nama",
            "dialog_text": "Isi Teks Dialog",
            "counter_text": "Counter Dialog"
        }
        display_name = elem_name_map.get(cur, cur)

        confirm = messagebox.askyesno(
            "Konfirmasi Hapus Elemen",
            f"Apakah kamu yakin ingin menghapus elemen '{display_name}' ({cur}) dari HUD?\n\nElemen ini tidak akan ditampilkan lagi dan akan dihapus dari konfigurasi."
        )
        if not confirm:
            return

        self._save_hud_snapshot()
        del elems[cur]
        if "custom_elements" in self.hud_cfg and cur in self.hud_cfg["custom_elements"]:
            del self.hud_cfg["custom_elements"][cur]

        # Clean from all groups
        for g_name, g_list in list(self.hud_cfg.get("groups", {}).items()):
            if cur in g_list:
                g_list.remove(cur)

        try:
            save_hud_config(self.hud_cfg)
            from compiler import compile_portraits_and_betterhud
            compile_portraits_and_betterhud(self.characters)
        except Exception as e:
            self._log(f"[WARN] Compile HUD setelah hapus elemen: {e}")

        self._refresh_hud_elements_combo()
        self._refresh_group_combo()
        self._update_hud_editor_fields()
        self._redraw_hud_canvas()
        self._log(f"[HUD] Elemen '{cur}' berhasil dihapus.")

    def _on_add_hud_element(self):
        to_add = self.combo_add_elem.get()
        if not to_add:
            return

        HUD_ELEMENT_DEFAULTS = {
            "bottom_cinematic_fade": {"x": 0, "y": -45, "scale": 2.5, "layer": 1},
            "portrait": {"x": 38, "y": -54, "scale": 0.78, "base_size": 128, "layer": 3},
            "nameplate": {"x": 56, "y": 38, "scale": 1.0, "layer": 4},
            "dialog_box": {"x": 0, "y": 0, "scale": 1.0, "layer": 2},
            "speaker_text": {"x": 64, "y": 44, "scale": 0.52, "color": "<#FFFFFF>", "space": 0, "layer": 5, "align": "left"},
            "dialog_text": {"x": 98, "y": 5, "scale": 0.46, "color": "<#F0F0F0>", "line": 4, "split_width": 145, "line_width": 9, "space": 0, "layer": 5, "align": "left"},
            "counter_text": {"x": 284, "y": 39, "scale": 0.45, "color": "<#DDDDDD>", "space": 0, "layer": 5}
        }

        self._save_hud_snapshot()
        elems = self.hud_cfg.setdefault("elements", {})
        elems[to_add] = dict(HUD_ELEMENT_DEFAULTS.get(to_add, {"x": 0, "y": 0, "scale": 1.0}))

        groups = self.hud_cfg.setdefault("groups", {})
        if "Semua Elemen (All)" in groups and to_add not in groups["Semua Elemen (All)"]:
            groups["Semua Elemen (All)"].append(to_add)

        try:
            save_hud_config(self.hud_cfg)
            from compiler import compile_portraits_and_betterhud
            compile_portraits_and_betterhud(self.characters)
        except Exception as e:
            self._log(f"[WARN] Compile HUD setelah tambah elemen: {e}")

        self._refresh_hud_elements_combo()
        self._refresh_group_combo()
        self.combo_hud_elem.set(to_add)
        self._update_hud_editor_fields()
        self._redraw_hud_canvas()
        self._log(f"[HUD] Elemen '{to_add}' berhasil ditambahkan kembali.")

    def _on_test_dialog_change(self, event=None):
        self._redraw_hud_canvas()

    def _load_long_preset_text(self):
        long_sample = "Perkenalkan, namaku Luna. Aku seorang penjelajah botani independen yang mencari benih bunga langka di kedalaman hutan rimba mistis Aethir."
        if hasattr(self, 'entry_test_dialog'):
            self.entry_test_dialog.delete(0, tk.END)
            self.entry_test_dialog.insert(0, long_sample)
        self._redraw_hud_canvas()

    def _refresh_sample_chars(self):
        char_ids = list(self.characters.keys())
        self.combo_sample_char["values"] = char_ids
        cur = self.combo_sample_char.get()
        if cur not in char_ids and char_ids:
            cur = "luna" if "luna" in char_ids else char_ids[0]
            self.combo_sample_char.set(cur)
        self._on_sample_char_change()

    def _on_sample_char_change(self, event=None):
        char_id = self.combo_sample_char.get()
        if not char_id or char_id not in self.characters:
            self.combo_sample_emotion["values"] = []
            return
        cdata = self.characters[char_id]
        portraits = cdata.get("portraits", {})
        emotions = list(portraits.keys())
        if not emotions:
            emotions = ["biasa"]
        self.combo_sample_emotion["values"] = emotions
        cur_em = self.combo_sample_emotion.get()
        if cur_em not in emotions:
            cur_em = "biasa" if "biasa" in emotions else emotions[0]
            self.combo_sample_emotion.set(cur_em)
        self._redraw_hud_canvas()

    def _get_current_sample_portrait_path(self):
        char_id = self.combo_sample_char.get()
        emotion = self.combo_sample_emotion.get()
        if not char_id or char_id not in self.characters:
            return None
        cdata = self.characters[char_id]
        portraits = cdata.get("portraits", {})
        path_str = portraits.get(emotion) or portraits.get("biasa") or ""
        if not path_str and portraits:
            path_str = next(iter(portraits.values()))
        if path_str:
            resolved = resolve_asset_path(path_str)
            if resolved and os.path.exists(resolved):
                return resolved
        return None

    def _refresh_hud_textures(self):
        font_dir = get_font_textures_dir()
        png_files = []
        if os.path.exists(font_dir):
            png_files = [f for f in os.listdir(font_dir) if f.lower().endswith(".png")]
        if not png_files:
            png_files = ["dialogue_box.png", "nameplate.png"]

        sorted_files = sorted(png_files)
        if hasattr(self, "combo_hud_box_tex"):
            self.combo_hud_box_tex["values"] = sorted_files
        if hasattr(self, "combo_hud_np_tex"):
            self.combo_hud_np_tex["values"] = sorted_files
        if hasattr(self, "combo_asset_box_tex"):
            self.combo_asset_box_tex["values"] = sorted_files
        if hasattr(self, "combo_asset_np_tex"):
            self.combo_asset_np_tex["values"] = sorted_files

        tex_cfg = self.hud_cfg.get("textures", {})
        box_tex = tex_cfg.get("dialog_box", "dialogue_box.png")
        np_tex = tex_cfg.get("nameplate", "nameplate.png")

        sel_box = box_tex if box_tex in sorted_files else (sorted_files[0] if sorted_files else "")
        sel_np = np_tex if np_tex in sorted_files else (sorted_files[0] if sorted_files else "")

        if hasattr(self, "combo_hud_box_tex"):
            self.combo_hud_box_tex.set(sel_box)
        if hasattr(self, "combo_asset_box_tex"):
            self.combo_asset_box_tex.set(sel_box)

        if hasattr(self, "combo_hud_np_tex"):
            self.combo_hud_np_tex.set(sel_np)
        if hasattr(self, "combo_asset_np_tex"):
            self.combo_asset_np_tex.set(sel_np)

    def _on_hud_texture_selected(self, event=None):
        self._save_hud_snapshot()
        self._texture_ram_cache.clear()
        self._hud_image_refs.clear()
        tex_cfg = self.hud_cfg.setdefault("textures", {})
        box_val = self.combo_hud_box_tex.get()
        np_val = self.combo_hud_np_tex.get()
        tex_cfg["dialog_box"] = box_val
        tex_cfg["nameplate"] = np_val
        if hasattr(self, "combo_asset_box_tex"):
            self.combo_asset_box_tex.set(box_val)
        if hasattr(self, "combo_asset_np_tex"):
            self.combo_asset_np_tex.set(np_val)
        save_hud_config(self.hud_cfg)
        try:
            from compiler import compile_portraits_and_betterhud
            compile_portraits_and_betterhud(self.characters)
        except Exception:
            pass
        self._redraw_hud_canvas()

    def _on_import_custom_texture(self):
        fn = filedialog.askopenfilename(
            title="Pilih File Tekstur PNG (Dialog Box / Nameplate / Custom HUD)",
            filetypes=[("PNG Textures", "*.png")]
        )
        if not fn:
            return

        font_dir = get_font_textures_dir()
        os.makedirs(font_dir, exist_ok=True)
        fname = os.path.basename(fn)
        dest = os.path.join(font_dir, fname)

        try:
            shutil.copyfile(fn, dest)
            self._texture_ram_cache.clear()
            self._hud_image_refs.clear()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyalin file tekstur: {e}")
            return

        # Modal dialog: Pilih target penerapan tekstur
        pick_dlg = tk.Toplevel(self)
        pick_dlg.title("Pasang Tekstur yang Diimpor")
        pick_dlg.geometry("440x300")
        pick_dlg.resizable(False, False)
        pick_dlg.transient(self)
        pick_dlg.grab_set()

        ttk.Label(
            pick_dlg,
            text=f"Tekstur '{fname}' berhasil diimpor!\\nPilih bagaimana Anda ingin menggunakan tekstur ini:",
            font=("Segoe UI", 9, "bold"),
            justify="center",
            wraplength=400
        ).pack(pady=(16, 12), padx=16)

        def _apply_box():
            tex_cfg = self.hud_cfg.setdefault("textures", {})
            tex_cfg["dialog_box"] = fname
            self._refresh_hud_textures()
            if hasattr(self, "combo_hud_box_tex"):
                self.combo_hud_box_tex.set(fname)
            if hasattr(self, "combo_asset_box_tex"):
                self.combo_asset_box_tex.set(fname)
            self._texture_ram_cache.clear()
            self._hud_image_refs.clear()
            save_hud_config(self.hud_cfg)
            try:
                from compiler import compile_portraits_and_betterhud
                compile_portraits_and_betterhud(self.characters)
            except Exception:
                pass
            self._redraw_hud_canvas()
            pick_dlg.destroy()
            messagebox.showinfo("Berhasil", f"Tekstur Kotak Dialog berhasil diganti ke '{fname}'!", parent=self)

        def _apply_nameplate():
            tex_cfg = self.hud_cfg.setdefault("textures", {})
            tex_cfg["nameplate"] = fname
            self._refresh_hud_textures()
            if hasattr(self, "combo_hud_np_tex"):
                self.combo_hud_np_tex.set(fname)
            if hasattr(self, "combo_asset_np_tex"):
                self.combo_asset_np_tex.set(fname)
            self._texture_ram_cache.clear()
            self._hud_image_refs.clear()
            save_hud_config(self.hud_cfg)
            try:
                from compiler import compile_portraits_and_betterhud
                compile_portraits_and_betterhud(self.characters)
            except Exception:
                pass
            self._redraw_hud_canvas()
            pick_dlg.destroy()
            messagebox.showinfo("Berhasil", f"Tekstur Pelat Nama berhasil diganti ke '{fname}'!", parent=self)

        def _apply_custom():
            pick_dlg.destroy()
            self._on_create_custom_hud_dialog(default_file=fname)

        def _apply_only_save():
            self._refresh_hud_textures()
            if hasattr(self, '_refresh_assets_gallery'):
                self._refresh_assets_gallery()
            self._redraw_hud_canvas()
            pick_dlg.destroy()
            messagebox.showinfo("Tersimpan", f"Tekstur '{fname}' disimpan di direktori aset font.\nAnda dapat memilihnya lewat dropdown kapan saja.", parent=self)

        btn_box = ttk.Frame(pick_dlg)
        btn_box.pack(fill=tk.BOTH, expand=True, padx=24, pady=6)

        ttk.Button(btn_box, text="🖼️ Terapkan ke Kotak Dialog (dialog_box)", command=_apply_box).pack(fill=tk.X, pady=3)
        ttk.Button(btn_box, text="🏷️ Terapkan ke Pelat Nama (nameplate)", command=_apply_nameplate).pack(fill=tk.X, pady=3)
        ttk.Button(btn_box, text="✨ Jadikan Elemen Custom HUD Baru", command=_apply_custom).pack(fill=tk.X, pady=3)
        ttk.Button(btn_box, text="💾 Hanya Simpan (Pilih Manual)", command=_apply_only_save).pack(fill=tk.X, pady=3)

    def _get_dialog_box_texture_path(self):
        font_dir = get_font_textures_dir()
        tex_cfg = self.hud_cfg.get("textures", {})
        fname = tex_cfg.get("dialog_box", "dialogue_box.png")
        p = os.path.join(font_dir, fname)
        if os.path.exists(p):
            return p
        fallback = os.path.join(font_dir, "dialogue_box.png")
        if os.path.exists(fallback):
            return fallback
        return DIALOG_BOX_TEXTURE

    def _get_nameplate_texture_path(self):
        font_dir = get_font_textures_dir()
        tex_cfg = self.hud_cfg.get("textures", {})
        fname = tex_cfg.get("nameplate", "nameplate.png")
        p = os.path.join(font_dir, fname)
        if os.path.exists(p):
            return p
        fallback = os.path.join(font_dir, "nameplate.png")
        if os.path.exists(fallback):
            return fallback
        return NAMEPLATE_TEXTURE

    def _refresh_group_combo(self):
        groups = list(self.hud_cfg.get("groups", {}).keys())
        all_vals = ["[Tunggal / Single Element]"] + groups
        self.combo_hud_group["values"] = all_vals
        cur = self.combo_hud_group.get()
        if cur not in all_vals:
            self.combo_hud_group.set("[Tunggal / Single Element]")

    def _on_hud_group_selected(self, event=None):
        cur = self.combo_hud_group.get()
        if cur != "[Tunggal / Single Element]":
            self.frame_group_tools.pack(fill=tk.X, pady=(2, 0))
            self.scale_group_slider.set(1.0)
            self._group_scaling_in_progress = False
        else:
            self.frame_group_tools.pack_forget()
        self._redraw_hud_canvas()

    def _on_add_hud_group(self):
        dlg = tk.Toplevel(self)
        dlg.title("Tambah Group Baru")
        dlg.geometry("360x390")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        ttk.Label(dlg, text="Nama Group Baru:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        ent_name = ttk.Entry(dlg, font=("Segoe UI", 10))
        ent_name.pack(fill=tk.X, padx=14, pady=(0, 10))
        ent_name.focus_set()

        ttk.Label(dlg, text="Pilih Elemen Anggota Group:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(0, 6))

        elem_labels = [
            ("portrait", "Potret Karakter (portrait)"),
            ("nameplate", "Pelat Nama (nameplate)"),
            ("dialog_box", "Kotak Dialog Utama (dialog_box)"),
            ("speaker_text", "Teks Nama Luna/Karakter (speaker_text)"),
            ("dialog_text", "Isi Teks Dialog (dialog_text)"),
            ("counter_text", "Indikator Counter Halaman (counter_text)")
        ]
        elem_vars = {}
        chk_frame = ttk.Frame(dlg)
        chk_frame.pack(fill=tk.BOTH, expand=True, padx=14)

        current_elems = self.hud_cfg.get("elements", {})
        for key, lbl in elem_labels:
            if key in current_elems:
                var = tk.BooleanVar(value=True)
                elem_vars[key] = var
                ttk.Checkbutton(chk_frame, text=lbl, variable=var).pack(anchor="w", pady=3)

        btn_box = ttk.Frame(dlg)
        btn_box.pack(fill=tk.X, padx=14, pady=12)

        def save_group():
            name = ent_name.get().strip()
            if not name:
                messagebox.showerror("Error", "Nama group tidak boleh kosong!", parent=dlg)
                return
            chosen = [k for k, v in elem_vars.items() if v.get()]
            if not chosen:
                messagebox.showerror("Error", "Pilih minimal 1 elemen untuk group ini!", parent=dlg)
                return

            self._save_hud_snapshot()
            groups = self.hud_cfg.setdefault("groups", {})
            groups[name] = chosen
            save_hud_config(self.hud_cfg)
            self._refresh_group_combo()
            self.combo_hud_group.set(name)
            self._on_hud_group_selected()
            dlg.destroy()
            messagebox.showinfo("Berhasil", f"Group '{name}' berhasil dibuat!", parent=self)

        ttk.Button(btn_box, text="✓ Simpan Group", command=save_group).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_box, text="Batal", command=dlg.destroy).pack(side=tk.RIGHT, padx=4)

    def _on_delete_hud_group(self):
        cur = self.combo_hud_group.get()
        if cur == "[Tunggal / Single Element]":
            messagebox.showwarning("Peringatan", "Pilih group yang ingin dihapus terlebih dahulu.")
            return
        if messagebox.askyesno("Hapus Group", f"Hapus group '{cur}'?\n(Elemen di dalamnya tidak akan terhapus)"):
            self._save_hud_snapshot()
            groups = self.hud_cfg.setdefault("groups", {})
            if cur in groups:
                del groups[cur]
            save_hud_config(self.hud_cfg)
            self._refresh_group_combo()
            self.combo_hud_group.set("[Tunggal / Single Element]")
            self._on_hud_group_selected()

    def _on_group_slider_scale(self, val):
        if not hasattr(self, 'hud_cfg') or not hasattr(self, 'combo_hud_group'):
            return
        active_group = self.combo_hud_group.get()
        groups = self.hud_cfg.get("groups", {})
        group_elems = groups.get(active_group, [])
        if not group_elems:
            return

        scale_mult = float(val)
        if not self._group_scaling_in_progress or self._group_scale_snapshot is None:
            self._save_hud_snapshot()
            self._group_scale_snapshot = copy.deepcopy(self.hud_cfg.get("elements", {}))
            self._group_scaling_in_progress = True

        # Calculate center of group elements in the base snapshot
        xs = [self._group_scale_snapshot.get(k, {}).get("x", 0) for k in group_elems if k in self._group_scale_snapshot]
        ys = [self._group_scale_snapshot.get(k, {}).get("y", 0) for k in group_elems if k in self._group_scale_snapshot]
        if not xs or not ys:
            return
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)

        elems = self.hud_cfg.setdefault("elements", {})
        for k in group_elems:
            orig = self._group_scale_snapshot.get(k, {})
            orig_x = orig.get("x", 0)
            orig_y = orig.get("y", 0)
            orig_s = orig.get("scale", 1.0)

            target = elems.setdefault(k, {})
            target["x"] = int(round(cx + (orig_x - cx) * scale_mult))
            target["y"] = int(round(cy + (orig_y - cy) * scale_mult))
            target["scale"] = max(0.1, round(orig_s * scale_mult, 2))

        self._update_hud_editor_fields()
        self._redraw_hud_canvas()

    def _on_group_slider_release(self, event=None):
        self._group_scaling_in_progress = False
        self._group_scale_snapshot = None

    def _reset_group_scale(self):
        self.scale_group_slider.set(1.0)
        self._group_scaling_in_progress = False
        self._group_scale_snapshot = None

    def _nudge(self, dx, dy):
        self._save_hud_snapshot()
        active_group = self.combo_hud_group.get()
        groups = self.hud_cfg.get("groups", {})
        group_elems = groups.get(active_group, [])
        elems = self.hud_cfg.setdefault("elements", {})

        if active_group != "[Tunggal / Single Element]" and group_elems:
            for k in group_elems:
                target = elems.setdefault(k, {})
                target["x"] = target.get("x", 0) + dx
                target["y"] = target.get("y", 0) + dy
        else:
            cur = self.combo_hud_elem.get()
            if cur:
                target = elems.setdefault(cur, {})
                target["x"] = target.get("x", 0) + dx
                target["y"] = target.get("y", 0) + dy

        self._update_hud_editor_fields()
        self._redraw_hud_canvas()

    def _redraw_hud_canvas_debounced(self, delay_ms=16):
        if self._redraw_timer is not None:
            self.after_cancel(self._redraw_timer)
        self._redraw_timer = self.after(delay_ms, self._redraw_hud_canvas)

    def _on_canvas_resize(self, event):
        cw = max(10, event.width)
        ch = max(10, event.height)

        target_aspect = 16.0 / 9.0
        current_aspect = cw / ch

        if current_aspect > target_aspect:
            vh = ch
            vw = int(round(ch * target_aspect))
            ox = (cw - vw) // 2
            oy = 0
        else:
            vw = cw
            vh = int(round(cw / target_aspect))
            ox = 0
            oy = (ch - vh) // 2

        scale = vw / 480.0
        self.hud_view = {"scale": scale, "ox": ox, "oy": oy, "vw": vw, "vh": vh}
        self._redraw_hud_canvas_debounced(delay_ms=20)

    def _on_change_portrait_base(self):
        self._save_hud_snapshot()
        base = self.var_portrait_base.get()
        elems = self.hud_cfg.setdefault("elements", {})
        port = elems.setdefault("portrait", {})
        port["base_size"] = base
        if base == 128 and port.get("scale", 1.0) >= 1.0:
            port["scale"] = 0.5
        elif base == 64 and port.get("scale", 0.5) <= 0.5:
            port["scale"] = 1.0
        self._update_hud_editor_fields()
        self._redraw_hud_canvas()

    def _update_hud_editor_fields(self):
        cur = self.combo_hud_elem.get()
        elems = self.hud_cfg.setdefault("elements", {})
        custom_elems = self.hud_cfg.setdefault("custom_elements", {})
        for ck, cv in custom_elems.items():
            if ck not in elems:
                elems[ck] = {
                    "x": cv.get("x", 0),
                    "y": cv.get("y", 0),
                    "scale": cv.get("scale", 1.0),
                    "layer": cv.get("layer", 2)
                }
        if not cur or cur not in elems:
            self.spin_hud_x.delete(0, tk.END)
            self.spin_hud_y.delete(0, tk.END)
            self.spin_hud_scale.delete(0, tk.END)
            if hasattr(self, 'spin_hud_layer'):
                self.spin_hud_layer.delete(0, tk.END)
            self.frame_portrait_mode.pack_forget()
            self.frame_text_props.pack_forget()
            return
        elem_data = elems.get(cur, {"x": 0, "y": 0, "scale": 1.0})

        self.spin_hud_x.delete(0, tk.END)
        self.spin_hud_x.insert(0, str(elem_data.get("x", 0)))

        self.spin_hud_y.delete(0, tk.END)
        self.spin_hud_y.insert(0, str(elem_data.get("y", 0)))

        s = float(elem_data.get("scale", 1.0))
        self.spin_hud_scale.delete(0, tk.END)
        self.spin_hud_scale.insert(0, f"{s:.2f}")
        self.scale_slider.set(s)

        default_layers = {
            "bottom_cinematic_fade": 1,
            "dialog_box": 2,
            "portrait": 3,
            "nameplate": 4,
            "speaker_text": 5,
            "dialog_text": 5,
            "counter_text": 5
        }
        if hasattr(self, 'spin_hud_layer'):
            self.spin_hud_layer.delete(0, tk.END)
            self.spin_hud_layer.insert(0, str(elem_data.get("layer", default_layers.get(cur, 1))))

        if cur == "portrait":
            self.frame_portrait_mode.pack(fill=tk.X, pady=(0, 6))
            base = elem_data.get("base_size", 128)
            self.var_portrait_base.set(base)
        else:
            self.frame_portrait_mode.pack_forget()

        if "text" in cur:
            self.frame_text_props.pack(fill=tk.X, pady=(4, 6))
            spc = elem_data.get("space", 0)
            self.spin_hud_space.delete(0, tk.END)
            self.spin_hud_space.insert(0, str(spc))
            if hasattr(self, 'var_hud_shadow'):
                self.var_hud_shadow.set(bool(elem_data.get("outline", True)))
            if cur == "dialog_text":
                self.lbl_hud_split_w.pack(anchor="w", pady=(4, 0))
                self.spin_hud_split_w.pack(anchor="w", pady=2)
                self.slider_split_w.pack(fill=tk.X, pady=(0, 4))
                sw = elem_data.get("split_width", 202)
                self.spin_hud_split_w.delete(0, tk.END)
                self.spin_hud_split_w.insert(0, str(sw))
                self.slider_split_w.set(sw)
            else:
                self.lbl_hud_split_w.pack_forget()
                self.spin_hud_split_w.pack_forget()
                self.slider_split_w.pack_forget()
        else:
            self.frame_text_props.pack_forget()

    def _on_hud_elem_selected(self, event=None):
        self._update_hud_editor_fields()
        self._redraw_hud_canvas()

    def _on_slider_scale(self, val):
        try:
            s = float(val)
            self.spin_hud_scale.delete(0, tk.END)
            self.spin_hud_scale.insert(0, f"{s:.2f}")
            self._on_hud_val_change()
        except Exception:
            pass

    def _on_split_w_slider(self, val):
        try:
            w = int(round(float(val)))
            self.spin_hud_split_w.delete(0, tk.END)
            self.spin_hud_split_w.insert(0, str(w))
            self._on_hud_val_change()
        except Exception:
            pass

    def _on_scale_slider_release(self, event=None):
        save_hud_config(self.hud_cfg)
        try:
            from compiler import compile_portraits_and_betterhud
            compile_portraits_and_betterhud(self.characters)
        except Exception:
            pass

    def _on_hud_val_change(self):
        if not hasattr(self, 'hud_cfg') or not hasattr(self, 'combo_hud_elem'):
            return
        cur = self.combo_hud_elem.get()
        if not cur:
            return
        try:
            x = int(float(self.spin_hud_x.get()))
            y = int(float(self.spin_hud_y.get()))
            scale = float(self.spin_hud_scale.get())
        except ValueError:
            return

        elems = self.hud_cfg.setdefault("elements", {})
        target = elems.setdefault(cur, {})
        target["x"] = x
        target["y"] = y
        target["scale"] = round(scale, 2)
        if hasattr(self, 'spin_hud_layer'):
            try:
                target["layer"] = int(float(self.spin_hud_layer.get()))
            except Exception:
                pass
        if "text" in cur:
            try:
                target["space"] = int(self.spin_hud_space.get())
            except Exception:
                pass
            if hasattr(self, 'var_hud_shadow'):
                target["outline"] = bool(self.var_hud_shadow.get())
            if cur == "dialog_text":
                try:
                    target["split_width"] = int(self.spin_hud_split_w.get())
                except Exception:
                    pass

        # Sync to custom_elements if applicable
        if "custom_elements" in self.hud_cfg and cur in self.hud_cfg["custom_elements"]:
            c_elem = self.hud_cfg["custom_elements"][cur]
            c_elem["x"] = x
            c_elem["y"] = y
            c_elem["scale"] = round(scale, 2)
            if "layer" in target:
                c_elem["layer"] = target["layer"]

        save_hud_config(self.hud_cfg)
        self._redraw_hud_canvas()

    def _on_hud_canvas_motion(self, event):
        # 1. Check hover over Canva handles
        for h_key, (hx, hy, r) in self._hud_handles.items():
            if abs(event.x - hx) <= r and abs(event.y - hy) <= r:
                if h_key == "handle_split_w":
                    self.hud_canvas.config(cursor="sb_h_double_arrow")
                    return
                elif h_key == "handle_scale":
                    self.hud_canvas.config(cursor="bottom_right_corner")
                    return

        # 2. Check hover over HUD elements
        for key, (cx, cy, w, h) in self._hud_canvas_items.items():
            if cx <= event.x <= cx + w and cy <= event.y <= cy + h:
                self.hud_canvas.config(cursor="fleur")
                return

        self.hud_canvas.config(cursor="")

    def _get_cached_photo(self, file_path, target_w, target_h):
        if not file_path or not os.path.exists(file_path):
            return None
        try:
            mtime = os.path.getmtime(file_path)
            cache_key = (file_path, target_w, target_h, mtime)
            if cache_key in self._texture_ram_cache:
                return self._texture_ram_cache[cache_key]

            with Image.open(file_path) as orig_img:
                conv = orig_img.convert("RGBA")
                res = conv.resize((target_w, target_h), Image.Resampling.NEAREST)
                photo = ImageTk.PhotoImage(res)
                self._texture_ram_cache[cache_key] = photo
                # Limit cache size to avoid unbounded RAM growth
                if len(self._texture_ram_cache) > 120:
                    self._texture_ram_cache.pop(next(iter(self._texture_ram_cache)))
                return photo
        except Exception:
            return None

    def _redraw_hud_canvas(self):
        self.hud_canvas.delete("all")
        self._hud_canvas_items = {}
        self._hud_handles = {}

        view = self.hud_view
        ox = view["ox"]
        oy = view["oy"]
        vw = view["vw"]
        vh = view["vh"]
        sc = view["scale"]

        # 16:9 Screen background & letterbox border
        self.hud_canvas.create_rectangle(ox, oy, ox + vw, oy + vh, fill="#1e1f29", outline="#3e4055", width=2)

        # Minecraft crosshair in center of 16:9 screen
        mid_x = ox + vw // 2
        mid_y = oy + vh // 2
        self.hud_canvas.create_line(mid_x - int(6 * sc), mid_y, mid_x + int(6 * sc), mid_y, fill="#888899", width=1)
        self.hud_canvas.create_line(mid_x, mid_y - int(6 * sc), mid_x, mid_y + int(6 * sc), fill="#888899", width=1)

        # Minecraft Standard Hotbar: width = 182, height = 22, centered at bottom
        hb_w = int(182 * sc)
        hb_h = int(22 * sc)
        hb_x = mid_x - hb_w // 2
        hb_y = oy + vh - hb_h

        # Draw Hotbar outline and slots
        self.hud_canvas.create_rectangle(hb_x, hb_y, hb_x + hb_w, hb_y + hb_h, fill="#181920", outline="#555566", width=1)
        slot_w = hb_w / 9.0
        for i in range(1, 9):
            sx = hb_x + int(i * slot_w)
            self.hud_canvas.create_line(sx, hb_y, sx, hb_y + hb_h, fill="#2f303d", width=1)
        self.hud_canvas.create_text(mid_x, hb_y + hb_h // 2, text="[ Hotbar Minecraft ]", fill="#777788", font=("Segoe UI", max(7, int(8 * sc))))

        # Minecraft screen center guideline (vertical guide)
        self.hud_canvas.create_line(mid_x, oy, mid_x, hb_y, fill="#2a3545", width=1, dash=(2, 4))

        elems = self.hud_cfg.get("elements", {})
        dlg_box_scale = elems.get("dialog_box", {}).get("scale", 1.0)
        box_path = self._get_dialog_box_texture_path()
        box_w = 255
        if box_path and os.path.exists(box_path):
            try:
                with Image.open(box_path) as tmp_img:
                    p_box = tmp_img.getbbox()
                    box_w = (p_box[2] - p_box[0]) if p_box else tmp_img.size[0]
            except Exception:
                pass
        base_origin_x = mid_x - int((box_w // 2) * dlg_box_scale * sc)
        base_origin_y = oy + vh - int(88 * sc)

        active_group = self.combo_hud_group.get()
        group_elems = self.hud_cfg.get("groups", {}).get(active_group, [])
        is_group_mode = (active_group != "[Tunggal / Single Element]" and bool(group_elems))

        default_layers = {
            "bottom_cinematic_fade": 1,
            "dialog_box": 2,
            "portrait": 3,
            "nameplate": 4,
            "speaker_text": 5,
            "dialog_text": 5,
            "counter_text": 5
        }
        all_keys = [k for k in ["bottom_cinematic_fade", "portrait", "dialog_box", "nameplate", "speaker_text", "dialog_text", "counter_text"] if k in elems]
        for k in elems.keys():
            if k not in all_keys:
                all_keys.append(k)
        order = sorted(all_keys, key=lambda k: (int(elems.get(k, {}).get("layer", default_layers.get(k, 1))), default_layers.get(k, 1)))
        selected = self.combo_hud_elem.get()

        for key in order:
            if key not in elems:
                continue
            ed = elems.get(key, {})
            x = ed.get("x", 0)
            y = ed.get("y", 0)
            elem_scale = ed.get("scale", 1.0)

            cx = base_origin_x + int(x * sc)
            cy = base_origin_y + int(y * sc)

            in_group = (is_group_mode and key in group_elems)
            is_sel = (key == selected and not is_group_mode) or (is_group_mode and in_group)
            
            outline_color = "#00FFDD" if in_group else ("#FFFF44" if is_sel else "#666677")
            dash_pattern = () if (is_sel or in_group) else (3, 3)
            border_width = 2 if (is_sel or in_group) else 1

            if key == "portrait":
                base_s = ed.get("base_size", 128)
                pw = max(1, int(base_s * elem_scale * sc))
                ph = max(1, int(base_s * elem_scale * sc))

                drawn_portrait = False
                port_path = self._get_current_sample_portrait_path()

                crop_x, crop_y, crop_w, crop_h = 0, 0, base_s, base_s
                if port_path and os.path.exists(port_path):
                    try:
                        with Image.open(port_path) as tmp_p:
                            p_box = tmp_p.getbbox()
                            if p_box:
                                crop_x, crop_y = p_box[0], p_box[1]
                                crop_w, crop_h = p_box[2] - p_box[0], p_box[3] - p_box[1]
                    except Exception:
                        pass

                if port_path and self.var_show_textures.get():
                    tk_port = self._get_cached_photo(port_path, pw, ph)
                    if tk_port:
                        self._hud_image_refs["portrait"] = tk_port
                        self.hud_canvas.create_image(cx, cy, anchor="nw", image=tk_port, tags=(key,))
                        drawn_portrait = True

                sel_x = cx + int(crop_x * elem_scale * sc)
                sel_y = cy + int(crop_y * elem_scale * sc)
                sel_w = max(1, int(crop_w * elem_scale * sc))
                sel_h = max(1, int(crop_h * elem_scale * sc))

                if not drawn_portrait:
                    self.hud_canvas.create_rectangle(sel_x, sel_y, sel_x + sel_w, sel_y + sel_h, fill="#3b2b40", outline="", tags=(key,))
                    self.hud_canvas.create_text(sel_x + sel_w // 2, sel_y + sel_h // 2, text=f"Potret {int(base_s*elem_scale)}px", fill="#eeddff", font=("Segoe UI", max(7, int(9 * sc)), "bold"), tags=(key,))

                # Selection / Group outline
                self.hud_canvas.create_rectangle(sel_x, sel_y, sel_x + sel_w, sel_y + sel_h, fill="", outline=outline_color, width=border_width, dash=dash_pattern, tags=(key,))
                self._hud_canvas_items[key] = (sel_x, sel_y, sel_w, sel_h)

            elif key == "dialog_box":
                drawn_box = False
                box_path = self._get_dialog_box_texture_path()
                box_w = 255
                box_h = 61
                if box_path and os.path.exists(box_path):
                    try:
                        with Image.open(box_path) as tmp_img:
                            box_w, box_h = tmp_img.size
                    except Exception:
                        pass
                bw = max(1, int(box_w * elem_scale * sc))
                bh = max(1, int(box_h * elem_scale * sc))

                if box_path and os.path.exists(box_path) and self.var_show_textures.get():
                    tk_box = self._get_cached_photo(box_path, bw, bh)
                    if tk_box:
                        self._hud_image_refs["dialog_box"] = tk_box
                        self.hud_canvas.create_image(cx, cy, anchor="nw", image=tk_box, tags=(key,))
                        drawn_box = True

                if not drawn_box:
                    self.hud_canvas.create_rectangle(cx, cy, cx + bw, cy + bh, fill="#1e2029", outline="", tags=(key,))
                    self.hud_canvas.create_text(cx + bw // 2, cy + bh // 2, text="Kotak Dialog Utama", fill="#aaccff", font=("Minecraft", -max(7, int(9 * sc))), tags=(key,))

                self.hud_canvas.create_rectangle(cx, cy, cx + bw, cy + bh, fill="", outline=outline_color, width=border_width, dash=dash_pattern, tags=(key,))
                self._hud_canvas_items[key] = (cx, cy, bw, bh)

            elif key == "nameplate":
                drawn_np = False
                np_path = self._get_nameplate_texture_path()
                np_w = 98
                np_h = 23
                if np_path and os.path.exists(np_path):
                    try:
                        with Image.open(np_path) as tmp_img:
                            np_w, np_h = tmp_img.size
                    except Exception:
                        pass
                nw = max(1, int(np_w * elem_scale * sc))
                nh = max(1, int(np_h * elem_scale * sc))

                if np_path and os.path.exists(np_path) and self.var_show_textures.get():
                    tk_np = self._get_cached_photo(np_path, nw, nh)
                    if tk_np:
                        self._hud_image_refs["nameplate"] = tk_np
                        self.hud_canvas.create_image(cx, cy, anchor="nw", image=tk_np, tags=(key,))
                        drawn_np = True

                if not drawn_np:
                    self.hud_canvas.create_rectangle(cx, cy, cx + nw, cy + nh, fill="#3a2520", outline="", tags=(key,))
                    self.hud_canvas.create_text(cx + nw // 2, cy + nh // 2, text="Nama", fill="#ffddbb", font=("Minecraft", -max(6, int(8 * sc)), "bold"), tags=(key,))

                self.hud_canvas.create_rectangle(cx, cy, cx + nw, cy + nh, fill="", outline=outline_color, width=border_width, dash=dash_pattern, tags=(key,))
                self._hud_canvas_items[key] = (cx, cy, nw, nh)

            elif key == "speaker_text":
                char_id = self.combo_sample_char.get() if hasattr(self, 'combo_sample_char') else ""
                speaker_name = self.characters.get(char_id, {}).get("speaker_name", "Luna") if char_id else "Luna"
                spk_rel = elem_scale / 0.50
                spk_px = max(7, int(round(8.0 * spk_rel * sc)))
                spk_font = ("Minecraft", -spk_px)
                sh_off = max(1, int(round(1.0 * sc)))
                has_shadow = ed.get("outline", True)
                if has_shadow:
                    self.hud_canvas.create_text(cx + sh_off, cy + sh_off, text=speaker_name, anchor="nw", fill="#3f3f3f", font=spk_font, tags=(key,))
                self.hud_canvas.create_text(cx, cy, text=speaker_name, anchor="nw", fill="#FFFFFF", font=spk_font, tags=(key,))
                spk_w = max(20, int(round(len(speaker_name) * 6 * spk_rel * sc)))
                self._hud_canvas_items[key] = (cx, cy, spk_w, max(8, int(round(10 * spk_rel * sc))))

            elif key == "dialog_text":
                sample_txt = self.entry_test_dialog.get() if hasattr(self, 'entry_test_dialog') and self.entry_test_dialog.get() else (self._preview_dialog_text or "Tapi tempat ini menyimpan hawa janggal... Tanah di sekitar sumur seolah berbisik memanggil nama asing.")
                sw = ed.get("split_width", 202)
                line_w_cfg = ed.get("line_width", 9)
                rel_scale = elem_scale / 0.50
                font_sz = max(7, int(round(8.0 * rel_scale * sc)))
                dlg_font = ("Minecraft", -font_sz)
                sh_off = max(1, int(round(1.0 * sc)))
                line_spacing = max(8, int(round(line_w_cfg * rel_scale * sc)))

                # Split exactly matching BetterHUD's split algorithm and character advances
                dlg_lines = split_dialogue_lines(sample_txt, sw, scale=elem_scale)
                max_line_w_unscaled = max((lw for _, lw in dlg_lines), default=sw)
                rendered_w_px = max(20, int(round(max_line_w_unscaled * rel_scale * sc)))
                total_th = max(line_spacing, len(dlg_lines) * line_spacing)

                has_shadow = ed.get("outline", True)
                # Render each line with Minecraft drop-shadow
                for l_idx, (line_str, line_w) in enumerate(dlg_lines):
                    line_y = cy + l_idx * line_spacing
                    if has_shadow:
                        self.hud_canvas.create_text(
                            cx + sh_off, line_y + sh_off,
                            text=line_str,
                            anchor="nw",
                            fill="#303030",
                            font=dlg_font,
                            tags=(key,)
                        )
                    self.hud_canvas.create_text(
                        cx, line_y,
                        text=line_str,
                        anchor="nw",
                        fill="#F0F0F0",
                        font=dlg_font,
                        tags=(key,)
                    )

                wrap_px = max(20, int(round(sw * rel_scale * sc)))
                self._hud_canvas_items[key] = (cx, cy, max(wrap_px, rendered_w_px), total_th)

                # Safe area right-border boundary overflow check (dialogue box right inner margin)
                box_elem = elems.get("dialog_box", {})
                box_scale = box_elem.get("scale", 1.0)
                box_x_px = base_origin_x + int(box_elem.get("x", 75) * sc)
                box_w_px = int(box_w * box_scale * sc)
                box_right_safe = box_x_px + box_w_px + int(2 * sc)

                text_right_px = cx + rendered_w_px
                if text_right_px > box_right_safe:
                    # Render warning alert tag over canvas
                    ov_w = int((text_right_px - (box_x_px + box_w_px)) / max(0.01, rel_scale * sc))
                    self.hud_canvas.create_rectangle(
                        box_right_safe - 2, cy - 4, text_right_px + 4, cy + total_th + 4,
                        fill="", outline="#FF3344", width=2, dash=(2, 2), tags=("overflow_warning",)
                    )
                    self.hud_canvas.create_text(
                        box_right_safe, cy - 8,
                        text=f"⚠️ OVERFLOW +{ov_w}px! Turunkan split_width",
                        anchor="sw",
                        fill="#FF3344",
                        font=("Segoe UI", max(8, int(9 * sc)), "bold"),
                        tags=("overflow_warning",)
                    )

                # Canva-style visual resize handles when selected
                if is_sel and not is_group_mode:
                    pad = 3
                    self.hud_canvas.create_rectangle(
                        cx - pad, cy - pad, cx + wrap_px + pad, cy + total_th + pad,
                        outline="#00E5FF", width=1.5, dash=(4, 2), tags=("text_guide",)
                    )
                    # Right Split-Width Handle (↔)
                    hw_x = cx + wrap_px + pad
                    hw_y = cy + total_th // 2
                    h_sz = max(4, int(4 * sc))
                    self.hud_canvas.create_rectangle(
                        hw_x - h_sz, hw_y - h_sz, hw_x + h_sz, hw_y + h_sz,
                        fill="#00FFFF", outline="#FFFFFF", width=1.5, tags=("handle_split_w",)
                    )
                    self._hud_handles["handle_split_w"] = (hw_x, hw_y, h_sz + 4)

                    # Bottom-Right Scale Handle (diagonal scale)
                    hs_x = cx + wrap_px + pad
                    hs_y = cy + total_th + pad
                    self.hud_canvas.create_oval(
                        hs_x - h_sz - 1, hs_y - h_sz - 1, hs_x + h_sz + 1, hs_y + h_sz + 1,
                        fill="#FFD700", outline="#FFFFFF", width=1.5, tags=("handle_scale",)
                    )
                    self._hud_handles["handle_scale"] = (hs_x, hs_y, h_sz + 4)

                    # Split width pill badge
                    self.hud_canvas.create_text(
                        hw_x + 10, hw_y,
                        text=f"↔ {sw}px ({len(dlg_lines)} baris)",
                        anchor="w",
                        fill="#00FFFF",
                        font=("Segoe UI", max(7, int(8 * sc)), "bold"),
                        tags=("handle_badge",)
                    )

            elif key == "counter_text":
                cnt_rel = elem_scale / 0.50
                cnt_px = max(6, int(round(8.0 * cnt_rel * sc)))
                cnt_font = ("Minecraft", -cnt_px)
                sh_off = max(1, int(round(1.0 * sc)))
                self.hud_canvas.create_text(cx + sh_off, cy + sh_off, text="1/5 ▶ ≡", anchor="ne", fill="#3f3f15", font=cnt_font, tags=(key,))
                self.hud_canvas.create_text(cx, cy, text="1/5 ▶ ≡", anchor="ne", fill="#FFFF55", font=cnt_font, tags=(key,))
                cnt_w = max(20, int(round(35 * cnt_rel * sc)))
                self._hud_canvas_items[key] = (cx - cnt_w, cy, cnt_w, max(8, int(round(10 * cnt_rel * sc))))

            else:
                # Custom HUD Element (Image or Text)
                c_data = self.hud_cfg.get("custom_elements", {}).get(key, {})
                c_type = c_data.get("type", "image")
                if c_type == "image":
                    c_file = c_data.get("file", f"{key}.png")
                    c_path = resolve_asset_path(c_file)
                    font_dir = get_font_textures_dir()
                    if not c_path or not os.path.exists(c_path):
                        c_path = os.path.join(font_dir, c_file)
                    img_w, img_h = 32, 32
                    if c_path and os.path.exists(c_path):
                        try:
                            with Image.open(c_path) as tmp_im:
                                img_w, img_h = tmp_im.size
                        except Exception:
                            pass
                    rw = max(1, int(img_w * elem_scale * sc))
                    rh = max(1, int(img_h * elem_scale * sc))
                    if "fade" in key.lower():
                        # BetterHUD compiles fade into independent vn_fade_layout with offset: center (pivot = mid_x - rw // 2)
                        cx = (mid_x - rw // 2) + int(x * sc)
                    drawn_custom = False
                    if c_path and os.path.exists(c_path) and self.var_show_textures.get():
                        tk_c = self._get_cached_photo(c_path, rw, rh)
                        if tk_c:
                            self._hud_image_refs[key] = tk_c
                            self.hud_canvas.create_image(cx, cy, anchor="nw", image=tk_c, tags=(key,))
                            drawn_custom = True
                    if not drawn_custom:
                        self.hud_canvas.create_rectangle(cx, cy, cx + rw, cy + rh, fill="#1c2833", outline="#2e4053", tags=(key,))
                        self.hud_canvas.create_text(cx + rw // 2, cy + rh // 2, text=key, fill="#5dade2", font=("Segoe UI", max(7, int(8 * sc)), "bold"), tags=(key,))
                    self.hud_canvas.create_rectangle(cx, cy, cx + rw, cy + rh, fill="", outline=outline_color, width=border_width, dash=dash_pattern, tags=(key,))
                    self._hud_canvas_items[key] = (cx, cy, rw, rh)
                else:
                    c_pat = c_data.get("pattern", key)
                    c_font_sz = max(7, int(round(8.0 * (elem_scale / 0.50) * sc)))
                    self.hud_canvas.create_text(cx, cy, text=c_pat, anchor="nw", fill="#FFFFFF", font=("Segoe UI", c_font_sz, "bold"), tags=(key,))
                    tw = max(24, int(len(c_pat) * 7 * elem_scale * sc))
                    th = max(12, int(14 * elem_scale * sc))
                    self.hud_canvas.create_rectangle(cx, cy, cx + tw, cy + th, fill="", outline=outline_color, width=border_width, dash=dash_pattern, tags=(key,))
                    self._hud_canvas_items[key] = (cx, cy, tw, th)

        # Draw Group Bounding Box if group mode active
        if is_group_mode and group_elems:
            min_gx = 999999
            min_gy = 999999
            max_gx = -999999
            max_gy = -999999
            for k in group_elems:
                if k in self._hud_canvas_items:
                    ix, iy, iw, ih = self._hud_canvas_items[k]
                    min_gx = min(min_gx, ix)
                    min_gy = min(min_gy, iy)
                    max_gx = max(max_gx, ix + iw)
                    max_gy = max(max_gy, iy + ih)

            if min_gx < max_gx and min_gy < max_gy:
                pad = int(5 * sc)
                self.hud_canvas.create_rectangle(
                    min_gx - pad, min_gy - pad, max_gx + pad, max_gy + pad,
                    outline="#00E5FF", width=2, dash=(6, 3)
                )
                self.hud_canvas.create_text(
                    min_gx - pad, min_gy - pad - int(12 * sc),
                    text=f"📦 Group: {active_group}",
                    anchor="sw",
                    fill="#00FFFF",
                    font=("Segoe UI", max(7, int(9 * sc)), "bold")
                )

    def _on_hud_canvas_click(self, event):
        self.hud_canvas.focus_set()

        # 1. Check if clicked on a Canva handle
        for h_key, (hx, hy, r) in self._hud_handles.items():
            if abs(event.x - hx) <= r and abs(event.y - hy) <= r:
                elems = self.hud_cfg.get("elements", {})
                d_elem = elems.get("dialog_text", {})
                if h_key == "handle_split_w":
                    self._active_handle = "split_width"
                    self._handle_start = (event.x, event.y, d_elem.get("split_width", 202))
                    return
                elif h_key == "handle_scale":
                    self._active_handle = "scale"
                    self._handle_start = (event.x, event.y, d_elem.get("scale", 0.50))
                    return

        self._active_handle = None

        # 2. Check if clicked on elements
        clicked_key = None
        elems = self.hud_cfg.get("elements", {})
        default_layers = {
            "bottom_cinematic_fade": 1,
            "dialog_box": 2,
            "portrait": 3,
            "nameplate": 4,
            "speaker_text": 5,
            "dialog_text": 5,
            "counter_text": 5
        }
        all_keys = [k for k in ["bottom_cinematic_fade", "portrait", "dialog_box", "nameplate", "speaker_text", "dialog_text", "counter_text"] if k in elems]
        for k in elems.keys():
            if k not in all_keys:
                all_keys.append(k)
        click_order = sorted(all_keys, key=lambda k: (int(elems.get(k, {}).get("layer", default_layers.get(k, 1))), default_layers.get(k, 1)))
        for key in reversed(click_order):
            if key in elems and key in self._hud_canvas_items:
                cx, cy, w, h = self._hud_canvas_items[key]
                if cx <= event.x <= cx + w and cy <= event.y <= cy + h:
                    clicked_key = key
                    break

        active_group = self.combo_hud_group.get()
        group_elems = self.hud_cfg.get("groups", {}).get(active_group, [])

        if active_group != "[Tunggal / Single Element]" and group_elems:
            if clicked_key and clicked_key not in group_elems:
                # Switch to clicked element in single mode
                self.combo_hud_group.set("[Tunggal / Single Element]")
                self._on_hud_group_selected()
                self.combo_hud_elem.set(clicked_key)
                self._update_hud_editor_fields()
                self._hud_drag_data = {
                    "is_group": False,
                    "elem_key": clicked_key,
                    "x": event.x,
                    "y": event.y,
                    "has_moved": False
                }
            else:
                # Group drag mode
                if clicked_key:
                    self.combo_hud_elem.set(clicked_key)
                    self._update_hud_editor_fields()
                self._hud_drag_data = {
                    "is_group": True,
                    "group_name": active_group,
                    "elem_keys": list(group_elems),
                    "x": event.x,
                    "y": event.y,
                    "has_moved": False
                }
        elif clicked_key:
            self.combo_hud_elem.set(clicked_key)
            self._update_hud_editor_fields()
            self._hud_drag_data = {
                "is_group": False,
                "elem_key": clicked_key,
                "x": event.x,
                "y": event.y,
                "has_moved": False
            }

        self._redraw_hud_canvas()

    def _on_hud_canvas_drag(self, event):
        sc = self.hud_view.get("scale", 1.0)
        if sc <= 0.01:
            return

        # Handle active Canva handle drag
        if self._active_handle:
            if not self._hud_drag_data.get("has_moved", False):
                self._save_hud_snapshot()
                self._hud_drag_data["has_moved"] = True

            elems = self.hud_cfg.setdefault("elements", {})
            d_elem = elems.setdefault("dialog_text", {})
            elem_scale = d_elem.get("scale", 0.50)

            if self._active_handle == "split_width":
                start_x, start_y, start_sw = self._handle_start
                rel_scale = elem_scale / 0.50
                dx = (event.x - start_x) / max(0.01, rel_scale * sc)
                new_sw = max(40, min(320, int(round(start_sw + dx))))
                d_elem["split_width"] = new_sw
                self.spin_hud_split_w.delete(0, tk.END)
                self.spin_hud_split_w.insert(0, str(new_sw))
                self.slider_split_w.set(new_sw)
                self._redraw_hud_canvas()
                return
            elif self._active_handle == "scale":
                start_x, start_y, start_scale = self._handle_start
                dx = (event.x - start_x) / (100.0 * sc)
                new_scale = max(0.15, min(2.5, round(start_scale + dx, 2)))
                d_elem["scale"] = new_scale
                self.spin_hud_scale.delete(0, tk.END)
                self.spin_hud_scale.insert(0, f"{new_scale:.2f}")
                self.scale_slider.set(new_scale)
                self._redraw_hud_canvas()
                return

        # Normal element / group drag
        if not self._hud_drag_data.get("elem_key") and not self._hud_drag_data.get("is_group"):
            return

        if not self._hud_drag_data.get("has_moved", False):
            self._save_hud_snapshot()
            self._hud_drag_data["has_moved"] = True

        dx = (event.x - self._hud_drag_data["x"]) / sc
        dy = (event.y - self._hud_drag_data["y"]) / sc

        elems = self.hud_cfg.setdefault("elements", {})
        if self._hud_drag_data.get("is_group"):
            for k in self._hud_drag_data.get("elem_keys", []):
                target = elems.setdefault(k, {})
                target["x"] = int(round(target.get("x", 0) + dx))
                target["y"] = int(round(target.get("y", 0) + dy))
        else:
            k = self._hud_drag_data.get("elem_key")
            if k:
                target = elems.setdefault(k, {})
                target["x"] = int(round(target.get("x", 0) + dx))
                target["y"] = int(round(target.get("y", 0) + dy))

        self._hud_drag_data["x"] = event.x
        self._hud_drag_data["y"] = event.y

        self._update_hud_editor_fields()
        self._redraw_hud_canvas()

    def _on_hud_canvas_release(self, event):
        self._active_handle = None
        if self._hud_drag_data.get("has_moved"):
            elems = self.hud_cfg.get("elements", {})
            custom_elems = self.hud_cfg.get("custom_elements", {})
            for k, ed in elems.items():
                if k in custom_elems:
                    custom_elems[k]["x"] = ed.get("x", 0)
                    custom_elems[k]["y"] = ed.get("y", 0)
                    custom_elems[k]["scale"] = ed.get("scale", 1.0)
                    if "layer" in ed:
                        custom_elems[k]["layer"] = ed["layer"]
            save_hud_config(self.hud_cfg)
            try:
                from compiler import compile_portraits_and_betterhud
                compile_portraits_and_betterhud(self.characters)
            except Exception:
                pass
        self._hud_drag_data = {"item": None, "x": 0, "y": 0, "elem_key": None, "is_group": False}

    def _on_save_hud_config(self):
        save_hud_config(self.hud_cfg)
        messagebox.showinfo("Tersimpan", "Konfigurasi layout HUD visual berhasil disimpan ke data/hud_config.yml!")

    def _on_save_and_compile_hud(self):
        save_hud_config(self.hud_cfg)
        self._on_compile_all()
        count, msg = sync_client_pack()
        messagebox.showinfo("Selesai", f"HUD Layout berhasil disimpan & di-compile!\nResource pack client diperbarui ({count} file).\n\nJalankan command berikut di Minecraft:\n/vn reload\n(atau tekan F3 + T jika mengubah tekstur)")

    def _on_reset_hud_config(self):
        if messagebox.askyesno("Reset", "Reset posisi dan ukuran layout ke settingan default?"):
            self._save_hud_snapshot()
            default_groups = {
                "Semua Elemen (All)": ["portrait", "nameplate", "dialog_box", "speaker_text", "dialog_text"],
                "Kotak Dialog & Teks": ["dialog_box", "dialog_text"],
                "Potret & Nama": ["portrait", "nameplate", "speaker_text"],
                "Semua Teks": ["speaker_text", "dialog_text"]
            }
            self.hud_cfg = {
                "elements": {
                    "dialog_box": {"x": 75, "y": -4, "scale": 1.0, "layer": 1},
                    "portrait": {"x": -12, "y": -58, "scale": 0.78, "base_size": 128, "layer": 2},
                    "nameplate": {"x": 4, "y": 34, "scale": 1.0, "layer": 3},
                    "speaker_text": {"x": 11, "y": 40, "scale": 0.58, "color": "<#FFFFFF>", "space": 0, "layer": 4},
                    "dialog_text": {"x": 80, "y": 1, "scale": 0.46, "color": "<#F0F0F0>", "line": 4, "split_width": 222, "line_width": 9, "space": 0, "layer": 4}
                },
                "groups": default_groups,
                "textures": {
                    "dialog_box": "dialogue_box.png",
                    "nameplate": "nameplate.png"
                }
            }
            save_hud_config(self.hud_cfg)
            self._refresh_hud_elements_combo()
            self._refresh_group_combo()
            self._refresh_hud_textures()
            self._update_hud_editor_fields()
            self._redraw_hud_canvas()

    # =========================================================================
    # TAB 4: ASSETS & DIRECTORIES CONFIGURATION
    # =========================================================================
    def _build_assets_tab(self):
        pane = ttk.PanedWindow(self.tab_assets, orient=tk.VERTICAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 1. Workflow & Texture Guide Frame
        guide_frame = ttk.LabelFrame(pane, text="📖 Panduan Format & Alur Kerja Tekstur UI", padding=10)
        pane.add(guide_frame, weight=0)

        guide_cols = ttk.Frame(guide_frame)
        guide_cols.pack(fill=tk.X)

        # Left Column: Standard Dimensions & Format
        col1 = ttk.Frame(guide_cols)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        ttk.Label(col1, text="Standar Resolusi Minecraft BetterHUD:", font=("Segoe UI", 9, "bold"), foreground="#38bdf8").pack(anchor="w", pady=(0, 4))
        c1_text = (
            "• dialogue_box.png : 250×54 px (9-slice: 5px ujung kiri/kanan, 240px tengah diulang).\n"
            "• nameplate.png    : 72×18 px (frame nama pembicara NPC).\n"
            "• Format File      : PNG 32-bit RGBA transparan."
        )
        ttk.Label(col1, text=c1_text, justify=tk.LEFT, foreground="#cbd5e1").pack(anchor="w")

        # Right Column: Direct Editing Workflow
        col2 = ttk.Frame(guide_cols)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        ttk.Label(col2, text="Alur Kerja & Akses Langsung:", font=("Segoe UI", 9, "bold"), foreground="#38bdf8").pack(anchor="w", pady=(0, 4))
        c2_text = (
            "1. Klik tombol '📂 Edit File' pada kartu aset untuk langsung membuka di Photoshop / Aseprite / Paint.\n"
            "2. Klik '📁 Explorer' untuk membuka lokasi file langsung di File Explorer Windows.\n"
            "3. Setelah simpan perubahan gambar, klik '🔄 Refresh Galeri' untuk sinkronisasi seketika.\n"
            "4. Cek hasil visual di tab 'Visual HUD Designer' dan jalankan '/vn reload' di Minecraft."
        )
        ttk.Label(col2, text=c2_text, justify=tk.LEFT, foreground="#cbd5e1").pack(anchor="w")

        # 2. Directory Settings Frame
        dir_frame = ttk.LabelFrame(pane, text="Pengaturan Direktori Workspace & Game", padding=10)
        pane.add(dir_frame, weight=0)

        grid_f = ttk.Frame(dir_frame)
        grid_f.pack(fill=tk.X, pady=2)

        # Minecraft Client Pack Folder
        ttk.Label(grid_f, text="Minecraft Client Pack:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_cfg_client_pack = ttk.Entry(grid_f, font=("Segoe UI", 9))
        self.entry_cfg_client_pack.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(grid_f, text="Pilih Folder...", command=lambda: self._browse_dir(self.entry_cfg_client_pack)).grid(row=0, column=2, padx=2, pady=4)
        ttk.Button(grid_f, text="📂 Buka Folder", command=lambda: self._open_dir(self.entry_cfg_client_pack.get())).grid(row=0, column=3, padx=2, pady=4)

        # Server Root / Plugins Folder
        ttk.Label(grid_f, text="Server Plugins / Root:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_cfg_server = ttk.Entry(grid_f, font=("Segoe UI", 9))
        self.entry_cfg_server.grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(grid_f, text="Pilih Folder...", command=lambda: self._browse_dir(self.entry_cfg_server)).grid(row=1, column=2, padx=2, pady=4)
        ttk.Button(grid_f, text="📂 Buka Folder", command=lambda: self._open_dir(self.entry_cfg_server.get())).grid(row=1, column=3, padx=2, pady=4)

        # Font Textures UI Folder
        ttk.Label(grid_f, text="Font Textures UI:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_cfg_font_dir = ttk.Entry(grid_f, font=("Segoe UI", 9))
        self.entry_cfg_font_dir.grid(row=2, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(grid_f, text="Pilih Folder...", command=lambda: self._browse_dir(self.entry_cfg_font_dir)).grid(row=2, column=2, padx=2, pady=4)
        ttk.Button(grid_f, text="📂 Buka Folder", command=lambda: self._open_dir(self.entry_cfg_font_dir.get())).grid(row=2, column=3, padx=2, pady=4)

        grid_f.columnconfigure(1, weight=1)

        btn_bar = ttk.Frame(dir_frame)
        btn_bar.pack(fill=tk.X, pady=(6, 2))
        ttk.Button(btn_bar, text="💾 Simpan Pengaturan Direktori", style="Primary.TButton", command=self._save_studio_paths).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="↺ Reset Direktori Default", command=self._reset_studio_paths).pack(side=tk.LEFT, padx=4)

        # 3. Dedicated Active UI Textures Control Bar
        active_tex_frame = ttk.LabelFrame(pane, text="Pengaturan Tekstur Kotak & Nameplate Aktif", padding=8)
        pane.add(active_tex_frame, weight=0)

        at_row = ttk.Frame(active_tex_frame)
        at_row.pack(fill=tk.X)

        ttk.Label(at_row, text="Dialog Box Aktif:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(2, 4))
        self.combo_asset_box_tex = ttk.Combobox(at_row, state="readonly", width=22)
        self.combo_asset_box_tex.pack(side=tk.LEFT, padx=(0, 14))
        self.combo_asset_box_tex.bind("<<ComboboxSelected>>", self._on_asset_tab_texture_selected)

        ttk.Label(at_row, text="Nameplate Aktif:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(4, 4))
        self.combo_asset_np_tex = ttk.Combobox(at_row, state="readonly", width=22)
        self.combo_asset_np_tex.pack(side=tk.LEFT, padx=(0, 14))
        self.combo_asset_np_tex.bind("<<ComboboxSelected>>", self._on_asset_tab_texture_selected)

        ttk.Button(at_row, text="✓ Terapkan Tekstur Aktif", style="Primary.TButton", command=self._apply_active_textures_from_tab).pack(side=tk.LEFT, padx=4)

        # 4. Asset Gallery Frame
        gallery_frame = ttk.LabelFrame(pane, text="Galeri Aset Tekstur UI & Font", padding=8)
        pane.add(gallery_frame, weight=3)

        g_top = ttk.Frame(gallery_frame)
        g_top.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(g_top, text="+ Import Tekstur Baru ke Font", style="Primary.TButton", command=self._on_import_custom_texture).pack(side=tk.LEFT, padx=4)
        ttk.Button(g_top, text="🔄 Refresh Galeri", command=self._refresh_assets_gallery).pack(side=tk.LEFT, padx=4)
        ttk.Button(g_top, text="📂 Buka Folder Font di Explorer", command=self._open_font_dir_in_explorer).pack(side=tk.LEFT, padx=4)
        self.lbl_gallery_count = ttk.Label(g_top, text="", foreground="#94a3b8")
        self.lbl_gallery_count.pack(side=tk.RIGHT, padx=4)

        # Scrollable gallery canvas
        self.gallery_canvas = tk.Canvas(gallery_frame, bg="#181818", highlightthickness=0)
        gallery_scroll = ttk.Scrollbar(gallery_frame, orient=tk.VERTICAL, command=self.gallery_canvas.yview)
        self.gallery_grid = ttk.Frame(self.gallery_canvas)

        self.gallery_grid.bind("<Configure>", lambda e: self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all")))
        self.gallery_canvas.create_window((0, 0), window=self.gallery_grid, anchor="nw")
        self.gallery_canvas.configure(yscrollcommand=gallery_scroll.set)

        self.gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gallery_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_studio_paths_to_form()
        # Gallery will be lazily loaded when user clicks tab 4

    def _load_studio_paths_to_form(self):
        cfg = load_studio_config()
        self.entry_cfg_client_pack.delete(0, tk.END)
        self.entry_cfg_client_pack.insert(0, cfg.get("client_pack_dir", ""))

        self.entry_cfg_server.delete(0, tk.END)
        self.entry_cfg_server.insert(0, cfg.get("server_dir", ""))

        self.entry_cfg_font_dir.delete(0, tk.END)
        self.entry_cfg_font_dir.insert(0, cfg.get("font_textures_dir", ""))

    def _browse_dir(self, entry_widget):
        init_dir = entry_widget.get().strip()
        if not os.path.exists(init_dir):
            init_dir = BASE_DIR
        d = filedialog.askdirectory(initialdir=init_dir)
        if d:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, os.path.normpath(d))

    def _open_dir(self, dir_path):
        p = os.path.normpath(dir_path.strip()) if dir_path else ""
        if p and os.path.exists(p):
            try:
                os.startfile(p)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka folder: {e}")
        else:
            messagebox.showerror("Folder Tidak Ditemukan", f"Folder belum ada atau path tidak valid:\n{p}")

    def _open_file(self, fpath):
        if fpath and os.path.exists(fpath):
            try:
                os.startfile(fpath)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka file: {e}")
        else:
            messagebox.showerror("File Tidak Ditemukan", f"File tidak ditemukan:\n{fpath}")

    def _reveal_in_explorer(self, fpath):
        if fpath and os.path.exists(fpath):
            try:
                import subprocess
                subprocess.run(["explorer", f"/select,{os.path.normpath(fpath)}"])
            except Exception:
                try:
                    os.startfile(os.path.dirname(fpath))
                except Exception as e:
                    messagebox.showerror("Error", f"Gagal membuka explorer: {e}")
        else:
            messagebox.showerror("File Tidak Ditemukan", f"File tidak ditemukan:\n{fpath}")

    def _save_studio_paths(self):
        cfg = {
            "client_pack_dir": self.entry_cfg_client_pack.get().strip(),
            "server_dir": self.entry_cfg_server.get().strip(),
            "font_textures_dir": self.entry_cfg_font_dir.get().strip(),
            "resourcepack_dir": os.path.join(BASE_DIR, "resourcepack")
        }
        save_studio_config(cfg)
        self.studio_cfg = cfg
        self._refresh_hud_textures()
        self._refresh_assets_gallery()
        messagebox.showinfo("Berhasil", "Pengaturan direktori berhasil disimpan ke data/studio_config.yml!")

    def _reset_studio_paths(self):
        if messagebox.askyesno("Reset", "Kembalikan direktori ke pengaturan default?"):
            defaults = {
                "client_pack_dir": r"C:\ATLauncher\instances\262\resourcepacks\BetterHud_Pack",
                "server_dir": os.path.abspath(os.path.join(BASE_DIR, "..", "..", "server")),
                "font_textures_dir": os.path.join(BASE_DIR, "resourcepack", "assets", "minecraft", "textures", "font"),
                "resourcepack_dir": os.path.join(BASE_DIR, "resourcepack")
            }
            save_studio_config(defaults)
            self._load_studio_paths_to_form()
            self._refresh_hud_textures()
            self._refresh_assets_gallery()

    def _open_font_dir_in_explorer(self):
        font_dir = get_font_textures_dir()
        self._open_dir(font_dir)

    def _refresh_assets_gallery(self):
        for w in self.gallery_grid.winfo_children():
            w.destroy()
        self._asset_thumbnails = {}
        self._gallery_rendered = True

        font_dir = get_font_textures_dir()
        if not os.path.exists(font_dir):
            self.lbl_gallery_count.config(text="Folder font tidak ditemukan")
            return

        files = sorted([f for f in os.listdir(font_dir) if f.lower().endswith(".png")])
        self.lbl_gallery_count.config(text=f"Total: {len(files)} file tekstur")

        for idx, fname in enumerate(files):
            fpath = os.path.join(font_dir, fname)
            card = ttk.LabelFrame(self.gallery_grid, text=f" {fname} ", padding=8)
            card.grid(row=idx // 4, column=idx % 4, padx=6, pady=6, sticky="nsew")

            c_w, c_h = 100, 56
            canv = tk.Canvas(card, width=c_w, height=c_h, bg="#1c1c1c", highlightthickness=1, highlightbackground="#383838")
            canv.pack(pady=4)

            try:
                mtime = os.path.getmtime(fpath)
                cache_key = (fpath, c_w, c_h, mtime)
                photo = self._texture_ram_cache.get(cache_key)
                
                with Image.open(fpath) as img:
                    orig_w, orig_h = img.size
                    fsize = os.path.getsize(fpath) / 1024.0

                    if photo is None:
                        aspect = orig_w / max(1, orig_h)
                        if aspect > (c_w / c_h):
                            nw = c_w - 6
                            nh = max(1, int(nw / aspect))
                        else:
                            nh = c_h - 6
                            nw = max(1, int(nh * aspect))

                        thumb = img.resize((nw, nh), Image.Resampling.NEAREST)
                        photo = ImageTk.PhotoImage(thumb)
                        self._texture_ram_cache[cache_key] = photo

                self._asset_thumbnails[fname] = photo
                canv.create_image(c_w // 2, c_h // 2, image=photo)
            except Exception:
                orig_w, orig_h = 0, 0
                fsize = 0.0

            info_txt = f"{orig_w}×{orig_h} px • {fsize:.1f} KB"
            ttk.Label(card, text=info_txt, font=("Segoe UI", 8), foreground="#94a3b8").pack()

            btn_row = ttk.Frame(card)
            btn_row.pack(fill=tk.X, pady=(6, 2))

            ttk.Button(btn_row, text="📂 Edit File", width=9, command=lambda p=fpath: self._open_file(p)).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_row, text="📁 Explorer", width=9, command=lambda p=fpath: self._reveal_in_explorer(p)).pack(side=tk.LEFT, padx=2)

    def _on_asset_tab_texture_selected(self, event=None):
        pass

    def _apply_active_textures_from_tab(self):
        if not hasattr(self, 'combo_asset_box_tex') or not hasattr(self, 'combo_asset_np_tex'):
            return
        box_tex = self.combo_asset_box_tex.get().strip()
        np_tex = self.combo_asset_np_tex.get().strip()
        if not box_tex or not np_tex:
            return
        self._save_hud_snapshot()
        tex_cfg = self.hud_cfg.setdefault("textures", {})
        tex_cfg["dialog_box"] = box_tex
        tex_cfg["nameplate"] = np_tex
        save_hud_config(self.hud_cfg)
        if hasattr(self, 'combo_hud_box_tex'):
            self.combo_hud_box_tex.set(box_tex)
        if hasattr(self, 'combo_hud_np_tex'):
            self.combo_hud_np_tex.set(np_tex)
        self._redraw_hud_canvas()
        messagebox.showinfo("Tekstur Diperbarui", f"Tekstur aktif berhasil diatur:\n• Dialog Box: {box_tex}\n• Nameplate: {np_tex}")

    # =========================================================================
    # TAB 5: 1-CLICK COMPILE & CLIENT SYNC
    # =========================================================================
    def _build_sync_tab(self):
        frame = ttk.Frame(self.tab_sync, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="1-Click Compiler & Pack Synchronizer", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=4)
        desc = (
            "Alur sinkronisasi otomatis:\n"
            "1. Menyesuaikan resolusi potret (64x64, 128x128, 256x256) agar pas di frame BetterHud (64x72).\n"
            "2. Mendaftarkan bitmap & kondisi emosi ke BetterHud (dialog-images.yml & dialog-layout.yml).\n"
            "3. Menghasilkan event FancyNpcs & router Skript (story_dialogues.sk).\n"
            "4. Menyalin aset & font ke resource pack client (BetterHud_Pack & Aethir_Story_VN) tanpa merusak shader depth 500.0."
        )
        ttk.Label(frame, text=desc, justify=tk.LEFT).pack(anchor="w", pady=6)

        btn_box = ttk.Frame(frame)
        btn_box.pack(fill=tk.X, pady=12)

        ttk.Button(btn_box, text="⚡ 1. COMPILE BETTERHUD & SKRIPT", command=self._on_compile_all).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_box, text="🔄 2. SYNC KE RESOURCE PACK CLIENT", command=self._on_sync_pack).pack(side=tk.LEFT, padx=6)

        ttk.Label(frame, text="Log Aktivitas:").pack(anchor="w", pady=(8, 2))
        self.log_text = tk.Text(
            frame,
            height=14,
            bg="#202020",
            fg="#e0e0e0",
            insertbackground="#60cdff",
            selectbackground="#007acc",
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightbackground="#383838",
            relief="flat",
            font=("Consolas", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def _on_compile_all(self):
        self._log("=== MEMULAI COMPILE ===")
        try:
            res = compile_all()
            self._log(f"-> Karakter terproses: {res['characters_compiled']}")
            self._log(f"-> Slot gambar terdaftar di layout: {res['layout_images_count']}")
            self._log(f"-> Skript router selesai dibuat: {res['skript_path']}")
            self._log("LANGKAH MUDAH SINKRONISASI IN-GAME:")
            self._log("Cukup ketik 1 perintah di chat / konsol Minecraft:")
            self._log("  👉 /vn reload")
            self._log("(Perintah ini otomatis reload BetterHUD, Skript router, dan dialog)")
            messagebox.showinfo("Compile Selesai", "Konfigurasi BetterHud & Skript berhasil di-generate!\n\nJalankan di Minecraft:\n/vn reload")
        except Exception as e:
            self._log(f"[ERROR] Gagal compile: {e}")
            messagebox.showerror("Error", f"Gagal compile: {e}")

    def _on_sync_pack(self):
        self._log("=== SINKRONISASI PACK KE CLIENT ===")
        try:
            count, msg = sync_client_pack()
            self._log(f"-> {msg}: {count} file berhasil disinkronkan.")
            self._log("PENTING: Jalankan '/vn reload' di Minecraft (dan F3 + T jika mengubah file gambar/font)!")
            messagebox.showinfo("Sync Selesai", f"Sinkronisasi berhasil! ({count} file)\n\nJalankan di Minecraft:\n/vn reload\n(atau F3 + T jika ada tekstur baru)")
        except Exception as e:
            self._log(f"[ERROR] Gagal sync pack: {e}")
            messagebox.showerror("Error", f"Gagal sync pack: {e}")

    def _on_create_custom_hud_dialog(self, default_file=""): 
        """Dialog untuk menambahkan custom HUD element (gambar atau teks) baru."""
        dlg = tk.Toplevel(self)
        dlg.title("Tambah Elemen Custom HUD Dialog")
        dlg.geometry("420x420")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        ttk.Label(dlg, text="ID Elemen Unik (contoh: quest_badge, decor_box):", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        ent_id = ttk.Entry(dlg, width=32)
        ent_id.pack(fill=tk.X, padx=14, pady=(0, 8))
        ent_id.focus_set()

        ttk.Label(dlg, text="Tipe Elemen:", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(2, 2))
        combo_type = ttk.Combobox(dlg, values=["image", "text"], state="readonly")
        combo_type.set("image")
        combo_type.pack(fill=tk.X, padx=14, pady=(0, 8))

        frame_img = ttk.LabelFrame(dlg, text="Pengaturan Gambar (PNG)", padding=8)
        frame_img.pack(fill=tk.X, padx=14, pady=4)
        
        row_file = ttk.Frame(frame_img)
        row_file.pack(fill=tk.X)
        ent_file = ttk.Entry(row_file)
        if default_file:
            ent_file.insert(0, default_file)
            ent_id.insert(0, os.path.splitext(default_file)[0].lower().replace(" ", "_"))
        ent_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        
        def _browse_img():
            fn = filedialog.askopenfilename(title="Pilih File Gambar PNG", filetypes=[("PNG Files", "*.png")])
            if fn:
                fname = os.path.basename(fn)
                font_dir = get_font_textures_dir()
                os.makedirs(font_dir, exist_ok=True)
                dest = os.path.join(font_dir, fname)
                try:
                    shutil.copyfile(fn, dest)
                except Exception:
                    pass
                ent_file.delete(0, tk.END)
                ent_file.insert(0, fname)
                if not ent_id.get().strip():
                    ent_id.insert(0, os.path.splitext(fname)[0].lower().replace(" ", "_"))

        ttk.Button(row_file, text="Browse...", command=_browse_img).pack(side=tk.RIGHT)

        frame_txt = ttk.LabelFrame(dlg, text="Pengaturan Teks", padding=8)
        ttk.Label(frame_txt, text="Pattern Teks (contoh: <#FFFF55>★ Quest):").pack(anchor="w", pady=(0, 2))
        ent_pattern = ttk.Entry(frame_txt)
        ent_pattern.pack(fill=tk.X)

        def _on_type_change(e=None):
            if combo_type.get() == "image":
                frame_txt.pack_forget()
                frame_img.pack(fill=tk.X, padx=14, pady=4)
            else:
                frame_img.pack_forget()
                frame_txt.pack(fill=tk.X, padx=14, pady=4)
        combo_type.bind("<<ComboboxSelected>>", _on_type_change)

        coords_row = ttk.Frame(dlg)
        coords_row.pack(fill=tk.X, padx=14, pady=8)
        ttk.Label(coords_row, text="X:").pack(side=tk.LEFT)
        sp_x = ttk.Spinbox(coords_row, from_=-400, to=800, width=6)
        sp_x.set("100")
        sp_x.pack(side=tk.LEFT, padx=(2, 8))
        
        ttk.Label(coords_row, text="Y:").pack(side=tk.LEFT)
        sp_y = ttk.Spinbox(coords_row, from_=-400, to=800, width=6)
        sp_y.set("10")
        sp_y.pack(side=tk.LEFT, padx=(2, 8))

        ttk.Label(coords_row, text="Layer:").pack(side=tk.LEFT)
        sp_ly = ttk.Spinbox(coords_row, from_=1, to=10, width=4)
        sp_ly.set("2")
        sp_ly.pack(side=tk.LEFT, padx=(2, 8))

        def _do_save_custom():
            cid = ent_id.get().strip().lower().replace(" ", "_")
            if not cid:
                messagebox.showerror("Error", "ID Elemen tidak boleh kosong!", parent=dlg)
                return
            elems = self.hud_cfg.setdefault("elements", {})
            if cid in elems:
                messagebox.showerror("Error", f"Elemen '{cid}' sudah ada!", parent=dlg)
                return
            ctype = combo_type.get()
            try:
                cx = int(sp_x.get())
                cy = int(sp_y.get())
                cly = int(sp_ly.get())
            except ValueError:
                cx, cy, cly = 100, 10, 2

            self._save_hud_snapshot()
            custom_elems = self.hud_cfg.setdefault("custom_elements", {})
            c_data = {
                "type": ctype,
                "x": cx,
                "y": cy,
                "scale": 1.0,
                "layer": cly
            }
            if ctype == "image":
                c_data["file"] = ent_file.get().strip() or f"{cid}.png"
            else:
                c_data["pattern"] = ent_pattern.get().strip() or cid
                c_data["shadow"] = True

            custom_elems[cid] = c_data
            elems[cid] = {
                "x": cx,
                "y": cy,
                "scale": 1.0,
                "layer": cly
            }
            groups = self.hud_cfg.setdefault("groups", {})
            if "Semua Elemen (All)" in groups and cid not in groups["Semua Elemen (All)"]:
                groups["Semua Elemen (All)"].append(cid)

            try:
                save_hud_config(self.hud_cfg)
                from compiler import compile_portraits_and_betterhud
                compile_portraits_and_betterhud(self.characters)
            except Exception as e:
                self._log(f"[WARN] Compile custom HUD: {e}")

            self._refresh_hud_elements_combo()
            self._refresh_group_combo()
            self.combo_hud_elem.set(cid)
            self._update_hud_editor_fields()
            self._redraw_hud_canvas()
            self._log(f"[HUD] Custom HUD Element '{cid}' berhasil ditambahkan.")
            dlg.destroy()

        btn_row = ttk.Frame(dlg)
        btn_row.pack(fill=tk.X, padx=14, pady=12)
        ttk.Button(btn_row, text="Batal", command=dlg.destroy).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="✓ Simpan & Tambahkan ke HUD", command=_do_save_custom).pack(side=tk.RIGHT)

if __name__ == "__main__":
    app = StoryStudioApp()
    app.mainloop()
