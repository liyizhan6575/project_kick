# Pitch Deck

The showcase place for KICK's **applied products** — polished previews you can read and watch
without the source. The implementations are **closed source for now**; these materials demonstrate
what they do. Linked from the repo [main README](../README.md).

## What's here

| Showcase | Material | Status |
|---|---|---|
| **Pitch Prism** — football telestrator | [`pitch_prism.pdf`](pitch_prism.pdf) — field guide | 🟡 Preview |
| **Pitch Reel** | `pitch_reel.pdf` | ◻︎ To do |
| **Pitch Pilot** | `pitch_pilot.pdf` | ◻︎ To do |

Materials come in three forms — **field-guide PDFs** (the interface tour of each app),
**demo videos** (the apps in motion), and **notebooks** where a walkthrough helps.

## Layout

```
pitch_deck/
  <product>.pdf              # product field guides, one per product
  src/<product>/
    <product>.html           # the styled PDF source (edit this)
    assets/                  # real screenshots + embedded fonts
```

## Rebuilding a product PDF

```
weasyprint src/pitch_prism/pitch_prism.html pitch_prism.pdf
```

Guides are styled to each app's own identity (Pitch Prism: neutral-dark + amber, Chakra Petch);
screenshots are real captures of the running app.
