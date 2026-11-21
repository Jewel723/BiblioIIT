# BiblioIIT — Système de Gestion de la Bibliothèque Universitaire (IIT)

Application console Python & SQLite développée dans le cadre de la **Séance 4 — Institut Ivoirien de Technologie (IIT)**.

- **Auteur** : Loïc Otniel ADON (`loic.adon@iit.ci` — Licence 2 Cyber Science)
- **Base de données** : SQLite3 (`biblio_iit.db`) pré-chargée avec **65 ouvrages** (`L001` à `L065`) et **15 usagers IIT** (Étudiants et Enseignants).
- **Tests automatisés** : `pytest` + Pipeline CI GitHub Actions.

---

## 1. Architecture Modulaire (Conforme Slide 29)

| Module | Branche Git | Responsabilité |
| :--- | :--- | :--- |
| [`modeles.py`](modeles.py) | `feature/modeles` | Entités typées : `Livre`, `Usager`, `Emprunt`, `Reservation`, `Sanction`, `EtatExemplaire`, `CategorieLivre`, `ModeConsultation`. |
| [`regles.py`](regles.py) | `feature/regles` | Règles métier : quotas (3 livres/14j pour étudiant, 5 livres/30j pour enseignant), contrôles d'éligibilité, prolongations, calcul des retards et pénalités (200 FCFA/jour, dégradation, perte). |
| [`depot_sqlite.py`](depot_sqlite.py) | `feature/base` | Persistance relationnelle SQLite3, transactions ACID et amorçage initial de **65 livres** répartis en 6 rayons thématiques. |
| [`service.py`](service.py) | `feature/service` | Orchestration métier des emprunts, retours avec inspection physique, gestion des files de réservation, prolongations et alertes de retard. |
| [`console.py`](console.py) | `feature/menu` | Interface console interactive reproduisant la session réelle du cours + fonctions avancées du bibliothécaire. |
| [`tests/`](tests/test_biblio_iit.py) | Toutes | Suite de tests unitaires et d'intégration couvrant tous les modules et le scénario exact de la Slide 29. |

---

## 2. Lancer l'application et les tests

```bash
# Lancer l'application interactive
python console.py

# Exécuter les tests unitaires
python -m pytest -v
```
