"""Unlock every plant in a PvZ2 (13.5.1 ROW) save file.

Usage:  python pvz2_unlock_plants.py pp.dat [--shop-only] [--max-levels]
        --shop-only:  only the 21 shop plants you cannot buy with gems
        --max-levels: also set every owned plant to its level cap and max mastery
Writes pp.dat in place and keeps the original as pp.dat.bak.

Plant IDs come from packages/PlantTypes.rton in the 13.5.1 OBB
(every PlantType* object without HideInPlantViewers).
"""
import shutil
import sys

import pvz2_rton as rton

# ponytail: hardcoded for 13.5.1; regenerate from the OBB when the game adds plants
PLANTS = {
    1: 'sunflower', 2: 'peashooter', 3: 'wallnut', 4: 'tallnut', 5: 'bonkchoy',
    6: 'cabbagepult', 7: 'melonpult', 8: 'cherry_bomb', 9: 'coconutcannon',
    10: 'gravebuster', 11: 'iceburg', 12: 'laser_bean', 13: 'potatomine',
    14: 'repeater', 15: 'snapdragon', 16: 'spikeweed', 17: 'threepeater',
    18: 'torchwood', 19: 'kernelpult', 20: 'springbean', 21: 'snowpea', 22: 'chilibean',
    23: 'splitpea', 24: 'lightningreed', 25: 'peapod', 26: 'magnifyinggrass',
    27: 'bloomerang', 28: 'holonut', 29: 'empea', 30: 'blover', 31: 'starfruit',
    32: 'imitater', 33: 'jalapeno', 34: 'wintermelon', 35: 'twinsunflower',
    37: 'spikerock', 38: 'powerlily', 39: 'squash', 40: 'citron', 41: 'powerplant',
    42: 'sunshroom', 44: 'puffshroom', 50: 'sunbean', 51: 'magnetshroom',
    52: 'hypnoshroom', 53: 'firepeashooter', 54: 'peanut', 55: 'fumeshroom',
    58: 'lilypad', 59: 'bowlingbulb', 60: 'banana', 61: 'tanglekelp',
    62: 'homingthistle', 63: 'chomper', 64: 'guacodile', 65: 'ghostpepper',
    66: 'sweetpotato', 67: 'sapfling', 68: 'hurrikale', 69: 'xshot', 70: 'chardguard',
    71: 'pepperpult', 72: 'hotpotato', 74: 'stunion', 76: 'dandelion', 78: 'redstinger',
    79: 'goldleaf', 81: 'akee', 82: 'lavaguava', 83: 'toadstool', 84: 'endurian',
    85: 'stallia', 86: 'strawburst', 87: 'cactus', 88: 'phatbeet', 89: 'thymewarp',
    90: 'celerystalker', 91: 'electricblueberry', 92: 'sporeshroom', 93: 'garlic',
    94: 'intensivecarrot', 95: 'jackolantern', 96: 'primalpeashooter', 97: 'grapeshot',
    98: 'primalwallnut', 99: 'coldsnapdragon', 100: 'perfumeshroom',
    101: 'primalsunflower', 102: 'primalpotatomine', 103: 'shrinkingviolet',
    104: 'moonflower', 105: 'nightshade', 106: 'shadowshroom', 107: 'bloominghearts',
    108: 'escaperoot', 109: 'grimrose', 110: 'dusklobber', 111: 'goldbloom',
    112: 'electriccurrant', 113: 'aloe', 114: 'wasabiwhip', 115: 'explodeonut',
    116: 'kiwibeast', 117: 'applemortar', 118: 'bombegranate', 119: 'missiletoe',
    120: 'parsnip', 121: 'witchhazel', 122: 'hotdate', 123: 'caulipower',
    124: 'solartomato', 125: 'electricpeashooter', 126: 'hollyknight', 129: 'filamint',
    130: 'peppermint', 131: 'wintermint', 132: 'enlightenmint', 133: 'reinforcemint',
    134: 'bombardmint', 135: 'ailmint', 136: 'enchantmint', 137: 'containmint',
    138: 'enforcemint', 139: 'armamint', 140: 'concealmint', 141: 'spearmint',
    142: 'shadowpeashooter', 143: 'poisonpeashooter', 144: 'slingpea',
    145: 'appeasemint', 147: 'snappea', 149: 'zoybeanpod', 150: 'dazeychain',
    151: 'blastberry', 152: 'electricitea', 153: 'imppear', 154: 'pokra',
    155: 'icebloom', 156: 'pyrevine', 157: 'pumpkin', 158: 'ultomato',
    159: 'dartichoke', 160: 'gumnut', 161: 'shinevine', 162: 'tumbleweed',
    163: 'puffball', 164: 'olivepit', 165: 'murkadamia', 166: 'explodeovine',
    167: 'turkeypult', 168: 'headbutter', 169: 'boingsetta', 170: 'stickybombrice',
    171: 'hocus', 172: 'gloomvine', 173: 'draftodil', 174: 'boomflower', 175: 'pvine',
    176: 'inferno', 177: 'solarsage', 178: 'powervine', 179: 'noctarine',
    181: 'heathseeker', 182: 'iceweed', 183: 'tigergrass', 184: 'teleportatomine',
    185: 'buttercup', 186: 'blockoli', 187: 'bramblebush', 188: 'rhubarbarian',
    189: 'megagatling', 190: 'levitater', 191: 'tombtangler', 192: 'vamporcini',
    193: 'meteorflower', 194: 'chillypepper', 195: 'waterrabbit', 196: 'buzzbutton',
    197: 'boomberry', 198: 'nightcap', 199: 'seaflora', 200: 'maybee',
    201: 'bamboospartan', 202: 'scaredyshroom', 203: 'sundewtangler', 204: 'beansprout',
    205: 'cranjelly', 206: 'iceshroom', 207: 'buduhboom', 208: 'dragonbruit',
    210: 'electricpeel', 211: 'seashroom', 212: 'guardshroom', 214: 'aquavine',
    215: 'mangofier', 216: 'doomshroom', 217: 'blastspinner', 219: 'blazeleaf',
    220: 'frostbonnet', 221: 'znakelily', 222: 'sweetheartsnare', 223: 'hammeruit',
    224: 'cornfetti', 225: 'seashooter', 226: 'devourbloom', 227: 'sourshot',
    228: 'brainstem', 229: 'lemonaid', 230: 'rose', 231: 'blazingknight', 232: 'sakura',
    233: 'voltsnapdragon', 234: 'thornwhip', 235: 'pyroak', 236: 'cactalog',
    237: 'baneberry',
}


