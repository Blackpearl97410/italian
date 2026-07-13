# Langues Pas a Pas

Application desktop PySide6 pour apprendre l'anglais et l'italien depuis le francais, par situations concretes.

## Architecture

- `app/` : point d'entree, configuration et chemins portables avec `pathlib`.
- `domain/` : modeles SQLAlchemy, schemas simples et enums.
- `database/` : creation SQLite, seed et repositories.
- `services/` : logique metier, feedback, progression, revision et import.
- `ui/` : fenetre PySide6, ecrans et widgets reutilisables.
- `data/seed/` : contenu pedagogique source et reformule.
- `tests/` : tests unitaires prioritaires.
- `scripts/` : initialisation et validation de contenu.

## Dependances

- Python 3.12+
- PySide6
- SQLAlchemy
- pytest pour les tests

Installation:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Sous Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer l'application

```bash
python -m app.main
```

La base SQLite est creee dans `~/.langues_pas_a_pas/langues_pas_a_pas.sqlite3`.

## Lancer la version web locale

La suite du developpement peut se faire dans `web_preview/`. Cette version garde la
progression, les reponses, les revisions et les imports dans `localStorage`.
Elle propose aussi des profils locaux avec login: chaque utilisateur conserve son
propre espace personnel, ses imports, ses scores et ses revisions.

```bash
python3 -m http.server 8765
```

Puis ouvrir:

```text
http://localhost:8765/web_preview/
```

Un fichier d'import exemple est disponible ici:

```text
web_preview/sample_import.json
```

La charte graphique web s'inspire du drapeau italien:

- vert profond pour les actions principales et la progression;
- blanc creme pour les surfaces de lecture;
- rouge doux pour les actions sensibles et les alertes;
- tons neutres chauds pour garder une interface sobre et pedagogique.

## Initialiser seulement la base

```bash
python scripts/create_db.py
```

## Tester

```bash
pytest
```

## Modele de donnees

La V1+ contient les tables `languages`, `sources`, `situations`, `phrases`, `grammar_points`, `exercises`, `user_progress`, `user_answers` et `review_items`.

Chaque contenu pedagogique est rattache a une source. Le seed V1+ est manuel et reformule; il conserve des references de travail vers le CECRL, Tatoeba et Creative Commons sans scraper ni copier massivement de contenu tiers.

Sources utiles verifiees le 2026-07-07:

- Conseil de l'Europe, descripteurs CECRL: https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions
- Tatoeba, conditions d'utilisation: https://tatoeba.org/en/terms_of_use
- Creative Commons BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/deed.en

## Import JSON

Format attendu:

```json
{
  "source": {
    "name": "Nom",
    "url": "https://example.com",
    "source_type": "educational_resource",
    "license": "manual",
    "retrieved_at": "2026-07-07",
    "reliability_score": 4,
    "notes": "Contenu reformule et valide manuellement."
  },
  "situations": [
    {
      "slug": "se-presenter",
      "title": "Se presenter",
      "level": "A1",
      "objective": "Savoir donner son nom.",
      "phrases": [
        {
          "fr_text": "Je m'appelle Alexandre.",
          "en_text": "My name is Alexandre.",
          "it_text": "Mi chiamo Alexandre.",
          "explanation": "Explication comparative.",
          "common_trap": "Piege frequent."
        }
      ],
      "exercises": [
        {
          "type": "multiple_choice",
          "question": "Question",
          "correct_answer": "Reponse",
          "options": ["Reponse", "Distracteur"],
          "explanation_correct": "Pourquoi c'est correct.",
          "explanation_wrong": "Correction pedagogique.",
          "difficulty": 1
        }
      ]
    }
  ]
}
```

Validation:

```bash
python scripts/validate_content.py data/seed/situations_seed.json
```

## Packaging futur

Le projet evite les chemins absolus et isole le point d'entree dans `app/main.py`, ce qui facilite PyInstaller ou Nuitka.

Exemple PyInstaller a ajuster selon plateforme:

```bash
pyinstaller --name "Langues Pas a Pas" --windowed --add-data "data:data" app/main.py
```

## Risques surveilles

- Droits des sources: pas de scraping massif en V1+, imports controles et attribution conservee.
- Packaging: dependances limitees a PySide6 et SQLAlchemy.
- Qualite pedagogique: contenus courts, comparatifs et revisables.
- Evolution audio/IA/cloud: modeles separes et champs de prononciation deja prevus.
