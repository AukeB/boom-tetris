TODO:

- Main functionalities
    - ARE (check if currently correct w.r.t place height, or maybe should be the other way around.)
    - DAS
    - Pause game
- Main layout
    - Tetris colored pieces
    - Fields borders
    - Polyomino borders
- Main Menu
- Sound effects
- Music
- Local 2 player mode
- Post-game statistics
    - In old repo we create plots with matploblib, then write those as images to disk. Because
    of writing to disk, sometimes the window minimizes in this step. Would be nice if we can
    fix this bug. Either find something so that when writing to disk the pygame window does not
    minimize, or write some sort of pygame based plotting library, so that all plots/graphs
    are just drawn in the same pygame session. Second option would work for sure, but would also
    be lots of extra code.