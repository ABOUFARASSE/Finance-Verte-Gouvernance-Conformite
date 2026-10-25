# Module 6 — Management financier et prise de décision stratégique

Cours de Badr Aboufarasse. Six séances, 21 heures, Master Finance verte.
Site statique autonome : ouvrir `index.html` ou publier le dossier via GitHub Pages.
L’évaluation formelle est différée. Les données du cas sont fictives.
Le parcours enrichi comporte sept applications chiffrées par séance et conserve les sections initiales. Les approfondissements et variantes sont dans `scripts/enrichment.py`.

## Sources et reproduction
Le texte original est dans `scripts/course.py`, les références dans `scripts/references.py`.
Le modèle annuel sans dépendance externe : `python3 scripts/model.py`.
Le site et les sources LaTeX se reconstruisent avec `python3 scripts/build.py` (nécessite lxml).
Les PDF se compilent avec pdfLaTeX ; le fichier complet est dans `downloads/`.
Les calculs navigateur et Python utilisent les mêmes conventions ; les tests comparent leurs sorties.
Les CSV utilisent UTF-8 BOM, séparateur point-virgule et décimales avec point.

## Conventions
Tous les montants monétaires du modèle sont en millions de MAD. L’impôt de 25 %, les financements, les gains, les seuils et les facteurs physiques sont des hypothèses pédagogiques.
Le modèle annuel ne garantit pas la liquidité intra-annuelle. Aucun conseil d’investissement réel n’est formulé.
