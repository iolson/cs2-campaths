# Counter-Strike 2 Campaths

A version controlled collection of camera paths (campaths) for Counter-Strike 2,
made with [HLAE](https://www.advancedfx.org/) (Half-Life Advanced Effects). They
are free to use in your own movies, cinematics and highlight reels.

This repository is mainly built for use with
[cs2-highlights-maker](https://github.com/iolson/cs2-highlights-maker), as the
source for its `--cinematic` cam paths and `--static-cam` fixed cameras. The
layout and the optional `.toml` files below follow what that tool reads. The campath
files themselves are plain HLAE campaths, so any HLAE workflow can use them too.

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
tools/            (helper scripts, see "Building a campath from getpos")
```

Each map directory holds that map's files and nothing else:

```
de_nuke/
  a-site-flyby.xml        moving cam paths (used by --cinematic)
  outside-to-ramp.xml
  labels.toml             optional: readable names for the cam paths
  static.toml             optional: fixed cameras (used by --static-cam)
  static/                 optional: fixed cameras as cam path files
    outside-window.campath
```

Only the campath files directly in the map directory are moving paths. Files in
`static/` are read only as fixed cameras, so a single-point path there never shows up
as a `--cinematic` candidate.

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

### `labels.toml`: readable names for cam paths

`cs2-highlights-maker` lists candidate paths by file name. A `labels.toml` in the map
directory adds a description next to each one. Keys are file names without the
extension:

```toml
# de_nuke/labels.toml
a-site-flyby = "Sweep from outside over A site"
outside-to-ramp = "Outside, through secret, down to ramp"
```

Paths without a label still work; they are just listed by file name.

### `static.toml`: fixed cameras

`--static-cam` records a separate take from a camera that holds one pose for the whole
clip. Each fixed camera is a table in `static.toml`. The table name is the camera's
name, which is what you pass to `--static-cam` (for example `--static-cam a-site,outside-window`).

To capture one:

1. Load a demo on the map, switch to free cam and frame the shot.
2. Run `getpos` in the console and copy the line it prints.
3. Add a table with that line:

```toml
# de_nuke/static.toml
[a-site]
getpos = "setpos -1234.500000 567.800000 128.000000;setang 12.500000 90.000000 0.000000"
label = "A site from heaven"   # optional
fov = 90                       # optional, default 90

[outside-window]
pos = [-410.0, -1950.0, 120.0] # instead of getpos: x, y, z
angles = [8.0, 45.0]           # pitch, yaw
```

Roll is ignored. Use lowercase and hyphens for table names, like file names.

You can also save a fixed camera as a cam path file in `static/`: in free cam run
`mirv_campath clear`, `mirv_campath add`, then `mirv_campath save "<file>"`. Only the
first point is used. This records HLAE's own camera pose, so it is the safest capture
while the `getpos` question below is open.

> **`getpos` vs `getpos_exact`:** in demo playback the two can print positions over
> 1,000 units apart with the same angles. Both are accepted, but which one matches the
> free cam has not been confirmed yet. Before adding many cameras or paths from `getpos`
> lines, check one: compare `getpos`, `getpos_exact` and `mirv_campath print` (after a
> `mirv_campath add`) without moving the camera.

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

### With cs2-highlights-maker

Point its `campaths` folder (or the `campaths_dir` setting under `[paths]`) at a
checkout of this repository. It reads the subfolder named after the demo's map:

- `--cinematic` picks from the campath files in the map directory, ranked by how close
  they pass to the play, and retimes the chosen one to fit the clip. The times in the
  file do not matter, only the order and spacing of the keyframes.
- `--static-cam auto|all|<names>` uses the cameras from `static.toml` and `static/`.

## Contributing

Contributions are welcome, for any of the maps above.

1. Fork the repository and create a branch.
2. Record your campath in HLAE and save it with `mirv_campath save`.
3. Put the file in the matching map directory with a descriptive name.
4. Check that it loads and plays correctly in HLAE on that map.
5. Open a pull request that says what the path shows and, where it matters, which
   tick or situation it was built for.

### Building a campath from `getpos`

If you would rather not record a path by hand, `tools/getpos_to_campath.py` builds
one from four or more camera positions. It only needs Python 3, with no extra packages.

1. Load a demo on the map and move to the spot where the shot should start.
2. Run `getpos` in the console and copy the line it prints:
   ```
   setpos 1234.000000 -567.000000 128.031250;setang 12.345678 90.000000 0.000000
   ```
3. Do the same for at least two points along the way and one where the shot ends.
   Four points is the minimum; there is no maximum, so add more for longer or curvier paths.
4. Generate the campath:
   ```
   python3 tools/getpos_to_campath.py -o de_nuke/a-site-flyby.xml
   ```
   With no lines on the command line, it asks you to paste each one; after the fourth,
   press Enter on a blank line to finish. You can also pass the lines as arguments, or
   put them in a text file and use `-i points.txt`.
   The path is 20 seconds unless you pass `-d`. The script prints the camera speed and
   warns when the length or speed is outside the ranges below.

Useful options:

| Option              | What it does                                                                      |
| ------------------- | --------------------------------------------------------------------------------- |
| `-d`, `--duration`  | Length of the path in seconds. Defaults to `20`.                                  |
| `-s`, `--start`     | Time of the first keyframe, in seconds. Defaults to `0`.                          |
| `--fov`             | FOV for every point (`--fov 70`) or one per point, in order (`--fov 90,80,75,70`). Defaults to `90`. |
| `--spacing`         | `distance` (default) keeps the camera at a steady speed; `even` gives each leg the same time. |
| `-o`, `--output`    | File to write. Without it, the campath prints to the terminal.                    |
| `-f`, `--force`     | Overwrite an existing file.                                                       |

#### How long should a path be?

Aim for about **20 seconds**, and keep paths between **8 and 30 seconds**.
`cs2-highlights-maker` never speeds a path up or slows it down to fit a clip: it can
only start it late or hold the last frame. A path longer than the clip is cut off, so
its ending never plays, and a shorter one stops before the clip ends. Clips are 4
seconds of lead-in, the action, then 3 seconds of lead-out, so even a single kill runs
about 7 seconds, and multi-kills and clutches run longer. For short single-kill shots,
add a separate short take (for example `a-site-flyby-short.xml`, around 8 to 12 seconds).

Keep the camera to a slow drift, roughly **10 to 100 units per second** (walking is
250). A reference pack of 153 paths has a median of 23 seconds at about 33 units per
second. If the script warns that a path is too fast, give it a longer `-d` or put the
points closer together.

Load the result with `mirv_campath load` and check it plays well before you submit it.
The same `getpos` vs `getpos_exact` caveat as for fixed cameras applies (see
[`static.toml`](#statictoml-fixed-cameras)): if the path plays in the wrong place but
looks in the right directions, the other variant is the one to use.

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
