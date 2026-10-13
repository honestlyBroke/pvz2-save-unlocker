"""Unlock every plant in a PvZ2 (ROW) save file.

Usage:  python pvz2_unlock_plants.py pp.dat [--shop-only] [--max-levels]
        --shop-only:  only the shop plants you cannot buy with gems
        --max-levels: also set every owned plant to its level cap and max mastery
Writes pp.dat in place and keeps the original as pp.dat.bak.

Plant tables live in plant_data.py; regenerate them after a game update with
update_plant_data.py.
"""
import shutil
import sys

import pvz2_rton as rton
from plant_data import DEFAULT_LEVEL_CAP, LEVEL_CAP, MASTERY_CAP, PLANTS, SHOP_ONLY


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
            top = LEVEL_CAP.get(i, DEFAULT_LEVEL_CAP) - 1
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
