#!/usr/bin/env python3
"""
Compiler for Story Core Visual Novel
Builds character definitions, portrait assets, BetterHud images & layout,
and generates Skript dialogue triggers with FancyNpcs integration.
"""

import os
import sys
import shutil
import zipfile
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from image_processor import process_portrait, TARGET_WIDTH, TARGET_HEIGHT

# Project Directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

DATA_DIR = os.path.join(BASE_DIR, "data")
CHARACTERS_DIR = os.path.join(DATA_DIR, "characters")
DIALOGUES_DIR = os.path.join(DATA_DIR, "dialogues")
HUD_CONFIG_FILE = os.path.join(DATA_DIR, "hud_config.yml")

SERVER_DIR = os.environ.get("VN_SERVER_DIR") or os.path.join(WORKSPACE_ROOT, "server")
BETTERHUD_DIR = os.path.join(SERVER_DIR, "plugins", "BetterHud")
BETTERHUD_ASSETS_DIR = os.path.join(BETTERHUD_DIR, "assets", "dialog")
BETTERHUD_IMAGES_FILE = os.path.join(BETTERHUD_DIR, "images", "dialog-images.yml")
BETTERHUD_LAYOUT_FILE = os.path.join(BETTERHUD_DIR, "layouts", "vn-dialog-layout.yml")
BETTERHUD_BUILD_ZIP = os.path.join(BETTERHUD_DIR, "build.zip")

SKRIPT_SCRIPTS_DIR = os.path.join(SERVER_DIR, "plugins", "Skript", "scripts")
LOCAL_SCRIPTS_DIR = BASE_DIR
CLIENT_PACK_DIR = os.environ.get("VN_CLIENT_PACK_DIR") or r"C:\ATLauncher\instances\262\resourcepacks\BetterHud_Pack"
STUDIO_CONFIG_FILE = os.path.join(DATA_DIR, "studio_config.yml")

STANDARD_EMOTIONS = ["biasa", "bahagia", "marah", "sedih", "unique"]

