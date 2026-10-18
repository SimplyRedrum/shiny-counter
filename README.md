# Shiny Reset Counter

A tap counter for soft-reset shiny hunting in Pokémon Gen 1–3 (Red/Blue/Yellow, Gold/Silver/Crystal, Ruby/Sapphire/Emerald, FireRed/LeafGreen).

- Shows the animated shiny sprite of the Pokémon you're hunting
- Tracks resets, resets today, and the chance you'd have seen a shiny by now
- Saves on your device and works offline once installed
- Backup and restore your hunts with a copy-paste code

Open the GitHub Pages site on your phone and use **Add to Home Screen** to install it.

Sprites come from the [PokeAPI sprites](https://github.com/PokeAPI/sprites) collection. Pokémon and its sprites are © Nintendo, Game Freak and The Pokémon Company. This is an unofficial fan project.

## Editing

The page is built from `src/app.src.html`. After changing it, run `python3 tools/build.py` to regenerate `index.html` and `sw.js`, then commit.
