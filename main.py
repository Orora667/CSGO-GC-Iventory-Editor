import os
import re
import webbrowser
import urllib.request
import json
from threading import Timer
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Paths
ITEMS_GAME_PATH = r"D:\SteamLibrary\steamapps\common\csgo legacy\csgo\scripts\items\items_game.txt"
INVENTORY_PATH = r"D:\SteamLibrary\steamapps\common\csgo legacy\csgo_gc\inventory.txt"

# Weapon ID mapping
FALLBACK_DEF_INDEX = {
    "weapon_deagle": "1", "weapon_elite": "2", "weapon_fiveseven": "3", "weapon_glock": "4",
    "weapon_ak47": "7", "weapon_aug": "8", "weapon_awp": "9", "weapon_famas": "10",
    "weapon_g3sg1": "11", "weapon_galilar": "13", "weapon_m249": "14", "weapon_m4a1": "16",
    "weapon_mac10": "17", "weapon_p90": "19", "weapon_mp5sd": "23", "weapon_ump45": "24",
    "weapon_xm1014": "25", "weapon_bizon": "26", "weapon_mag7": "27", "weapon_negev": "28",
    "weapon_sawedoff": "29", "weapon_tec9": "30", "weapon_taser": "31", "weapon_hkp2000": "32",
    "weapon_mp7": "33", "weapon_mp9": "34", "weapon_nova": "35", "weapon_p250": "36",
    "weapon_scar20": "38", "weapon_sg556": "39", "weapon_ssg08": "40", "weapon_knifegg": "41", 
    "weapon_knife": "42", "weapon_flashbang": "43", "weapon_hegrenade": "44", "weapon_smokegrenade": "45", 
    "weapon_molotov": "46", "weapon_decoy": "47", "weapon_incgrenade": "48", "weapon_c4": "49", 
    "weapon_healthshot": "57", "weapon_knife_t": "59", "weapon_m4a1_silencer": "60",
    "weapon_usp_silencer": "61", "weapon_cz75a": "63", "weapon_revolver": "64",
    "weapon_bayonet": "500", "weapon_knife_css": "503", "weapon_knife_flip": "505", "weapon_knife_gut": "506",
    "weapon_knife_karambit": "507", "weapon_knife_m9_bayonet": "508", "weapon_knife_tactical": "509",
    "weapon_knife_falchion": "512", "weapon_knife_survival_bowie": "514", "weapon_knife_butterfly": "515",
    "weapon_knife_push": "516", "weapon_knife_cord": "517", "weapon_knife_canis": "518", 
    "weapon_knife_ursus": "519", "weapon_knife_gypsy_jackknife": "520", "weapon_knife_outdoor": "521", 
    "weapon_knife_stiletto": "522", "weapon_knife_widowmaker": "523", "weapon_knife_skeleton": "525",
    "weapon_knife_kukri": "526",
    "studded_bloodhound_gloves": "5027", "t_gloves": "5028", "ct_gloves": "5029", "sporty_gloves": "5030",
    "slick_gloves": "5031", "leather_handwraps": "5032", "motorcycle_gloves": "5033", "specialist_gloves": "5034",
    "studded_hydra_gloves": "5035", "studded_brokenfang_gloves": "4725",
    "weapon_sticker": "1209", "weapon_patch": "4746", "weapon_graffiti": "1348", "weapon_graffiti_unsealed": "1349"
}

real_names_map = {}
real_images_map = {}
CATALOG = {}
ALL_ITEMS_LIST = []
API_SKINS = []
def_index_map = FALLBACK_DEF_INDEX.copy()

def extract_items(data):
    if isinstance(data, list):
        for i in data: yield from extract_items(i)
    elif isinstance(data, dict):
        if 'id' in data and 'name' in data: yield data
        else:
            for v in data.values(): yield from extract_items(v)

