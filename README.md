# pvz2-save-unlocker

Unlock every plant in a Plants vs. Zombies 2 save, and optionally max every plant's level and mastery. It edits `pp.dat` directly, from a Windows PC over USB, with no root needed.

Built and tested against **PvZ2 13.5.1 (ROW, `com.ea.game.pvz2_row`)** on Android.

## Requirements

- Windows with Python 3.8+ on `PATH`
- [Android platform-tools](https://developer.android.com/tools/releases/platform-tools) (`adb`)
- USB debugging enabled on the phone

## Usage

1. Install the game, play past the first level (the save has no player profile before that), then close it.
2. Connect the phone and accept the USB debugging prompt.
3. Run one of:

```powershell
# unlock all 216 plants
powershell -ExecutionPolicy Bypass -File unlock_plants.ps1

# unlock all plants and max every plant's level and mastery
powershell -ExecutionPolicy Bypass -File unlock_plants.ps1 --max-levels

# only the 21 shop plants that cannot be bought with gems
powershell -ExecutionPolicy Bypass -File unlock_plants.ps1 --shop-only
```

4. Start the game with the internet **off** the first time, so cloud sync doesn't overwrite the edit.

The script force-stops the game, pulls `pp.dat`, edits it, and pushes it back. Every run keeps the pulled original in `save_backups\<timestamp>\pp.dat.bak`. If any step fails, the phone's save is left untouched.

You can also edit a `pp.dat` you copied off the phone yourself:

```powershell
python pvz2_unlock_plants.py pp.dat --max-levels
```

## How it works

- `pp.dat` is PopCap's RTON binary format (plain, not encrypted, in 13.5.1). `pvz2_rton.py` is a small reader/writer that round-trips the game's own saves byte-for-byte.
- Owned plants are the `p` list of integer plant IDs in the `PlayerInfo` object.
- Plant progress lives in `plis` entries: `l` = upgrades done (level − 1), `x` = unspent seed packets, `m` = mastery rank.
- Plant IDs, level caps (10/15/20, Imitater 1) and the mastery cap (200) were extracted from the 13.5.1 game data (`PlantTypes`, `PlantLevels`, `PlantMastery`). Hidden helper objects such as Sprout and Sun Gun are left out.

## Caveats

- **Game updates:** newer versions add plants. The script still works, but new plants aren't included until the `PLANTS` table is regenerated.
- **Cloud saves:** on an EA-linked account, a later sync may restore the server copy.
- **Account risk:** editing saves is against EA's terms. Use it for single-player play, and expect online modes to possibly flag edited accounts.

## Self-check

```powershell
python test_pvz2_unlock.py path\to\pp.dat
```

This checks the byte-exact RTON round-trip, the unlock and max-level edits, and that a second run changes nothing. The file you pass in is not modified.

## Disclaimer

This project is not affiliated with or endorsed by Electronic Arts or PopCap. Plants vs. Zombies is a trademark of Electronic Arts Inc. No game assets are included.
