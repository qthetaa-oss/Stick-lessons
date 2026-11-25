# Stick Lessons – Arbeitsanweisung für Claude

Kanal: **Stick Lessons** (TikTok @stick.lessons, YouTube „Stick Lessons“, Instagram folgt).
Minimalistische Strichmännchen-Videos im Hochformat 1080×1920, 30 fps, englische Bildschirmtexte,
dunkler Hintergrund, Akzentfarbe Grün (#39E58C), Rot (#EB4848) für Verlust.

## Ablauf (vom Kanalinhaber festgelegt)
1. Der Inhaber sagt, dass neue Videos erstellt werden sollen (ggf. mit Format/Thema).
2. Claude baut die Videos und schickt sie zur Ansicht.
3. **Erst nach ausdrücklicher Freigabe** lädt Claude sie nach `videos/` hoch (commit + push auf `main`)
   und plant sie in Buffer ein (Organisation „My organization“).
4. Video-URL für Buffer: `https://raw.githubusercontent.com/qthetaa-oss/Stick-lessons/main/videos/<datei>.mp4`

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

## Eingeplant am 25.11.2026 (Buffer, je 18:30)
- YouTube 01: 25.11. · 02: 27.11. · 08: 30.11. · 03: 02.12. · 09: 04.12. · 04: 07.12. · 10: 09.12. · 05: 11.12. · 06: 14.12. · 07: 16.12.
- TikTok: dieselben Termine ab 27.11. (ohne 01)
- Nächster freier Termin: Fr 18.12.2026

## Ton
- Jedes Video bekommt Hintergrundmusik aus `engine/music.py` (selbst erzeugtes Piano, lizenzfrei).
- Mischung (vom Inhaber freigegeben): Effekte volume 0.9, Musik volume 0.33, danach loudnorm I=-14 TP=-1.5.
- Aktuelle Upload-Dateien mit Musik liegen in `videos/v2/`.

## Stimme (ElevenLabs)
- Stimme: „Crystal Erickson“ (voice_id 0SPbwsQMh0YMtHHFcLu7), Modell eleven_v4. Claude kann die MP3 nicht selbst laden (Proxy blockt elevenlabsusercontent.com): der Inhaber lädt die gewählte Variante herunter und schickt sie.
- Bisher nur 08_bamboo mit Stimme (`videos/v3/08_bamboo_voice.mp4`). ElevenLabs-Konto im Free-Plan → Quellenangabe „Voice: ElevenLabs“ in der Caption; bei Monetarisierung auf Starter wechseln.
