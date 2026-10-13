"""Self-check: python test_pvz2_unlock.py path/to/any/pp.dat"""
import sys

import pvz2_rton as rton
from pvz2_unlock_plants import PLANTS, unlock

src = open(sys.argv[1], 'rb').read()
assert rton.encode(rton.decode(src)) == src, 'RTON round-trip is not byte-exact'

new, added, _ = unlock(src)
before = rton.decode(src)['objects'][0]['objdata']
after = rton.decode(new)['objects'][0]['objdata']
assert set(PLANTS) <= set(after['p'])
assert set(after['p']) - set(before['p']) == {i for i, n in PLANTS.items() if n in added}
assert {k: v for k, v in after.items() if k != 'p'} == {k: v for k, v in before.items() if k != 'p'}
assert unlock(new)[1] == [], 'second run should be a no-op'
print(f'ok: {len(added)} added, {len(after["p"])} owned')

from pvz2_unlock_plants import LEVEL_CAP, MASTERY_CAP
maxed, _, n = unlock(src, max_levels=True)
plis = {e['p']: e for e in rton.decode(maxed)['objects'][0]['objdata']['plis']}
assert all(plis[i]['l'] == LEVEL_CAP.get(i, 10) - 1 for i in PLANTS), 'a plant is not at its cap'
assert all(plis[i]['m'] == MASTERY_CAP for i in PLANTS), 'a plant is not at max mastery'
assert unlock(maxed, max_levels=True)[2] == 0, 'second max-levels run should be a no-op'
print(f'ok: max levels set on {n} plants')
