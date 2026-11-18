# trend-detection

Détection de tendances TikTok : repérer les groupes de vidéos similaires (même son, format ou sujet) dont la popularité croît plus vite que la normale.

Thèmes : danse, cuisine, memes. Les critères et le score sont détaillés dans `004_SIA_261002_104436.pdf`.

## Installation

```bash
python3 -m pip install TikTokApi python-dotenv
python3 -m playwright install chromium
cp .env.example .env   # puis y coller le cookie msToken de tiktok.com
```

## Collecte

```bash
python3 collect/test_tiktokapi.py --hashtag dance
```

Chaque lancement enregistre un relevé horodaté dans `data/raw/`. À relancer chaque jour pour mesurer la croissance. Si TikTok bloque, ajouter `--show-browser`.
