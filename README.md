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

# only the shop plants that cannot be bought with gems (21 in 13.5.1)
powershell -ExecutionPolicy Bypass -File unlock_plants.ps1 --shop-only
```

4. Start the game with the internet **off** the first time, so cloud sync doesn't overwrite the edit.

The script force-stops the game, pulls `pp.dat`, edits it, and pushes it back. Every run keeps the pulled original in `save_backups\<timestamp>\pp.dat.bak`. If any step fails, the phone's save is left untouched.

You can also edit a `pp.dat` you copied off the phone yourself:

```powershell
python pvz2_unlock_plants.py pp.dat --max-levels
```

## After a game update

New game versions add plants. To pick them up, regenerate the plant tables from the new game data (the OBB), then run the unlock again.

1. Update the game, open it once so it finishes downloading, then close it.
2. Pull the OBB off the phone (about 1 GB):

   ```powershell
   adb shell ls /sdcard/Android/obb/com.ea.game.pvz2_row/
   adb pull /sdcard/Android/obb/com.ea.game.pvz2_row/main.<version>.com.ea.game.pvz2_row.obb
   ```

3. Regenerate `plant_data.py`. It prints how many plants it found and lists the new ones:

   ```powershell
   python update_plant_data.py main.<version>.com.ea.game.pvz2_row.obb
   ```

4. Pull your save to the PC and sanity-check the new tables against it (the save itself isn't modified):

   ```powershell
   adb pull /sdcard/Android/data/com.ea.game.pvz2_row/files/No_Backup/pp.dat
   python test_pvz2_unlock.py pp.dat
   ```

5. Redo the edits on the phone:

   ```powershell
   powershell -ExecutionPolicy Bypass -File unlock_plants.ps1 --max-levels
   ```

6. Delete the OBB copy from the PC (it's git-ignored either way), and commit the new `plant_data.py`.

If `update_plant_data.py` says it can't find the plant tables, or the self-check fails, the game's data format has changed. Don't run the unlock; open an issue instead.

## How it works

- `pp.dat` is PopCap's RTON binary format (plain, not encrypted, in 13.5.1). `pvz2_rton.py` is a small reader/writer that round-trips the game's own saves byte-for-byte.
- Owned plants are the `p` list of integer plant IDs in the `PlayerInfo` object.
- Plant progress lives in `plis` entries: `l` = upgrades done (level − 1), `x` = unspent seed packets, `m` = mastery rank.
- Plant IDs, level caps (10/15/20, Imitater 1), the mastery cap (200) and the shop-only list live in `plant_data.py`. `update_plant_data.py` generates that file from the game data (`PlantTypes`, `PlantLevels`, `PlantMastery`, `StoreProductProps` inside the OBB's `Packages` group). Hidden helper objects such as Sprout and Sun Gun are left out.

## Caveats

- **Game updates:** newer versions add plants. The script still works, but new plants aren't included until you regenerate `plant_data.py` (see [After a game update](#after-a-game-update)).
- **Cloud saves:** on an EA-linked account, a later sync may restore the server copy.
- **Shop-only list:** it's based on the game's built-in catalog. The live shop can price plants differently per region or account, so `--shop-only` may not match exactly what you see.
- **Account risk:** editing saves is against EA's terms. Use it for single-player play, and expect online modes to possibly flag edited accounts.

## Self-check

```powershell
python test_pvz2_unlock.py path\to\pp.dat
```

This checks the byte-exact RTON round-trip, the unlock and max-level edits, and that a second run changes nothing. The file you pass in is not modified.

## Disclaimer

This project is not affiliated with or endorsed by Electronic Arts or PopCap. Plants vs. Zombies is a trademark of Electronic Arts Inc. No game assets are included.