def fetch_real_names():
    global API_SKINS, real_names_map, real_images_map, ALL_ITEMS_LIST, CATALOG
    print("Fetching API database...")
    url = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/all.json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode('utf-8'))
        
        for item in extract_items(data):
            api_id = str(item.get('id', '')).lower()
            api_name = item.get('name', '')
            api_image = item.get('image', '')
                
            real_names_map[api_id] = api_name
            if api_image: real_images_map[api_id] = api_image
            if "-" in api_id:
                parts = api_id.split("-")
                if len(parts) > 1 and parts[-1].isdigit():
                    real_names_map[parts[-1]] = api_name
                    if api_image: real_images_map[parts[-1]] = api_image

            # Stickers, patches, graffiti
            if api_id.startswith("sticker-") or api_id.startswith("patch-") or api_id.startswith("graffiti-"):
                kit_id = api_id.split("-")[-1]
                if kit_id.isdigit():
                    if api_id.startswith("sticker-"): 
                        def_idx = "1209"
                        cat = "Stickers"
                        prefix = "sticker"
                    elif api_id.startswith("patch-"): 
                        def_idx = "4746"
                        cat = "Patches"
                        prefix = "patch"
                    else: 
                        def_idx = "1348"
                        cat = "Graffitis"
                        prefix = "graffiti"
                        
                    unique_id = f"{prefix}_{kit_id}"
                    if unique_id not in CATALOG:
                        item_dict = {
                            "id": def_idx, "paint_index": "0", "music_id": "0", "kit_id": kit_id,
                            "name": api_name, "internal_name": api_id, "category": cat, "image": api_image
                        }
                        ALL_ITEMS_LIST.append(item_dict)
                        CATALOG[unique_id] = item_dict
                continue

            # Cases, keys, pins
            if api_id.startswith("crate-") or api_id.startswith("key-") or api_id.startswith("collectible-"):
                def_index = api_id.split("-")[-1]
                if def_index.isdigit() and def_index not in CATALOG:
                    cat = "Other"
                    if "crate-" in api_id: cat = "Cases & Packages"
                    elif "key-" in api_id: cat = "Keys"
                    elif "collectible-" in api_id: cat = "Pins & Coins"
                    
                    item_dict = {
                        "id": def_index, "paint_index": "0", "music_id": "0", "kit_id": "0",
                        "name": api_name, "internal_name": api_id, "category": cat, "image": api_image
                    }
                    ALL_ITEMS_LIST.append(item_dict)
                    CATALOG[def_index] = item_dict
                continue

            # Music kits
            if api_id.startswith("music_kit-"):
                music_id = api_id.split("-")[-1]
                if music_id.isdigit() and f"music_{music_id}" not in CATALOG:
                    music_item = {
                        "id": "1314", "paint_index": "0", "music_id": music_id, "kit_id": "0",
                        "name": api_name, "internal_name": api_id, "category": "Music Kits", "image": api_image
                    }
                    ALL_ITEMS_LIST.append(music_item)
                    CATALOG[f"music_{music_id}"] = music_item
                continue

            # Agents
            if api_id.startswith("agent-"):
                agent_id = api_id.split("-")[-1]
                if agent_id.isdigit() and agent_id not in CATALOG:
                    agent_item = {
                        "id": agent_id, "paint_index": "0", "music_id": "0", "kit_id": "0",
                        "name": api_name, "internal_name": api_id, "category": "Agents", "image": api_image
                    }
                    ALL_ITEMS_LIST.append(agent_item)
                    CATALOG[agent_id] = agent_item
                continue
            
            # Skins and gloves
            if api_id.startswith("skin-") or api_id.startswith("glove-"):
                weapon_data = item.get("weapon", {})
                weapon_name_internal = weapon_data.get("id", "")
                paint_val = item.get("paint_index") or item.get("paint_kit") or "0"
                
                if weapon_name_internal:
                    cat = "Weapons"
                    if "knife" in weapon_name_internal.lower() or "bayonet" in weapon_name_internal.lower() or "karambit" in weapon_name_internal.lower() or "glove" in weapon_name_internal.lower() or "handwraps" in weapon_name_internal.lower() or "bloodhound" in weapon_name_internal.lower():
                        cat = "Knives & Gloves"
                    API_SKINS.append({
                        "api_id": api_id, "name": api_name, "weapon_internal": weapon_name_internal.lower(),
                        "paint_index": str(paint_val), "category": cat, "image": api_image
                    })
                        
        print("API loaded.")
    except Exception as e:
        print(f"Error loading API: {e}")