def load_studio_config():
    """Loads custom workspace and directory locations."""
    defaults = {
        "client_pack_dir": CLIENT_PACK_DIR,
        "server_dir": SERVER_DIR,
        "resourcepack_dir": os.path.join(BASE_DIR, "resourcepack"),
        "font_textures_dir": os.path.join(BASE_DIR, "resourcepack", "assets", "minecraft", "textures", "font")
    }
    if os.path.exists(STUDIO_CONFIG_FILE):
        try:
            with open(STUDIO_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and isinstance(data, dict):
                    defaults.update(data)
        except Exception:
            pass
    return defaults

def save_studio_config(cfg):
    """Saves custom workspace and directory locations."""
    os.makedirs(os.path.dirname(STUDIO_CONFIG_FILE), exist_ok=True)
    with open(STUDIO_CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

def get_client_pack_dir():
    return load_studio_config().get("client_pack_dir", CLIENT_PACK_DIR)

def get_server_dir():
    return load_studio_config().get("server_dir", SERVER_DIR)

def get_font_textures_dir():
    return load_studio_config().get("font_textures_dir", os.path.join(BASE_DIR, "resourcepack", "assets", "minecraft", "textures", "font"))

def resolve_asset_path(path_str: str) -> str:
    """Resolves relative paths from either BASE_DIR or WORKSPACE_ROOT."""
    if not path_str:
        return ""
    if os.path.isabs(path_str) and os.path.exists(path_str):
        return path_str
    
    # Try relative to BASE_DIR (plugins/story)
    candidate1 = os.path.abspath(os.path.join(BASE_DIR, path_str))
    if os.path.exists(candidate1):
        return candidate1
        
    # Try relative to WORKSPACE_ROOT (Project-mc)
    candidate2 = os.path.abspath(os.path.join(WORKSPACE_ROOT, path_str))
    if os.path.exists(candidate2):
        return candidate2
        
    return candidate1

def ensure_dirs():
    os.makedirs(CHARACTERS_DIR, exist_ok=True)
    os.makedirs(DIALOGUES_DIR, exist_ok=True)
    os.makedirs(BETTERHUD_ASSETS_DIR, exist_ok=True)
    for d in (BETTERHUD_IMAGES_FILE, BETTERHUD_LAYOUT_FILE):
        os.makedirs(os.path.dirname(d), exist_ok=True)

def load_characters():
    characters = {}
    if not os.path.exists(CHARACTERS_DIR):
        return characters
    for fname in os.listdir(CHARACTERS_DIR):
        if fname.endswith(".yml") or fname.endswith(".yaml"):
            fpath = os.path.join(CHARACTERS_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "id" in data:
                    characters[data["id"]] = data
    return characters

def load_dialogues():
    dialogues = {}
    if not os.path.exists(DIALOGUES_DIR):
        return dialogues
    for fname in os.listdir(DIALOGUES_DIR):
        if fname.endswith(".yml") or fname.endswith(".yaml"):
            fpath = os.path.join(DIALOGUES_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "id" in data:
                    dialogues[data["id"]] = data
    return dialogues

def load_hud_config():
    """Loads HUD layout element positions and scales."""
    default_groups = {
        "Semua Elemen (All)": ["portrait", "nameplate", "dialog_box", "speaker_text", "dialog_text"],
        "Kotak Dialog & Teks": ["dialog_box", "dialog_text"],
        "Potret & Nama": ["portrait", "nameplate", "speaker_text"],
        "Semua Teks": ["speaker_text", "dialog_text"]
    }
    default_textures = {
        "dialog_box": "dialogue_box.png",
        "nameplate": "nameplate.png"
    }
    default_config = {
        "elements": {
            "portrait": {"x": 38, "y": -54, "scale": 0.78, "base_size": 128},
            "nameplate": {"x": 56, "y": 38, "scale": 1.0},
            "dialog_box": {"x": 0, "y": 0, "scale": 1.0},
            "speaker_text": {"x": 64, "y": 44, "scale": 0.52, "color": "<#FFFFFF>", "space": 0, "align": "left"},
            "dialog_text": {"x": 98, "y": 5, "scale": 0.46, "color": "<#F0F0F0>", "line": 4, "split_width": 145, "line_width": 9, "space": 0, "align": "left"}
        },
        "groups": default_groups,
        "textures": default_textures,
        "custom_elements": {}
    }
    if os.path.exists(HUD_CONFIG_FILE):
        try:
            with open(HUD_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                if cfg and "elements" in cfg:
                    if "groups" not in cfg or not cfg["groups"]:
                        cfg["groups"] = default_groups
                    if "textures" not in cfg or not cfg["textures"]:
                        cfg["textures"] = dict(default_textures)
                    return cfg
        except Exception:
            pass
    return default_config

def save_hud_config(config):
    """Saves HUD layout element positions and scales."""
    os.makedirs(os.path.dirname(HUD_CONFIG_FILE), exist_ok=True)
    with open(HUD_CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def compile_portraits_and_betterhud(characters):
    """
    1. Resizes all character emotion portraits into BetterHud assets.
    2. Writes BetterHud images/dialog-images.yml.
    3. Writes BetterHud layouts/dialog-layout.yml with dynamic speaker + emotion conditions.
    """
    ensure_dirs()
    raw_hud = load_hud_config()
    hud_cfg = raw_hud["elements"]
    tex_cfg = raw_hud.get("textures", {})
    box_filename = tex_cfg.get("dialog_box", "dialogue_box.png")
    nameplate_filename = tex_cfg.get("nameplate", "nameplate.png")

    font_dir = get_font_textures_dir()
    src_box = os.path.join(font_dir, box_filename)
    if not os.path.exists(src_box):
        src_box = os.path.join(font_dir, "dialogue_box.png")
    dest_box = os.path.join(BETTERHUD_ASSETS_DIR, "dialogue_box.png")
    if os.path.exists(src_box):
        os.makedirs(os.path.dirname(dest_box), exist_ok=True)
        shutil.copyfile(src_box, dest_box)

    src_np = os.path.join(font_dir, nameplate_filename)
    if not os.path.exists(src_np):
        src_np = os.path.join(font_dir, "nameplate.png")
    dest_np = os.path.join(BETTERHUD_ASSETS_DIR, "nameplate.png")
    if os.path.exists(src_np):
        os.makedirs(os.path.dirname(dest_np), exist_ok=True)
        shutil.copyfile(src_np, dest_np)

    src_fade = os.path.join(BASE_DIR, "textures", "bottom_cinematic_fade.png")
    dest_fade = os.path.join(BETTERHUD_ASSETS_DIR, "bottom_cinematic_fade.png")
    if os.path.exists(src_fade):
        os.makedirs(os.path.dirname(dest_fade), exist_ok=True)
        shutil.copyfile(src_fade, dest_fade)
    
    images_dict = {
        "bottom_cinematic_fade": {
            "type": "single",
            "file": "dialog/bottom_cinematic_fade.png"
        },
        "dialog_box": {
            "type": "single",
            "file": "dialog/dialogue_box.png"
        },
        "nameplate": {
            "type": "single",
            "file": "dialog/nameplate.png"
        }
    }
    
    DEFAULT_HUD_LAYERS = {
        "dialog_box": 2,
        "portrait": 3,
        "nameplate": 4,
        "speaker_text": 5,
        "dialog_text": 5,
        "counter_text": 5
    }

    image_groups = []

    # Include bottom_cinematic_fade in vn_dialog_layout (single layout pattern matching test_box)
    fade_key = "bottom_cinematic_fade" if "bottom_cinematic_fade" in hud_cfg else "background_fade"
    if fade_key in hud_cfg:
        bg_cfg = hud_cfg[fade_key]
        if bg_cfg.get("enabled", True):
            bg_layer = int(bg_cfg.get("layer", 1))
            fade_item = {
                "name": "bottom_cinematic_fade",
                "x": int(bg_cfg.get("x", 0)),
                "y": int(bg_cfg.get("y", -45)),
                "scale": float(bg_cfg.get("scale", 2.5)),
                "layer": bg_layer
            }
            image_groups.append((bg_layer, [fade_item]))

    if "dialog_box" in hud_cfg:
        box_cfg = hud_cfg["dialog_box"]
        b_layer = int(box_cfg.get("layer", DEFAULT_HUD_LAYERS["dialog_box"]))
        box_item = {
            "name": "dialog_box",
            "x": int(box_cfg.get("x", 75)),
            "y": int(box_cfg.get("y", -23)),
            "scale": float(box_cfg.get("scale", 1.0)),
            "layer": b_layer
        }
        image_groups.append((b_layer, [box_item]))

    if "portrait" in hud_cfg:
        port_cfg = hud_cfg["portrait"]
        p_layer = int(port_cfg.get("layer", DEFAULT_HUD_LAYERS["portrait"]))
        port_scale = float(port_cfg.get("scale", 0.78))
        port_items = []
        for char_id, char_data in characters.items():
            speaker_name = char_data.get("speaker_name", char_data.get("name", char_id.capitalize()))
            portraits = char_data.get("portraits", {})
            
            char_emotions = list(STANDARD_EMOTIONS)
            for em in portraits.keys():
                if em and em not in char_emotions:
                    char_emotions.append(em)

            for em in char_emotions:
                img_key = f"portrait_{char_id}_{em}"
                src_raw = portraits.get(em, "")
                src_img = resolve_asset_path(src_raw)
                dest_png = os.path.join(BETTERHUD_ASSETS_DIR, f"{img_key}.png")
                
                if src_img and os.path.exists(src_img):
                    # Copy original file directly without resizing to preserve native resolution (e.g. 128x128 pixel art)
                    os.makedirs(os.path.dirname(dest_png), exist_ok=True)
                    shutil.copyfile(src_img, dest_png)
                elif not os.path.exists(dest_png):
                    biasa_dest = os.path.join(BETTERHUD_ASSETS_DIR, "portrait_luna_biasa.png")
                    if os.path.exists(biasa_dest):
                        shutil.copyfile(biasa_dest, dest_png)

                images_dict[img_key] = {
                    "type": "single",
                    "file": f"dialog/{img_key}.png"
                }

                p_entry = {
                    "name": img_key,
                    "x": int(port_cfg.get("x", -18)),
                    "y": int(port_cfg.get("y", -43)),
                    "scale": port_scale,
                    "layer": p_layer,
                    "conditions": {
                        1: {
                            "first": "custom_variable:skript_1",
                            "second": f"'{speaker_name}'",
                            "operation": "=="
                        },
                        2: {
                            "first": "custom_variable:skript_4",
                            "second": f"'{em}'",
                            "operation": "=="
                        }
                    }
                }
                port_items.append(p_entry)

                # If emotion is unique, also support alias 'kustom'
                if em == "unique":
                    p_entry_kustom = {
                        "name": img_key,
                        "x": int(port_cfg.get("x", -18)),
                        "y": int(port_cfg.get("y", -43)),
                        "scale": port_scale,
                        "layer": p_layer,
                        "conditions": {
                            1: {
                                "first": "custom_variable:skript_1",
                                "second": f"'{speaker_name}'",
                                "operation": "=="
                            },
                            2: {
                                "first": "custom_variable:skript_4",
                                "second": "'kustom'",
                                "operation": "=="
                            }
                        }
                    }
                    port_items.append(p_entry_kustom)
        image_groups.append((p_layer, port_items))

    if "nameplate" in hud_cfg:
        np_cfg = hud_cfg["nameplate"]
        np_layer = int(np_cfg.get("layer", DEFAULT_HUD_LAYERS["nameplate"]))
        np_item = {
            "name": "nameplate",
            "x": int(np_cfg.get("x", 1)),
            "y": int(np_cfg.get("y", 38)),
            "scale": float(np_cfg.get("scale", 1.0)),
            "layer": np_layer
        }
        image_groups.append((np_layer, [np_item]))

    # Sort image groups by layer (lower layer rendered first / background, higher layer rendered later / foreground)
    image_groups.sort(key=lambda g: g[0])

    layout_images = {}
    img_counter = 1
    for _, items in image_groups:
        for item in items:
            layout_images[img_counter] = item
            img_counter += 1

    layout_texts = {}
    text_counter = 1

    if "speaker_text" in hud_cfg:
        spk_cfg = hud_cfg["speaker_text"]
        spk_layer = int(spk_cfg.get("layer", DEFAULT_HUD_LAYERS["speaker_text"]))
        spk_x = int(spk_cfg.get("x", 64))
        spk_y = int(spk_cfg.get("y", 44))
        spk_scale = float(spk_cfg.get("scale", 0.52))
        spk_align = spk_cfg.get("align", "left")

        # Enforce minimum layer 4 for text shadow so BetterHUD shader doesn't clip (layer: 0 bug)
        spk_render_layer = max(spk_layer, 6)
        shadow_layer = spk_render_layer - 1

        # Two-layer text: Shadow (offset +1,+1 in <#111111>)
        layout_texts[text_counter] = {
            "name": "dialog_font",
            "pattern": "<#111111>[custom_variable:skript_1]",
            "x": spk_x + 1,
            "y": spk_y + 1,
            "align": spk_align,
            "scale": spk_scale,
            "layer": shadow_layer
        }
        text_counter += 1

        # Foreground Text
        layout_texts[text_counter] = {
            "name": "dialog_font",
            "pattern": f"{spk_cfg.get('color', '<#FFFFFF>')}[custom_variable:skript_1]",
            "x": spk_x,
            "y": spk_y,
            "align": spk_align,
            "scale": spk_scale,
            "layer": spk_render_layer
        }
        text_counter += 1

    if "dialog_text" in hud_cfg:
        dlg_cfg = hud_cfg["dialog_text"]
        dlg_layer = int(dlg_cfg.get("layer", DEFAULT_HUD_LAYERS["dialog_text"]))
        dlg_x = int(dlg_cfg.get("x", 98))
        dlg_y = int(dlg_cfg.get("y", 5))
        dlg_scale = float(dlg_cfg.get("scale", 0.46))
        dlg_space = int(dlg_cfg.get("space", 0))
        dlg_line = int(dlg_cfg.get("line", 4))
        dlg_split = int(dlg_cfg.get("split_width", 145))
        dlg_line_w = int(dlg_cfg.get("line_width", 9))
        dlg_align = dlg_cfg.get("align", "left")

        # Dialog text must render above dialog_box (2) / portrait (3) / nameplate (4)
        dlg_render_layer = max(dlg_layer, 6)
        shadow_dlg_layer = dlg_render_layer - 1

        # Two-layer text: Shadow (offset +1,+1 in <#111111>)
        layout_texts[text_counter] = {
            "name": "dialog_font",
            "pattern": "<#111111>[custom_variable:skript_2]",
            "x": dlg_x + 1,
            "y": dlg_y + 1,
            "align": dlg_align,
            "scale": dlg_scale,
            "space": dlg_space,
            "line": dlg_line,
            "split-width": dlg_split,
            "line-width": dlg_line_w,
            "force-split": False,
            "layer": shadow_dlg_layer
        }
        text_counter += 1

        # Foreground Text
        layout_texts[text_counter] = {
            "name": "dialog_font",
            "pattern": f"{dlg_cfg.get('color', '<#F0F0F0>')}[custom_variable:skript_2]",
            "x": dlg_x,
            "y": dlg_y,
            "align": dlg_align,
            "scale": dlg_scale,
            "space": dlg_space,
            "line": dlg_line,
            "split-width": dlg_split,
            "line-width": dlg_line_w,
            "force-split": False,
            "layer": dlg_render_layer
        }
        text_counter += 1

    # Keep fade inside same layout. Center alignment preserves each element's local offset.
    fade_layout_images = {}
    fade_img_counter = 1

    custom_elems = raw_hud.get("custom_elements", {})
    if custom_elems:
        for c_key, c_data in custom_elems.items():
            elem_data = hud_cfg.get(c_key, {})
            c_type = c_data.get("type", "image")
            c_x = int(elem_data.get("x", c_data.get("x", 0)))
            c_y = int(elem_data.get("y", c_data.get("y", 0)))
            c_scale = float(elem_data.get("scale", c_data.get("scale", 1.0)))
            c_layer = int(elem_data.get("layer", c_data.get("layer", 2)))
            
            if c_type == "image":
                c_file = c_data.get("file", f"{c_key}.png")
                src_custom = resolve_asset_path(c_file)
                if not src_custom or not os.path.exists(src_custom):
                    src_custom = os.path.join(font_dir, c_file)
                dest_custom = os.path.join(BETTERHUD_ASSETS_DIR, f"{c_key}.png")
                if src_custom and os.path.exists(src_custom):
                    shutil.copyfile(src_custom, dest_custom)
                
                images_dict[c_key] = {
                    "type": "single",
                    "file": f"dialog/{c_key}.png"
                }

                if "fade" in c_key.lower():
                    fade_layout_images[fade_img_counter] = {
                        "name": c_key,
                        "x": c_x,
                        "y": c_y,
                        "scale": c_scale,
                        "layer": c_layer
                    }
                    fade_img_counter += 1
                else:
                    layout_images[img_counter] = {
                        "name": c_key,
                        "x": c_x,
                        "y": c_y,
                        "scale": c_scale,
                        "layer": c_layer
                    }
                    img_counter += 1
            elif c_type == "text":
                c_pattern = c_data.get("pattern", "")
                c_font = c_data.get("font", "dialog_font")
                c_align = c_data.get("align", "left")
                if c_data.get("shadow", True):
                    layout_texts[text_counter] = {
                        "name": c_font,
                        "pattern": f"<#111111>{c_pattern}",
                        "x": c_x + 1,
                        "y": c_y + 1,
                        "align": c_align,
                        "scale": c_scale,
                        "layer": max(1, c_layer - 1)
                    }
                    text_counter += 1
                layout_texts[text_counter] = {
                    "name": c_font,
                    "pattern": c_pattern,
                    "x": c_x,
                    "y": c_y,
                    "align": c_align,
                    "scale": c_scale,
                    "layer": c_layer
                }
                text_counter += 1

    dialog_layout = {
        "vn_dialog_layout": {
            "align": "left",
            "offset": "center",
            "images": layout_images,
            "texts": layout_texts
        }
    }

    with open(BETTERHUD_IMAGES_FILE, "w", encoding="utf-8") as f:
        yaml.dump(images_dict, f, default_flow_style=False, sort_keys=False)
        
    with open(BETTERHUD_LAYOUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(dialog_layout, f, default_flow_style=False, sort_keys=False)

    # Clean up redundant separate fade layout
    fade_layout_file = os.path.join(BETTERHUD_DIR, "layouts", "vn-fade-layout.yml")
    if os.path.exists(fade_layout_file):
        os.remove(fade_layout_file)

    # Sync popup definition using single layout (vn_dialog_layout)
    popup_file = os.path.join(BETTERHUD_DIR, "popups", "vn-dialog-popup.yml")
    if os.path.exists(popup_file) or os.path.exists(os.path.dirname(popup_file)):
        os.makedirs(os.path.dirname(popup_file), exist_ok=True)
        popup_layouts = {
            1: {
                "name": "vn_dialog_layout",
                "gui": {"x": 50, "y": 100},
                "pixel": {"x": 0, "y": -78}
            }
        }
        popup_data = {
            "vn_dialog": {
                "duration": 999999,
                "key-mapping": False,
                "triggers": {
                    1: {
                        "class": "custom",
                        "name": "vn_dialog"
                    }
                },
                "layouts": popup_layouts
            }
        }
        with open(popup_file, "w", encoding="utf-8") as pf:
            yaml.dump(popup_data, pf, default_flow_style=False, sort_keys=False)
        
    return len(characters), len(layout_images)

def generate_skript_dialogues(characters, dialogues):
    """
    Generates story_dialogues.sk with FancyNpcs / villager routing and dynamic queue calls.
    """
    lines = [
        "# ==============================================================================",
        "#              GENERATED STORY DIALOGUES & NPC ROUTER",
        "#         Auto-generated by Story Studio Compiler. Do NOT edit manually.",
        "# ==============================================================================",
        "",
        "# Router utama ke skrip dialog karakter",
        "function storyRouteNpcDialogue(p: player, npcName: text, loc: location):",
        "\tset {_uuid} to uuid of {_p}",
        "\tset {_waitedFin} to difference between {story::dialogue_finish_cooldown::%{_uuid}%} and now",
        "\tif {_waitedFin} is less than 1.5 seconds:",
        "\t\tstop",
        "\t"
    ]

    for char_id, char_data in characters.items():
        fn_name = char_data.get("fancynpc_name", char_data.get("name", char_id.capitalize()))
        speaker = char_data.get("speaker_name", char_data.get("name", char_id.capitalize()))
        
        lines.append(f"\tif {{_npcName}} contains \"{fn_name}\" or \"{char_id}\" or \"{speaker}\":")
        lines.append(f"\t\thandleStoryNpc_{char_id}({{_p}}, {{_loc}})")
        lines.append("\t\tstop")
        lines.append("\t")

    lines.append("")
    lines.append("# ==============================================================================")
    lines.append("#                         HANDLER DIALOG PER KARAKTER")
    lines.append("# ==============================================================================")
    lines.append("")

    for char_id, char_data in characters.items():
        speaker = char_data.get("speaker_name", char_data.get("name", char_id.capitalize()))
        voice = char_data.get("voice", {}).get("sound", "")
        if voice is None:
            voice = ""
        pitch = 1.0

        char_dlgs = [d for d in dialogues.values() if d.get("character") == char_id]

        lines.append(f"function handleStoryNpc_{char_id}(p: player, loc: location):")
        lines.append(f"\tset {{_uuid}} to uuid of {{_p}}")
        lines.append(f"\tset {{_stage}} to {{story::{char_id}::%{{_uuid}}%::stage}} ? \"NOT_STARTED\"")
        lines.append(f"\tstoryClearDialogueQueue({{_p}})")
        lines.append("")

        if not char_dlgs:
            lines.append(f"\tstoryQueueDialogue({{_p}}, \"{speaker}\", \"Halo petualang! Senang bertemu denganmu.\", \"{voice}\", {pitch}, \"biasa\")")
            lines.append(f"\tstoryStartDialogueQueue({{_p}}, \"\", {{_loc}})")
        else:
            for i, dlg in enumerate(char_dlgs):
                req_stage = dlg.get("trigger", {}).get("stage_required", "NOT_STARTED")
                cond = "if" if i == 0 else "else if"
                lines.append(f"\t{cond} {{_stage}} is \"{req_stage}\":")
                for item in dlg.get("lines", []):
                    em = item.get("emotion", "biasa")
                    t = item.get("text", "").replace('"', '\\"')
                    lines.append(f"\t\tstoryQueueDialogue({{_p}}, \"{speaker}\", \"{t}\", \"{voice}\", {pitch}, \"{em}\")")
                cb = dlg.get("callback", "")
                lines.append(f"\t\tstoryStartDialogueQueue({{_p}}, \"{cb}\", {{_loc}})")

        lines.append("")

    sk_content = "\n".join(lines)
    
    server_path = os.path.join(SKRIPT_SCRIPTS_DIR, "story", "story_dialogues.sk")
    local_path = os.path.join(LOCAL_SCRIPTS_DIR, "story_dialogues.sk")
    
    os.makedirs(os.path.dirname(server_path), exist_ok=True)
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(sk_content)
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(sk_content)

    return server_path

def validate_font_json(name, raw):
    """Flags bitmap providers whose ascent > height (non-encoded) which Minecraft rejects."""
    if not (name.endswith('.json') and '/font/' in name):
        return []
    import json
    try:
        providers = json.loads(raw.decode('utf-8')).get('providers', [])
    except Exception as e:
        return [f"{name}: invalid JSON ({e})"]
    out = []
    for i, prov in enumerate(providers):
        if prov.get('type') != 'bitmap':
            continue
        asc, hgt = prov.get('ascent', 0), prov.get('height', 8)
        # BetterHUD encodes screen coordinates in large negative ascents; those are intentional
        if asc >= 0 and asc > hgt:
            out.append(f"{name}: provider #{i} ascent {asc} > height {hgt}")
    return out

def sync_client_pack():
    """
    Copies compiled files from BetterHud build.zip directly to client BetterHud_Pack.zip,
    strictly filtering out unreferenced default assets (compasses, mob heads, default bars, font1),
    ensures 26.2 root shaders are placed in assets/minecraft/shaders/core/,
    and cleans up any loose BetterHud_Pack directory to prevent client override conflicts.
    """
    client_pack = get_client_pack_dir()
    if not os.path.exists(BETTERHUD_BUILD_ZIP):
        return 0, "build.zip not found (run /betterhud reload first on server)"
    
    zip_dest = client_pack if client_pack.endswith('.zip') else client_pack + ".zip"
    rp_dir = os.path.dirname(zip_dest)
    if not os.path.exists(rp_dir):
        return 0, f"Client resourcepack directory not found: {rp_dir}"

    loose_dir = client_pack[:-4] if client_pack.endswith('.zip') else client_pack
    if os.path.exists(loose_dir) and os.path.isdir(loose_dir):
        try:
            shutil.rmtree(loose_dir)
        except Exception:
            pass

    count = 0
    import io
    buf = io.BytesIO()
    shader_src = {}
    problems = []
    with zipfile.ZipFile(BETTERHUD_BUILD_ZIP, 'r') as zin, zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            name = item.filename
            if name.endswith('/'):
                continue
            nl = name.lower()
            # Filter out unused default BetterHUD demo assets
            if ('compass_' in nl or 
                'entity_head' in nl or 
                'image_entity_' in nl or 
                'image_default_' in nl or 
                'entity_health' in nl or 
                'test_hud' in nl or 
                'image_air_' in nl or
                'image_armor_' in nl or
                'image_health_' in nl or
                'image_hunger_' in nl or
                'image_image_' in nl):
                continue

            raw = zin.read(name)

            # Root shaders are (re)written below; remember source variants, skip the raw copy
            if name.startswith('assets/minecraft/shaders/core/'):
                shader_src.setdefault(os.path.basename(name), raw)
                continue
            if name.startswith('betterhud_26_2/assets/minecraft/shaders/core/'):
                shader_src[os.path.basename(name)] = raw

            problems.extend(validate_font_json(name, raw))
            if name == 'pack.mcmeta':
                try:
                    import json
                    meta = json.loads(raw.decode('utf-8'))
                    if 'pack' in meta:
                        meta['pack']['pack_format'] = 88
                        meta['pack']['min_format'] = 15
                        meta['pack']['max_format'] = 200
                        meta['pack']['supported_formats'] = {"min_inclusive": 15, "max_inclusive": 200}
                    raw = json.dumps(meta, indent=2).encode('utf-8')
                except Exception:
                    pass
            zout.writestr(item, raw)
            count += 1


        # Always place text/rendertype_text shaders at the pack root for MC 26.2
        for ext in ('vsh', 'fsh'):
            raw = shader_src.get(f'text.{ext}')
            if raw is None:
                problems.append(f"shader text.{ext} not found in build.zip; BossBar text will render as tofu")
                continue
            for target in (f'text.{ext}', f'rendertype_text.{ext}'):
                zout.writestr(f'assets/minecraft/shaders/core/{target}', raw)
                count += 1

    buf_data = buf.getvalue()
    with open(zip_dest, 'wb') as f:
        f.write(buf_data)

    for msg in problems:
        print(f"[WARN] {msg}")
    return count, f"Sync complete & packed into {os.path.basename(zip_dest)}"

def compile_all():
    ensure_dirs()
    chars = load_characters()
    dlgs = load_dialogues()
    
    char_count, img_count = compile_portraits_and_betterhud(chars)
    sk_path = generate_skript_dialogues(chars, dlgs)
    
    # Auto-sync client packs & inject root shaders if build.zip exists
    sync_res = None
    if os.path.exists(BETTERHUD_BUILD_ZIP):
        sync_res = sync_client_pack()
    
    return {
        "characters_compiled": char_count,
        "layout_images_count": img_count,
        "skript_path": sk_path,
        "pack_sync": sync_res
    }

if __name__ == "__main__":
    result = compile_all()
    print("Compilation Result:", result)
