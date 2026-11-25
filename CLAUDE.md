# Stick Lessons – Arbeitsanweisung für Claude

Kanal: **Stick Lessons** (TikTok @stick.lessons, YouTube „Stick Lessons“, Instagram folgt).
Minimalistische Strichmännchen-Videos im Hochformat 1080×1920, 30 fps, englische Bildschirmtexte,
dunkler Hintergrund, Akzentfarbe Grün (#39E58C), Rot (#EB4848) für Verlust.

## Ablauf (vom Kanalinhaber festgelegt)
1. Der Inhaber sagt, dass neue Videos erstellt werden sollen (ggf. mit Format/Thema).
2. Claude baut die Videos und schickt sie zur Ansicht.
3. **Erst nach ausdrücklicher Freigabe** lädt Claude sie nach `videos/` hoch (commit + push auf `main`)
   und plant sie in Buffer ein (Organisation „My organization“).
4. Video-URL für Buffer: `https://raw.githubusercontent.com/qthetaa-oss/stick-lessons/main/videos/<datei>.mp4`

## Buffer
- TikTok-Kanal: `6b06cc588541f09ecb9be19b`, YouTube-Kanal: `6b06cd178541f09ecb9be6b7`
- Free-Plan: max. 10 geplante Posts pro Kanal gleichzeitig.
- Standard-Rhythmus: Mo/Mi/Fr 18:30 Europe/Berlin, mode `customScheduled`.
- YouTube: type `short`, categoryId `27` (Education), Titel mit `#shorts`.
- Jede Caption endet mit Disclaimer bei Geld-Themen („Not financial advice.“).

## Formate / Vorlagen (`engine/`)
- `money/` – drei (oder zwei) Figuren, Geldstapel, Jahreszähler (`videos.py` enthält alle Konfigurationen, `build.sh <name>` rendert).
- `bamboo/` – zwei Panels, einer gibt auf, Durchbruch beim anderen.
- `charts/` – „X vs Y vs Z“ mit drei Schreibtischen und Charts.
- `typo/` – schwarz-weiße Kinetic Typography mit Mini-Figur.
Hinweis: Die Skripte enthalten noch absolute Pfade (`/home/claude/vid…`); vor dem Rendern anpassen.

## Bereits veröffentlicht
- 01_compound_interest: TikTok manuell durch den Inhaber gepostet (nicht erneut auf TikTok einplanen).