def parse_items_game():
    global ALL_ITEMS_LIST, CATALOG
    
    # Fallback parser for items_game.txt
    if os.path.exists(ITEMS_GAME_PATH):
        try:
            with open(ITEMS_GAME_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Extract ID to internal_name mapping
                items_section = content.split('"paint_kits"')[0] if '"paint_kits"' in content else content
                pattern = r'"(\d+)"\s*\{[^{}]*?"name"\s*"([^"]+)"'
                matches = re.findall(pattern, items_section)
                
                for item_id, item_name in matches:
                    def_index_map[item_name.lower()] = item_id
                    # Create fallback entry if unknown
                    if item_id not in CATALOG:
                        CATALOG[item_id] = {
                            "id": item_id, "paint_index": "0", "music_id": "0", "kit_id": "0",
                            "name": item_name, "internal_name": item_name, "category": "Other", "image": ""
                        }
        except Exception as e:
            print(f"Error parsing items_game.txt: {e}")

    # Link skins to base weapons
    for skin in API_SKINS:
        weapon_internal = skin["weapon_internal"]
        def_index = def_index_map.get(weapon_internal)
        
        if def_index:
            unique_id = f"{def_index}_{skin['paint_index']}"
            item_dict = {
                "id": def_index,
                "paint_index": skin["paint_index"],
                "music_id": "0",
                "kit_id": "0",
                "name": skin["name"],
                "internal_name": skin["api_id"],
                "category": skin["category"],
                "image": skin.get("image", "")
            }
            ALL_ITEMS_LIST.append(item_dict)
            CATALOG[unique_id] = item_dict

# UI Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CS:GO GC - Inventory Manager</title>
    <style>
        :root {
            --bg-main: #1b2838; --bg-sidebar: #171a21; --bg-card: #202326; --bg-card-hover: #2a475e;
            --border-card: #3c3d3e; --accent: #66c0f4; --text-main: #8f98a0; --text-hover: #ffffff; 
            --btn-green-top: #a4d007; --btn-green-bot: #536904; --danger: #cc3333; 
            --stattrak: #cf6a32; --gold: #d4af37;
        }
        body {
            margin: 0; font-family: 'Motiva Sans', 'Segoe UI', Arial, sans-serif;
            background-color: var(--bg-main); color: var(--text-hover); display: flex; height: 100vh; overflow: hidden;
        }
        
        .sidebar {
            width: 260px; background-color: var(--bg-sidebar); padding: 20px 10px;
            display: flex; flex-direction: column; gap: 4px; z-index: 20; box-shadow: 2px 0 5px rgba(0,0,0,0.5);
            overflow-y: auto;
        }
        .sidebar h2 { 
            color: var(--text-hover); font-size: 16px; margin: 10px 10px 20px 10px;
            text-transform: uppercase; font-weight: normal; letter-spacing: 1px;
            border-bottom: 1px solid #2a475e; padding-bottom: 10px;
        }
        .category-btn {
            background: none; border: none; color: var(--text-main); text-align: left;
            padding: 10px 15px; font-size: 14px; cursor: pointer; transition: 0.2s; border-radius: 2px;
        }
        .category-btn:hover { color: var(--text-hover); background: rgba(102, 192, 244, 0.1); }
        .category-btn.active {
            background-color: var(--bg-card-hover); color: var(--text-hover); border-left: 3px solid var(--accent);
        }
        .stats { margin-top: auto; padding: 20px 10px; font-size: 13px; color: var(--text-main); text-align: center; border-top: 1px solid #2a475e;}
        
        .main-wrapper { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; }
        
        .topbar {
            background-color: rgba(0,0,0,0.2); padding: 0 20px; display: flex; gap: 5px;
            border-bottom: 1px solid rgba(0,0,0,0.5); z-index: 10; height: 50px; align-items: flex-end;
        }
        .nav-btn {
            background: rgba(0,0,0,0.3); color: var(--accent); border: none; padding: 12px 20px;
            cursor: pointer; font-size: 14px; transition: 0.2s; border-top-left-radius: 3px;
            border-top-right-radius: 3px; border-top: 3px solid transparent; text-transform: uppercase; font-weight: bold;
        }
        .nav-btn:hover { background: rgba(0,0,0,0.5); color: var(--text-hover); }
        .nav-btn.active { background: var(--bg-main); color: var(--text-hover); border-top-color: var(--accent); }

        .main-content { padding: 20px; display: flex; flex-direction: column; overflow-y: auto; flex-grow: 1; }
        
        .search-container { display: flex; gap: 10px; margin-bottom: 15px; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 3px;}
        .search-input {
            flex-grow: 1; padding: 10px 15px; background-color: #101214; border: 1px solid #000;
            color: white; border-radius: 3px; font-size: 14px; box-shadow: inset 0 0 4px #000;
        }
        .search-input:focus { outline: none; border-color: var(--accent); }
        
        .options-bar {
            display: flex; gap: 15px; align-items: center; margin-bottom: 20px; padding: 15px;
            background-color: rgba(0,0,0,0.3); border-radius: 3px; flex-wrap: wrap; border: 1px solid #2a475e;
        }
        .opt-group { display: flex; align-items: center; gap: 8px; }
        .opt-label { font-size: 13px; color: var(--text-main); }
        .opt-input {
            padding: 8px; background: #101214; border: 1px solid #000; color: #fff;
            border-radius: 2px; font-size: 13px; width: 100px;
        }
        .opt-input.wide { width: 160px; }
        .st-checkbox { accent-color: var(--stattrak); cursor: pointer; }

        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; align-content: start; }
        
        .card {
            background-color: var(--bg-card); padding: 10px; cursor: pointer;
            transition: all 0.1s; display: flex; flex-direction: column; justify-content: space-between; 
            align-items: center; text-align: center; border: 1px solid var(--border-card); position: relative; min-height: 200px;
        }
        .card:hover { background-color: var(--bg-card-hover); border-color: var(--accent); }
        
        .card-img { width: 100%; height: 100px; object-fit: contain; margin-bottom: 10px; filter: drop-shadow(0 0 5px rgba(0,0,0,0.8)); }
        .card .id-badge { font-size: 10px; color: var(--text-main); margin-bottom: 5px; background: rgba(0,0,0,0.5); padding: 3px 6px; border-radius: 3px;}
        .card .name { font-size: 13px; color: #d2d2d2; word-break: break-word;}
        .card:hover .name { color: #ffffff; }
        .card .custom-name { font-size: 12px; color: var(--gold); font-style: italic; margin-top: 5px;}
        .card .float-pattern { font-size: 11px; color: #888; margin-top: 5px;}
        
        .inventory-card { border-top: 3px solid var(--accent); }
        .st-badge { position: absolute; top: 5px; right: 5px; color: var(--stattrak); font-size: 11px; font-weight: bold; text-shadow: 1px 1px 2px #000;}
        
        .action-btn {
            margin-top: 15px; padding: 8px; border-radius: 2px; cursor: pointer; 
            font-size: 13px; border: none; width: 100%; font-weight: bold; transition: 0.2s;
        }
        .add-btn { background: linear-gradient(to bottom, var(--btn-green-top) 5%, var(--btn-green-bot) 95%); color: #d2efa9; }
        .add-btn:hover { background: linear-gradient(to bottom, #b9eb0a 5%, #6a8605 95%); color: white; }
        
        .delete-btn { background: rgba(204, 51, 51, 0.1); border: 1px solid #cc3333; color: #cc3333; }
        .delete-btn:hover { background: #cc3333; color: white; }
        
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: #101214; }
        ::-webkit-scrollbar-thumb { background-color: #3c3d3e; border: 1px solid #101214; }
        ::-webkit-scrollbar-thumb:hover { background-color: #4a4b4c; }

        #toast {
            visibility: hidden; min-width: 250px; background-color: #4c5b61; color: #fff; text-align: center; padding: 15px; position: fixed; border: 1px solid var(--accent);
            z-index: 100; right: 20px; bottom: 20px; font-size: 14px; box-shadow: 0 4px 8px rgba(0,0,0,0.5);
        }
        #toast.show { visibility: visible; animation: fadein 0.2s, fadeout 0.2s 2.8s forwards; }
        @keyframes fadein { from {bottom: 0; opacity: 0;} to {bottom: 20px; opacity: 1;} }
        @keyframes fadeout { from {opacity: 1;} to {opacity: 0;} }
    </style>
</head>
<body>

    <div class="sidebar">
        <h2>Filters</h2>
        <button class="category-btn active" onclick="filterCategory('All')">All Items</button>
        <button class="category-btn" onclick="filterCategory('Weapons')">Weapons</button>
        <button class="category-btn" onclick="filterCategory('Knives & Gloves')">Knives & Gloves</button>
        <button class="category-btn" onclick="filterCategory('Stickers')">Stickers</button>
        <button class="category-btn" onclick="filterCategory('Patches')">Patches</button>
        <button class="category-btn" onclick="filterCategory('Graffitis')">Graffitis</button>
        <button class="category-btn" onclick="filterCategory('Agents')">Agents</button>
        <button class="category-btn" onclick="filterCategory('Music Kits')">Music Kits</button>
        <button class="category-btn" onclick="filterCategory('Cases & Packages')">Cases & Packages</button>
        <button class="category-btn" onclick="filterCategory('Keys')">Keys</button>
        <button class="category-btn" onclick="filterCategory('Pins & Coins')">Pins & Coins</button>
        <button class="category-btn" onclick="filterCategory('Other')">Other</button>
        <div class="stats" id="statsCounter">Loading...</div>
    </div>

    <div class="main-wrapper">
        <div class="topbar">
            <button class="nav-btn active" id="btn-shop" onclick="switchView('shop')">Store & Generator</button>
            <button class="nav-btn" id="btn-inv" onclick="switchView('inventory')">My Inventory</button>
        </div>

        <div class="main-content">
            <div class="search-container">
                <input type="text" id="searchInput" class="search-input" placeholder="Search (e.g. dreams nightmare, ibp holo, awp)..." onkeyup="searchItems()">
            </div>
            
            <div class="options-bar" id="shopOptions">
                <div class="opt-group">
                    <span class="opt-label">Qty:</span>
                    <input type="number" id="itemQty" class="opt-input" value="1" min="1" max="500" style="width: 60px;">
                </div>
                <div class="opt-group">
                    <span class="opt-label" style="color:var(--gold);">Name Tag:</span>
                    <input type="text" id="customNameInput" class="opt-input wide" placeholder="e.g. 502 Goldz" maxlength="40">
                </div>
                <div class="opt-group">
                    <span class="opt-label">Pattern (7):</span>
                    <input type="number" id="patternInput" class="opt-input" placeholder="0-1000">
                </div>
                <div class="opt-group">
                    <span class="opt-label">Float (8):</span>
                    <input type="number" id="floatInput" class="opt-input" placeholder="e.g. 0.1295" step="0.0001">
                </div>
                <div class="opt-group" style="margin-left: 10px;">
                    <label class="opt-label" style="color: var(--stattrak); font-weight:bold; cursor:pointer;">
                        <input type="checkbox" id="chkStatTrak" class="st-checkbox" onchange="toggleStKills()"> StatTrak™
                    </label>
                    <input type="number" id="stKillsInput" class="opt-input" placeholder="Kills" style="display: none; width: 70px;" min="0">
                </div>
            </div>

            <div class="grid" id="itemGrid"></div>
        </div>
    </div>

    <div id="toast">Operation successful!</div>

    <script>
        let allItems = [];
        let myInventory = [];
        let currentCategory = 'All';
        let currentView = 'shop';
        let activeItemData = null;
        
        const FALLBACK_IMG = "https://community.cloudflare.steamstatic.com/public/images/economy/appIconFallback/730.png";

        fetch('/api/items')
            .then(response => response.json())
            .then(data => {
                allItems = data;
                switchView('shop');
            });

        function switchView(view) {
            currentView = view;
            document.getElementById('btn-shop').classList.toggle('active', view === 'shop');
            document.getElementById('btn-inv').classList.toggle('active', view === 'inventory');
            
            if(view === 'shop') {
                document.getElementById('searchInput').placeholder = "Search for items...";
                document.getElementById('shopOptions').style.display = 'flex';
                searchItems();
            } else {
                document.getElementById('searchInput').placeholder = "Search in your inventory...";
                document.getElementById('shopOptions').style.display = 'none';
                loadInventory();
            }
        }

        function filterCategory(category) {
            currentCategory = category;
            document.querySelectorAll('.category-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            searchItems();
        }

        function toggleStKills() {
            const chk = document.getElementById('chkStatTrak');
            const stInput = document.getElementById('stKillsInput');
            stInput.style.display = chk.checked ? 'block' : 'none';
            if(chk.checked && !stInput.value) stInput.value = 0;
        }

        function searchItems() {
            let query = document.getElementById('searchInput').value.toLowerCase().trim();
            query = query.replace(/&/g, 'and').replace(/\ban\b/g, 'and');
            const searchTerms = query.split(/\s+/).filter(word => word.length > 0);

            if(currentView === 'shop') {
                const filtered = allItems.filter(item => {
                    const matchCat = (currentCategory === 'All' || item.category === currentCategory);
                    let searchPool = (item.name + " " + item.internal_name + " " + item.id).toLowerCase();
                    searchPool = searchPool.replace(/&/g, 'and');
                    
                    if (item.category === 'Cases & Packages') searchPool += " case crate package box bundle capsule";
                    if (item.category === 'Music Kits') searchPool += " music kit sound";
                    if (item.category === 'Agents') searchPool += " agent character skin";
                    if (item.category === 'Stickers') searchPool += " sticker autocollant";

                    const matchSearch = searchTerms.every(term => searchPool.includes(term));
                    return matchCat && matchSearch;
                });
                renderShopItems(filtered);
                document.getElementById('statsCounter').innerText = "Found " + filtered.length + " items";
            } else {
                filterAndRenderInventory(searchTerms);
            }
        }

        function renderShopItems(items) {
            const grid = document.getElementById('itemGrid');
            grid.innerHTML = '';
            
            const displayItems = items.slice(0, 1000);

            displayItems.forEach(item => {
                const card = document.createElement('div');
                card.className = 'card';
                
                let labelInfo = item.paint_index && item.paint_index !== "0" ? `DEF: ${item.id} | PK: ${item.paint_index}` : `DEF: ${item.id}`;
                if (item.music_id && item.music_id !== "0") labelInfo = `DEF: ${item.id} | MUS: ${item.music_id}`;
                if (item.kit_id && item.kit_id !== "0") labelInfo = `DEF: ${item.id} | KIT: ${item.kit_id}`;
                
                let imgSrc = item.image ? item.image : FALLBACK_IMG;

                card.innerHTML = `
                    <div style="width:100%; text-align:center;">
                        <img src="${imgSrc}" class="card-img" loading="lazy" alt="Image">
                        <div class="id-badge">${labelInfo}</div>
                        <div class="name">${item.name}</div>
                    </div>
                    <button class="action-btn add-btn" onclick="addItem(this, '${item.id}', '${item.paint_index || "0"}', '${item.music_id || "0"}', '${item.kit_id || "0"}', '${item.name.replace(/'/g, "\\'")}')">Add to Inventory</button>
                `;
                grid.appendChild(card);
            });
        }

        function loadInventory() {
            fetch('/api/inventory')
                .then(res => res.json())
                .then(data => {
                    myInventory = data;
                    searchItems();
                });
        }

        function filterAndRenderInventory(searchTerms) {
            const filtered = myInventory.filter(item => {
                const matchCat = (currentCategory === 'All' || item.category === currentCategory);
                let searchPool = (item.name + " " + item.def_index + " " + (item.custom_name||"")).toLowerCase();
                searchPool = searchPool.replace(/&/g, 'and');
                
                const matchSearch = searchTerms.every(term => searchPool.includes(term));
                return matchCat && matchSearch;
            });
            
            const grid = document.getElementById('itemGrid');
            grid.innerHTML = '';
            document.getElementById('statsCounter').innerText = filtered.length + " items owned";

            filtered.forEach(item => {
                const card = document.createElement('div');
                card.className = 'card inventory-card';
                let stBadge = item.is_stattrak ? `<div class="st-badge">ST™ (${item.st_kills})</div>` : '';
                
                let pkStr = "";
                if(item.paint_index && item.paint_index !== "0") pkStr = ` | PK: ${item.paint_index}`;
                if(item.kit_id && item.kit_id !== "0") pkStr = ` | KIT: ${item.kit_id}`;
                
                let customNameHtml = item.custom_name ? `<div class="custom-name">"${item.custom_name}"</div>` : '';
                
                let floatPatternHtml = "";
                if (item.pattern !== null || item.wear !== null) {
                    let p = item.pattern !== null ? `P: ${item.pattern}` : "";
                    let w = item.wear !== null ? `F: ${item.wear}` : "";
                    floatPatternHtml = `<div class="float-pattern">${p} ${w}</div>`;
                }

                let imgSrc = item.image ? item.image : FALLBACK_IMG;

                card.innerHTML = `
                    <div style="width:100%; text-align:center;">
                        ${stBadge}
                        <img src="${imgSrc}" class="card-img" loading="lazy" alt="Image">
                        <div class="id-badge">INV: ${item.inv_id} | DEF: ${item.def_index}${pkStr}</div>
                        <div class="name">${item.name}</div>
                        ${customNameHtml}
                        ${floatPatternHtml}
                    </div>
                    <button class="action-btn delete-btn" onclick="deleteItem('${item.inv_id}', '${item.name.replace(/'/g, "\\'")}')">Remove Item</button>
                `;
                grid.appendChild(card);
            });
        }

        function showToast(message, isError=false) {
            const toast = document.getElementById('toast');
            toast.innerText = message;
            toast.style.borderColor = isError ? "#cc3333" : "#66c0f4";
            toast.className = "show";
            setTimeout(() => { toast.className = toast.className.replace("show", ""); }, 3000);
        }

        function addItem(btn, id, paint_index, music_id, kit_id, name) {
            const quantity = parseInt(document.getElementById('itemQty').value) || 1;
            const customName = document.getElementById('customNameInput').value.trim();
            const pattern = document.getElementById('patternInput').value.trim();
            const wear = document.getElementById('floatInput').value.trim();
            
            const isStatTrak = document.getElementById('chkStatTrak').checked;
            const stKills = isStatTrak ? parseInt(document.getElementById('stKillsInput').value) || 0 : 0;
            
            // Update button state
            let oldText = btn.innerText;
            btn.innerText = "Adding...";
            
            fetch('/api/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    id: id, 
                    paint_index: paint_index,
                    music_id: music_id,
                    kit_id: kit_id,
                    name: name, 
                    quantity: quantity,
                    custom_name: customName,
                    pattern: pattern,
                    wear: wear,
                    stattrak: isStatTrak,
                    st_kills: stKills
                })
            })
            .then(res => res.json())
            .then(data => {
                btn.innerText = oldText;
                if(data.success) {
                    let msg = quantity > 1 ? `Added ${quantity}x ${name}` : `Added ${name}`;
                    showToast(msg);
                } else {
                    alert("Error adding item: " + data.error);
                }
            });
        }

        function deleteItem(inv_id, name) {
            if(confirm("Are you sure you want to delete:\\n" + name)) {
                fetch('/api/inventory/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ inv_id: inv_id })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        showToast("Removed " + name, true);
                        loadInventory();
                    } else {
                        alert("Error: " + data.error);
                    }
                });
            }
        }
    </script>
</body>
</html>
"""

# Routes

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/items')
def get_items():
    return jsonify(ALL_ITEMS_LIST)

@app.route('/api/add', methods=['POST'])
def add_item():
    data = request.json
    def_index = data.get('id')
    paint_index = data.get('paint_index', "0")
    music_id = data.get('music_id', "0")
    kit_id = data.get('kit_id', "0")
    quantity = int(data.get('quantity', 1))
    
    custom_name = data.get('custom_name', "")
    pattern = data.get('pattern', "")
    wear = data.get('wear', "")
    
    stattrak = data.get('stattrak', False)
    st_kills = int(data.get('st_kills', 0))
    
    if quantity < 1: quantity = 1
    if quantity > 500: quantity = 500 

    if not os.path.exists(INVENTORY_PATH): return jsonify({"success": False, "error": "File not found"})
    try:
        with open(INVENTORY_PATH, 'r', encoding='utf-8') as f: lines = f.readlines()
        last_idx = 0
        for line in lines:
            m = re.search(r'^\s*"(\d+)"\s*$', line)
            if m: last_idx = max(last_idx, int(m.group(1)))
        
        insert_idx = -1
        for i, line in enumerate(lines):
            if '"default_equips"' in line:
                for j in range(i-1, -1, -1):
                    if '}' in lines[j]:
                        insert_idx = j
                        break
                break
        if insert_idx == -1: 
            for i in range(len(lines)-1, -1, -1):
                if '}' in lines[i]:
                    insert_idx = i
                    break

        attr_block = ""
        attrs = []
        if paint_index and paint_index != "0":
            attrs.append(f"\t\t\t\"6\"\t\t\"{paint_index}.000000\"")
        if pattern:
            pattern_val = f"{int(pattern)}.000000" if pattern.isdigit() else pattern
            attrs.append(f"\t\t\t\"7\"\t\t\"{pattern_val}\"")
        if wear:
            attrs.append(f"\t\t\t\"8\"\t\t\"{wear}\"")
            
        if kit_id and kit_id != "0":
            # 137: unapplied stickers, patches, graffitis
            attrs.append(f"\t\t\t\"137\"\t\t\"{kit_id}.000000\"")
            
        if music_id and music_id != "0":
            attrs.append(f"\t\t\t\"166\"\t\t\"{music_id}.000000\"")
        if stattrak:
            attrs.append(f"\t\t\t\"80\"\t\t\"{st_kills}.000000\"")
            
        if attrs:
            attr_str = "\n".join(attrs)
            attr_block = f"\n\t\t\"attributes\"\n\t\t{{\n{attr_str}\n\t\t}}"

        custom_name_str = f"\n\t\t\"custom_name\"\t\t\"{custom_name}\"" if custom_name else ""

        new_items_str = ""
        for _ in range(quantity):
            last_idx += 1
            new_idx = last_idx
            new_items_str += f"\t\"{new_idx}\"\n\t{{\n\t\t\"inventory\"\t\t\"{new_idx}\"\n\t\t\"def_index\"\t\t\"{def_index}\"\n\t\t\"level\"\t\t\"1\"\n\t\t\"quality\"\t\t\"3\"\n\t\t\"flags\"\t\t\"0\"\n\t\t\"origin\"\t\t\"24\"{custom_name_str}\n\t\t\"in_use\"\t\t\"0\"\n\t\t\"rarity\"\t\t\"6\"{attr_block}\n\t}}\n"

        lines.insert(insert_idx, new_items_str)
        with open(INVENTORY_PATH, 'w', encoding='utf-8') as f: f.writelines(lines)
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "error": str(e)})


@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    if not os.path.exists(INVENTORY_PATH): return jsonify([])
    inv_items = []
    try:
        with open(INVENTORY_PATH, 'r', encoding='utf-8') as f: lines = f.readlines()
        current_inv_id = None
        current_def_idx = None
        current_paint_idx = "0"
        current_music_id = "0"
        current_kit_id = "0"
        current_custom_name = None
        current_pattern = None
        current_wear = None
        is_stattrak = False
        st_kills = 0
        brace_level = 0
        in_item_block = False
        
        for line in lines:
            if '}' in line:
                brace_level -= line.count('}')
                if brace_level == 1 and in_item_block: 
                    if current_inv_id and current_def_idx:
                        unique_id = current_def_idx
                        if current_music_id != "0":
                            unique_id = f"music_{current_music_id}"
                        elif current_kit_id != "0":
                            if current_def_idx == "1209": unique_id = f"sticker_{current_kit_id}"
                            elif current_def_idx == "4746": unique_id = f"patch_{current_kit_id}"
                            elif current_def_idx in ["1348", "1349"]: unique_id = f"graffiti_{current_kit_id}"
                        elif current_paint_idx != "0":
                            unique_id = f"{current_def_idx}_{current_paint_idx}"
                            
                        item_info = CATALOG.get(unique_id) or CATALOG.get(current_def_idx) or {}
                        
                        inv_items.append({
                            "inv_id": current_inv_id,
                            "def_index": current_def_idx,
                            "paint_index": current_paint_idx,
                            "music_id": current_music_id,
                            "kit_id": current_kit_id,
                            "custom_name": current_custom_name,
                            "pattern": current_pattern,
                            "wear": current_wear,
                            "name": item_info.get('name', f"Unknown Item ({current_def_idx})"),
                            "category": item_info.get('category', 'Other'),
                            "image": item_info.get('image', ''),
                            "is_stattrak": is_stattrak,
                            "st_kills": st_kills
                        })
                    in_item_block = False
                    current_inv_id = None
                    current_def_idx = None
                    current_paint_idx = "0"
                    current_music_id = "0"
                    current_kit_id = "0"
                    current_custom_name = None
                    current_pattern = None
                    current_wear = None
                    is_stattrak = False
                    st_kills = 0

            if brace_level == 1 and not in_item_block:
                m = re.match(r'^\s*"(\d+)"\s*$', line)
                if m:
                    current_inv_id = m.group(1)
                    in_item_block = True

            if '{' in line:
                brace_level += line.count('{')
                
            if in_item_block:
                if current_def_idx is None:
                    m = re.search(r'"def_index"\s*"(\d+)"', line)
                    if m: current_def_idx = m.group(1)
                
                c_name_match = re.search(r'"custom_name"\s*"([^"]+)"', line)
                if c_name_match: current_custom_name = c_name_match.group(1)

                pk_match = re.search(r'"6"\s*"([0-9.]+)"', line)
                if pk_match: current_paint_idx = str(int(float(pk_match.group(1))))

                pattern_match = re.search(r'"7"\s*"([0-9.]+)"', line)
                if pattern_match: current_pattern = str(int(float(pattern_match.group(1))))

                wear_match = re.search(r'"8"\s*"([0-9.]+)"', line)
                if wear_match: current_wear = wear_match.group(1)

                kit_match = re.search(r'"137"\s*"([0-9.]+)"', line)
                if kit_match: current_kit_id = str(int(float(kit_match.group(1))))

                mk_match = re.search(r'"166"\s*"([0-9.]+)"', line)
                if mk_match: current_music_id = str(int(float(mk_match.group(1))))

                st_match = re.search(r'"80"\s*"([0-9.]+)"', line)
                if st_match:
                    is_stattrak = True
                    st_kills = int(float(st_match.group(1)))

    except: pass
    return jsonify(inv_items)


@app.route('/api/inventory/delete', methods=['POST'])
def delete_item():
    target_id = str(request.json.get('inv_id'))
    if not os.path.exists(INVENTORY_PATH): return jsonify({"success": False, "error": "File not found"})
    
    try:
        with open(INVENTORY_PATH, 'r', encoding='utf-8') as f: lines = f.readlines()
            
        new_lines = []
        skip_mode = False
        bracket_count = 0
        seen_first_bracket = False
        
        for line in lines:
            if skip_mode:
                if '{' in line:
                    bracket_count += line.count('{')
                    seen_first_bracket = True
                if '}' in line:
                    bracket_count -= line.count('}')
                if seen_first_bracket and bracket_count <= 0:
                    skip_mode = False 
                continue

            match = re.match(r'^\s*"(\d+)"\s*$', line)
            if match and match.group(1) == target_id:
                skip_mode = True 
                bracket_count = 0
                seen_first_bracket = False
                if '{' in line:
                    bracket_count += line.count('{')
                    seen_first_bracket = True
                continue

            new_lines.append(line)
            
        with open(INVENTORY_PATH, 'w', encoding='utf-8') as f: f.writelines(new_lines)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def open_browser(): webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    fetch_real_names()
    parse_items_game()
    print("Starting server...")
    Timer(1, open_browser).start()
    app.run(port=5000, debug=False)
