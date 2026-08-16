# Boom! Tetris — Remaining Work

Features present in the old `Tetris/` repo but not yet ported to `boom-tetris/`.
This is an overview of **what** is left, not how to do it. Tick a box (`[x]`) when done.

## Already working in the new repo (for reference)
- [x] Board, gravity, line clears
- [x] Scoring for line clears + level progression
- [x] ARE (entry delay)
- [x] DAS + tucking (wall-charge)
- [x] Next-piece preview (piece is shown)
- [x] Config system + UI field layout (LINES / SCORE / LEVEL text)
- [x] Optional gridlines rendering

## Core gameplay still missing
- [x] Correct piece RNG — NES-style anti-repeat reroll (currently a uniformly random shape, no reroll)
- [ ] Game-over detection and handling (no top-out check yet)
- [ ] Pause game
- [ ] Soft-drop and hard-drop points added to score (config values exist but are unused)
- [ ] Hard-drop enable/disable option
- [ ] NTSC vs PAL timing selection (PAL values exist in config but are unused)
- [ ] Line-clear animation and its delay
- [ ] Landing preview / ghost piece (toggleable)
- [ ] In-game toggle keys for gridlines and preview
- [ ] Type B mode — clear a set number of lines starting from a pre-filled garbage stack, with height/level selectors (new feature — was not in the old repo)

## Visual / layout still missing
- [ ] Coloured tetromino pieces (NES per-level colour scheme; currently one flat colour)
- [ ] Beveled block borders (black outer + coloured inner border look)
- [ ] Borders around each UI field
- [ ] Game background — ideally identical to the real NES Tetris background; if that is too hard, something that more closely resembles it (the old repo used a hand-made mathematical brick pattern as an easier stand-in)
- [ ] Statistics field content — per-piece frequency counts with mini pieces
- [ ] Type field content — current piece indicator
- [ ] CTWC metric fields — tetris rate, burn count, drought meter

## Main menu (currently absent entirely)
- [ ] Start-up / title splash screen (with intro sfx)
- [ ] Main menu entries: Singleplayer, Multiplayer, AI Game, Options, Music, Commentary, Quit
- [ ] Menu visuals: background image, button hover highlight, click sfx, mouse + keyboard navigation
- [ ] Singleplayer screen — level select 0–9, and 10–19 via shift/hold
- [ ] Multiplayer screen — level select + mode
- [ ] Options screen:
    - [ ] Tetromino preview on/off
    - [ ] Gridlines on/off
    - [ ] Hard drop on/off
    - [ ] Tetris version NTSC/PAL
    - [ ] Same piecesets on/off (multiplayer)
    - [ ] Music volume
    - [ ] Commentary volume
    - [ ] Singleplayer controls remap
    - [ ] Multiplayer controls remap
    - [ ] Advanced options (was a placeholder in old repo)
- [ ] Controls remapping screen — press-a-key rebinding (single + multiplayer)
- [ ] Music screen — browse folders/songs with pagination
- [ ] Commentary screen — select commentary mode (+ Boom Tetris voice submenu)

## Sound effects (none yet)
- [ ] Movement, rotation, line clear, level up
- [ ] Game-start countdown, game over
- [ ] Commentary system: Boom Tetris for <name>, tetris-ready, there-it-is, neck-and-neck, Tetris God piece callouts, World Cup 2010
- [ ] Commentary volume control

## Music (none yet)
- [ ] Background music playback with playlist/queue
- [ ] Music folders (8-bit Bangers, Original soundtrack, Other VG) + user-added tracks
- [ ] Random shuffle, menu music, end-of-song handling, volume control

## Local 2-player mode (none yet)
- [ ] Two boards side by side with separate controls
- [ ] Same / different piecesets option
- [ ] Score-difference / tetris-lead display (toggle)
- [ ] "It's neck and neck" commentary trigger
- [ ] Best-of-5 mode with hearts field
- [ ] Winner detection
- [ ] Per-player colours and per-player toggles (preview / gridlines)

## Post-game statistics (none yet)
- [ ] Stats button after game → graphs
- [ ] Graphs: score, score lead, score-type distribution, tetris rate, tetromino distribution (+ chi-squared), droughts
- [ ] Highscores — read/write highscores file with top-10 insertion
- [ ] Matplotlib-to-disk window-minimize bug — fix, or replace with pygame-native plotting so graphs render in the same session

## Bonus
- [ ] Port / fix the DQN reinforcement-learning agent (known broken — see analysis in chat)
- [ ] (Optional) Windows packaging / executable build
