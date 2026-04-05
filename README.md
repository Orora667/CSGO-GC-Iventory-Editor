# Important notice : This is meant to be used alongside CSGO GC
https://github.com/mikkokko/csgo_gc

it also uses the api from ByMykel:
https://github.com/ByMykel/CSGO-API

# CSGO-GC-Iventory-Editor
A useful webapp built with flask to add any CSGO Legacy items in your inventory with csgo gc.
you can edit about anything
 
# INSTALLATION 
 Drop the main.py in the root (where the csgo.exe is) and open a cmd and enter "python main.py"
 it is important to replace theses lines :

ITEMS_GAME_PATH = r"D:\SteamLibrary\steamapps\common\csgo legacy\csgo\scripts\items\items_game.txt" <- where your items_game.txt is
INVENTORY_PATH = r"D:\SteamLibrary\steamapps\common\csgo legacy\csgo_gc\inventory.txt" <- where your inventory is

 For exemple for me in my D drive

 I strongly Recommend Backing up your inventory before doing any changes

 # What this does ?
 It can read your inventory.exe and add stuff like crates, knife with custom floats or patterns and stattrak with custom number

# Is it safe to use ?
It is, as long as you use the GC patch and open the game with -insecure -steam

# can i add these skins in my legits cs2 ?
Nope, the skins are only for your GC inventory on csgo legacy?

# What is csgo Legacy ? 
It is the last version of CSGO downloadable on Steam : https://store.steampowered.com/app/4465480/CounterStrikeGlobal_Offensive/
