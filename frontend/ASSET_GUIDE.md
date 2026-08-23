# Card Artwork Contract

All card artwork uses the existing project ratio: **3:4**.

- Existing native size: **60 × 80 px**
- Recommended larger canvas: **600 × 800 px** or **1200 × 1600 px**
- Export format: PNG or WebP
- On a 600 × 800 canvas, keep essential text and faces at least 48 px away from every edge.
- Do not create separate artwork for the board, hand, and detail panel. The UI scales the same image proportionally.
- Artwork fills the frame with `cover`, so decorative background near the outer edge may be cropped slightly at fractional screen scaling.

Rendered reference sizes at the standard desktop layout:

- Board card: 84 × 112 CSS px at the standard desktop layout. Rows overlap by 14 px so the larger cards still fit on one shared screen.
- Hand card: 48 × 64 CSS px
- Detail artwork: 120 × 160 CSS px
