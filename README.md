# Counter-Strike 2 Campaths

A version controlled collection of camera paths (campaths) for Counter-Strike 2,
made with [HLAE](https://www.advancedfx.org/) (Half-Life Advanced Effects). They
are free to use in your own movies, cinematics and highlight reels.

The collection is also the campath source for my
[cs2-highlights-maker](https://github.com/iolson/cs2-highlights-maker) fork, which
uses them for cinematic recordings. Nothing here is tied to that tool, so any
HLAE workflow can use these files.

## Repository layout

There is one directory per Active Duty map, named after the map's internal name:

```
de_ancient/
de_anubis/
de_cache/
de_dust2/
de_inferno/
de_mirage/
de_nuke/
de_overpass/
de_train/
de_vertigo/
resources/        (gitignored, see below)
```

Each map directory holds campath files for that map and nothing else.

### What a campath file is

A campath is the HLAE camera path format: an XML file of timed keyframes
(`<p t x y z ...>`) giving the camera position, rotation and field of view over
time. HLAE writes this format when you save with `mirv_campath save`, and reads it
back with `mirv_campath load`.

Accepted file extensions:

| Extension   | Notes                                              |
| ----------- | -------------------------------------------------- |
| `.xml`      | The default HLAE export.                           |
| `.campath`  | Same format, different extension.                  |
| `.dz`       | Same format, commonly used for shared campath packs. |

All three are the same XML underneath, so use whichever extension suits you.

### What belongs in each map directory

Campaths for that map, such as:

- **Utility showcases:** following a smoke, molotov or flash from the throw to where it lands.
- **Site and area flybys:** sweeping establishing shots of a bombsite, mid, or a lane.
- **Angle and position reveals:** a path that ends on a common hold or a one-way.
- **Kill and round cinematics:** shots built to frame a play from a known position.

A campath only makes sense on the map it was recorded on, because the coordinates
are world positions. Put each file in the directory of its map.

### Naming

Use short, descriptive names that say where the path is and what it does, for example:

```
de_nuke/
  a-site-flyby.xml
  outside-to-ramp.xml
  heaven-smoke-throw.xml
```

Use lowercase and hyphens, with no spaces. If one idea has several takes, add a suffix
(`-v2`) rather than overwriting the original.

## Using these campaths

1. In HLAE, with the demo loaded on the matching map, run:
   ```
   mirv_campath load "path/to/de_nuke/a-site-flyby.xml"
   mirv_campath enabled 1
   ```
2. Start playback or recording from the tick where the path should begin.

For `cs2-highlights-maker`, point its `campaths` folder (or the `campaths_dir`
setting under `[paths]`) at a checkout of this repository. It picks files up from the
subfolder named after the map, and accepts either `de_nuke` or `Nuke`.

## Contributing

Contributions are welcome, for any of the maps above.

1. Fork the repository and create a branch.
2. Record your campath in HLAE and save it with `mirv_campath save`.
3. Put the file in the matching map directory with a descriptive name.
4. Check that it loads and plays correctly in HLAE on that map.
5. Open a pull request that says what the path shows and, where it matters, which
   tick or situation it was built for.

Before you submit:

- **Only submit paths you made yourself.** Do not submit paths from paid packs,
  other creators' work without their permission, or anything you do not have the
  right to share.
- Keep files small and clean: remove stray test points and unused takes.
- One campath per file, and each file must be valid HLAE campath XML.
- Do not include demos, videos or other binaries.

## `resources/`

`resources/` is for local reference material that cannot be shared publicly, such as
paid campath packs used as examples while building out new maps. Everything in it
is gitignored (only its `.gitignore` is tracked), so it never reaches GitHub. Do not
copy files from it into the map directories.
