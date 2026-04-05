> **Important notice:** This is meant to be used alongside [CSGO GC](https://github.com/mikkokko/csgo_gc).
> It also uses the item database API from [ByMykel](https://github.com/ByMykel/CSGO-API).
> Showcase / help discord : https://discord.gg/VCJRHqwt

# CSGO-GC-Iventory-Editor
A useful webapp built with Flask to add any CS:GO Legacy items to your inventory using the custom Game Coordinator (`csgo_gc`). 
You can edit just about anything!
 
# INSTALLATION 
1. Drop `main.py` in the root folder (where your `csgo.exe` is located).
2. Open a command prompt (cmd) in that folder and enter: `python main.py`

**Crucial Step:** Before running the script, open `main.py` in a text editor and replace these lines with your actual Steam paths:

```python
ITEMS_GAME_PATH = r"D:\SteamLibrary\steamapps\common\csgo legacy\csgo\scripts\items\items_game.txt" # <- where your items_game.txt is
INVENTORY_PATH = r"D:\SteamLibrary\steamapps\common\csgo legacy\csgo_gc\inventory.txt" # <- where your inventory.txt is
```
*(For example, these are the paths for my D: drive).*

⚠️ **I strongly recommend backing up your `inventory.txt` before making any changes!**

# What this does ?
It can read your `inventory.txt` file and let you easily add items like crates, knives with custom floats or patterns, and StatTrak™ items with a custom kill count.

# Is it safe to use ?
It is, as long as you use the GC patch and open the game with the `-insecure` and `-steam` launch options.

# Can I add these skins in my legit CS2?
Nope, these generated skins are exclusively for your local GC inventory on CS:GO Legacy.

# What is CS:GO Legacy ? 
It is the last version of CS:GO downloadable on Steam : https://store.steampowered.com/app/4465480/CounterStrikeGlobal_Offensive/
