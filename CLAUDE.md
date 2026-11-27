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
- YouTube 01: 25.11. · 02: 26.11. (vorgezogen, TikTok ebenso) · · 08: 30.11. · 03: 02.12. · 09: 04.12. · 04: 07.12. · 10: 09.12. · 05: 11.12. · 06: 14.12. · 07: 16.12.
- TikTok: dieselben Termine ab 27.11. (ohne 01)
- Nächster freier Termin: Fr 18.12.2026

## Ton
- Jedes Video bekommt Hintergrundmusik aus `engine/music.py` (selbst erzeugtes Piano, lizenzfrei).
- Mischung (vom Inhaber freigegeben): Effekte volume 0.9, Musik volume 0.33, danach loudnorm I=-14 TP=-1.5.
- Aktuelle Upload-Dateien mit Musik liegen in `videos/v2/`.

## Stimme (ElevenLabs)
- Stimme: „Crystal Erickson“ (voice_id 0SPbwsQMh0YMtHHFcLu7), Modell eleven_v4. Claude kann die MP3 nicht selbst laden (Proxy blockt elevenlabsusercontent.com): der Inhaber lädt die gewählte Variante herunter und schickt sie.
- Bisher nur 08_bamboo mit Stimme (`videos/v3/08_bamboo_voice.mp4`). ElevenLabs-Konto im Free-Plan → Quellenangabe „Voice: ElevenLabs“ in der Caption; bei Monetarisierung auf Starter wechseln.

## TikTok-Schnitte (ab 26.11.2026)
- TikTok-Analyse: Ø Wiedergabe nur 12 s von 45 s → kürzere Schnitte (≈28 s), großer Aufhänger ab Bild 1 (kein Fade-in), größere Texte.
- Vorlage: `engine/tiktok/tt.py` (Konfiguration `coffee_tt`), Engine-Option `fade_in=False`, Captions mit t0=0 erscheinen sofort.
- 03_coffee: TikTok-Schnitt `videos/tiktok/03_coffee_tiktok.mp4` am 26.11. auf TikTok UND YouTube sofort gepostet (vorgezogen vom 02.12.).
- Geplant: übrige Videos ebenso umbauen + deutscher Test – erst nach Freigabe des Inhabers.

## Neu am 27.11.2026
- YouTube ab 28.11. täglich 18:30 (Inhaber-Wunsch: fast täglich auf YouTube). Reihenfolge: 08, 09, 04, 10, 05, 06, 07 (bis 4.12.).
- TikTok: Inhaber lädt Videos händisch hoch (Buffer-Uploads bekamen 0 Aufrufe). TikTok-Posts in Buffer nicht automatisch nutzen, ohne Rücksprache.
- Neue Ladung (noch NICHT freigegeben): discipline_climb (`engine/climb/climb.py`) + 6 Geld-Videos im Kurzformat (`engine/tiktok/tt2.py`: eating_out, subscriptions, phone, lottery, smoking, kid).
- Edit-Format (`engine/edits/edit.py`): Schwarz-Weiß-Geld-Edit, Schnitte auf 120 BPM, eigene Grafiken; nur TikTok, händisch vom Inhaber hochgeladen (money_edit, 27.11.).

- Story-Format (`engine/story/story.py`): 2D-Strichmännchen in 3D-artigen Kulissen (Büro Nacht/Regen/Morgen, Dach), Texte oben, Laptop-UI; Inhaber spricht Audio selbst ein. Erstes Video: story_one_hour (27.11.), vom Inhaber gut bewertet.

## Bibliothek (27.11.2026)
- Alle bisher erstellten Videos (finale Versionen) liegen nummeriert in `videos/library/` (01–23), vom Inhaber zum Herunterladen/manuellen Posten (u. a. Instagram) gewünscht.