# Shop plants with no gem price (cash and/or mints only): 21 of the 59 plants in
# StoreProductProps "Plant Unlock" in the 13.5.1 OBB. The other 38 are gem-buyable.
SHOP_ONLY = {86, 87, 108, 115, 118, 122, 124,  # cash only
             129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 145}  # mints


# LevelCap from packages/PlantLevels.rton (13.5.1); every other plant caps at 10.
LEVEL_CAP = {2: 20, 3: 20, 5: 20, 6: 20, 7: 15, 11: 20, 12: 15, 13: 20, 14: 20, 17: 20,
             19: 15, 20: 15, 23: 20, 24: 15, 25: 15, 27: 20, 32: 1, 44: 20, 55: 15,
             64: 15, 71: 15, 88: 15, 92: 15, 96: 15, 98: 15}
MASTERY_CAP = 200  # PlantMastery.rton LevelCap, same for every plant


def unlock(data, ids=PLANTS, max_levels=False):
    """Return (new pp.dat bytes, names of plants added, number of plants levelled)."""
    root = rton.decode(data)
    info = next((o['objdata'] for o in root['objects'] if o.get('objclass') == 'PlayerInfo'), None)
    if info is None:
        sys.exit('Save has no player profile yet: play past the first level, close the game, retry.')
    owned = info['p']
    have = set(owned)
    added = [i for i in ids if i not in have]
    owned += [rton.RInt(i, 0x24) for i in added]  # 0x24 = uvarint, same as the game writes

    levelled = 0
    if max_levels:
        # plis entry: p = plant id, l = upgrades done (level - 1; -1 = untouched), x = seed packets, m = mastery
        plis = info.setdefault('plis', [])
        by_id = {e['p']: e for e in plis}
        for i in owned:
            if i not in PLANTS:
                continue
            top = LEVEL_CAP.get(i, 10) - 1
            e = by_id.get(i)
            if e is None:
                plis.append({'p': rton.RInt(i, 0x24), 'l': rton.RInt(top, 0x24),
                             'x': rton.RInt(0, 0x21), 'm': rton.RInt(MASTERY_CAP, 0x24)})
            elif e['l'] != top or e.get('m') != MASTERY_CAP:
                e['l'] = rton.RInt(top, 0x24)
                e['m'] = rton.RInt(MASTERY_CAP, 0x24)
            else:
                continue
            levelled += 1
    return rton.encode(root), [PLANTS[i] for i in added], levelled


def main(path, shop_only=False, max_levels=False):
    data = open(path, 'rb').read()
    if data[:4] != b'RTON':
        sys.exit('pp.dat is not plain RTON (encrypted or wrong file); nothing changed.')
    new, added, levelled = unlock(data, SHOP_ONLY if shop_only else PLANTS, max_levels)
    if not added and not levelled:
        print('Nothing to change.')
        return
    shutil.copyfile(path, path + '.bak')
    open(path, 'wb').write(new)
    if added:
        print(f'Unlocked {len(added)} plants: {", ".join(added)}')
    if max_levels:
        print(f'Maxed level and mastery on {levelled} plants.')
    print(f'Backup: {path}.bak')


if __name__ == '__main__':
    flags = {'--shop-only', '--max-levels'}
    args = [a for a in sys.argv[1:] if a not in flags]
    if len(args) != 1:
        sys.exit(__doc__)
    main(args[0], '--shop-only' in sys.argv, '--max-levels' in sys.argv)
