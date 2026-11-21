"""
console.py — Interface console interactive de l'application BiblioIIT.
Institut Ivoirien de Technologie (IIT) — Séance 4.

Reproduit fidèlement la session réelle présentée sur la Slide 29 du cours :
=== BiblioIIT ===
1. Rechercher un livre   2. Emprunter
3. Rendre                4. Retards        0. Quitter

Et propose également les fonctions métier complètes d'une bibliothèque universitaire :
5. Prolonger un emprunt  6. Réserver un livre emprunté
7. Fiche Usager / Payer  8. Catalogue par Rayon / Ajouter
9. Tableau de Bord & Statistiques IIT
"""

import sys
from typing import Callable, Optional

from depot_sqlite import DepotSQLite
from modeles import CategorieLivre, EtatExemplaire, Livre, ModeConsultation, TypeUsager, Usager
from regles import formater_date_fr, obtenir_quota_max, parser_date_iso
from service import ServiceBibliotheque


def afficher_resultats_recherche(livres: list[Livre], afficher_details: bool = False) -> None:
    """
    Affiche les résultats d'une recherche exactement selon le format de la Slide 29 :
      L004  Allah n'est pas obligé — Ahmadou Kourouma (2000)
      L002  Les Soleils des indépendances — „ (1968)
    """
    if not livres:
        print("  Aucun livre trouvé pour cette recherche.")
        return

    auteur_prec: Optional[str] = None
    for livre in livres:
        ligne = livre.format_console(auteur_prec)
        if afficher_details:
            statut = (
                "SUR PLACE"
                if livre.mode_consultation == ModeConsultation.SUR_PLACE.value
                else ("EMPRUNTÉ" if livre.est_emprunte else "DISPONIBLE")
            )
            ligne += f" [{livre.rayon} | {livre.etat} | {statut}]"
        print(ligne)
        auteur_prec = livre.auteur


def afficher_menu() -> None:
    """Affiche le menu principal conforme à la Slide 29 enrichi des options bibliothécaire."""
    print("\n=== BiblioIIT ===")
    print("1. Rechercher un livre   2. Emprunter")
    print("3. Rendre                4. Retards        0. Quitter")
    print("------------------------------------------------------")
    print("5. Prolonger un prêt     6. Réserver un livre")
    print("7. Dossier Usager/Amende 8. Catalogue & Rayons (65+ livres)")
    print("9. Tableau de bord & Statistiques de la bibliothèque")


def executer_console(
    chemin_db: str = "biblio_iit.db",
    input_fn: Callable[[str], str] = input,
) -> None:
    """Boucle interactive principale de l'application console BiblioIIT."""
    depot = DepotSQLite(chemin_db=chemin_db, peupler_par_defaut=True)
    service = ServiceBibliotheque(depot)

    try:
        while True:
            afficher_menu()
            try:
                choix = input_fn("Votre choix : ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nFermeture de BiblioIIT. À bientôt !")
                break

            if choix == "0":
                print("Fermeture de BiblioIIT. À bientôt !")
                break

            # -----------------------------------------------------------------
            # 1. RECHERCHER UN LIVRE (Slide 29)
            # -----------------------------------------------------------------
            elif choix == "1":
                mot_cle = input_fn("Mot-clé : ").strip()
                resultats = service.rechercher(mot_cle)
                afficher_resultats_recherche(resultats)

            # -----------------------------------------------------------------
            # 2. EMPRUNTER UN LIVRE (Slide 29)
            # -----------------------------------------------------------------
            elif choix == "2":
                code = input_fn("Code du livre : ").strip()
                matricule = input_fn("Matricule : ").strip()
                _, message = service.emprunter_livre(code, matricule)
                print(message)

            # -----------------------------------------------------------------
            # 3. RENDRE UN LIVRE (Slide 29 + inspection état physique)
            # -----------------------------------------------------------------
            elif choix == "3":
                code = input_fn("Code du livre : ").strip()
                etat_saisi = input_fn("État au retour (Entrée=BON, ou ABIME / PERDU) : ").strip()
                etat = etat_saisi if etat_saisi else None
                _, message = service.rendre_livre(code, etat_retour=etat)
                print(message)

            # -----------------------------------------------------------------
            # 4. RETARDS (Slide 29)
            # -----------------------------------------------------------------
            elif choix == "4":
                retards = service.lister_retards()
                if not retards:
                    print("Aucun emprunt en retard actuellement.")
                else:
                    print(f"--- Emprunts en retard ({len(retards)}) ---")
                    for item in retards:
                        emp = item["emprunt"]
                        livre = item["livre"]
                        usager = item["usager"]
                        titre = livre.titre if livre else emp.code_livre
                        nom = usager.nom_complet if usager else emp.matricule
                        print(
                            f"  {emp.code_livre} « {titre} » — {emp.matricule} ({nom}) | "
                            f"Échéance : {item['echeance_fr']} | "
                            f"Retard : {item['jours_retard']} j | "
                            f"Pénalité : {item['amende_estimee_fcfa']} FCFA"
                        )

            # -----------------------------------------------------------------
            # 5. PROLONGER UN PRÊT
            # -----------------------------------------------------------------
            elif choix == "5":
                code = input_fn("Code du livre à prolonger : ").strip()
                _, message = service.prolonger_emprunt_livre(code)
                print(message)

            # -----------------------------------------------------------------
            # 6. RÉSERVER UN LIVRE EMPRUNTÉ
            # -----------------------------------------------------------------
            elif choix == "6":
                code = input_fn("Code du livre à réserver : ").strip()
                matricule = input_fn("Matricule : ").strip()
                _, message = service.reserver_livre(code, matricule)
                print(message)

            # -----------------------------------------------------------------
            # 7. DOSSIER USAGER & RÈGLEMENT DES PÉNALITÉS
            # -----------------------------------------------------------------
            elif choix == "7":
                matricule = input_fn("Matricule de l'usager (ex. E2026-001) : ").strip()
                usager = depot.obtenir_usager(matricule)
                if not usager:
                    print(f"Aucun usager inscrit sous le matricule {matricule}.")
                else:
                    emprunts_u = depot.lister_emprunts_actifs_par_usager(usager.matricule)
                    quota = obtenir_quota_max(usager)
                    print(f"\n--- Dossier Usager {usager.matricule} ---")
                    print(f"  Nom complet : {usager.nom_complet}")
                    print(f"  Profil      : {usager.type_usager} ({usager.filiere_ou_departement})")
                    print(f"  Emprunts    : {len(emprunts_u)}/{quota} en cours")
                    print(f"  Pénalités   : {usager.penalites_impayees_fcfa} FCFA")
                    for e in emprunts_u:
                        liv = depot.obtenir_livre(e.code_livre)
                        t_liv = liv.titre if liv else e.code_livre
                        ech_fr = formater_date_fr(parser_date_iso(e.date_retour_prevue))
                        print(f"    • {e.code_livre} : {t_liv} (Retour prévu le {ech_fr})")
                    if usager.penalites_impayees_fcfa > 0:
                        rep = input_fn("Régler les pénalités maintenant ? (o/n) : ").strip().lower()
                        if rep == "o":
                            encaisse = depot.regler_penalites_usager(usager.matricule)
                            print(f"Règlement de {encaisse} FCFA enregistré. Dossier régularisé.")

            # -----------------------------------------------------------------
            # 8. CATALOGUE PAR RAYON / AJOUT D'UN NOUVEL OUVRAGE
            # -----------------------------------------------------------------
            elif choix == "8":
                print("\n--- Catalogue de la Bibliothèque de l'IIT ---")
                print("  1. Afficher tout le catalogue (65+ ouvrages avec cotes et disponibilités)")
                print("  2. Filtrer par catégorie thématique")
                print("  3. Enregistrer une nouvelle acquisition (Ajouter un livre)")
                sous_choix = input_fn("Votre choix : ").strip()
                if sous_choix == "1":
                    tous = service.obtenir_catalogue_complet()
                    print(f"\nCatalogue complet ({len(tous)} ouvrages) :")
                    afficher_resultats_recherche(tous, afficher_details=True)
                elif sous_choix == "2":
                    categories = [c.value for c in CategorieLivre]
                    for idx, cat in enumerate(categories, start=1):
                        print(f"  {idx}. {cat}")
                    num = input_fn("Numéro ou nom de catégorie : ").strip()
                    if num.isdigit() and 1 <= int(num) <= len(categories):
                        cat_choisie = categories[int(num) - 1]
                    else:
                        cat_choisie = num
                    livres_cat = depot.lister_livres_par_categorie(cat_choisie)
                    print(f"\nOuvrages dans « {cat_choisie} » ({len(livres_cat)}) :")
                    afficher_resultats_recherche(livres_cat, afficher_details=True)
                elif sous_choix == "3":
                    code_n = input_fn("Code du nouveau livre (ex. L066) : ").strip().upper()
                    titre_n = input_fn("Titre : ").strip()
                    auteur_n = input_fn("Auteur : ").strip()
                    annee_s = input_fn("Année de parution (ex. 2025) : ").strip()
                    rayon_n = input_fn("Rayon (ex. RAYON-CYB-04) : ").strip() or "RAYON-GEN-01"
                    annee_n = int(annee_s) if annee_s.isdigit() else 2025
                    if code_n and titre_n and auteur_n:
                        depot.ajouter_livre(
                            Livre(
                                code=code_n,
                                titre=titre_n,
                                auteur=auteur_n,
                                annee=annee_n,
                                rayon=rayon_n,
                                etat=EtatExemplaire.NEUF.value,
                            )
                        )
                        print(f"Livre {code_n} « {titre_n} » ajouté au catalogue avec succès.")

            # -----------------------------------------------------------------
            # 9. TABLEAU DE BORD & STATISTIQUES DE LA BIBLIOTHÈQUE
            # -----------------------------------------------------------------
            elif choix == "9":
                stats = depot.obtenir_statistiques_globales()
                retards_actuels = service.lister_retards()
                print("\n=== Tableau de Bord — Bibliothèque Universitaire IIT ===")
                print(f"  • Fonds documentaire total   : {stats['total_livres']} ouvrages")
                print(f"  • Ouvrages disponibles       : {stats['livres_disponibles']}")
                print(f"  • Ouvrages actuellement prêtés : {stats['livres_empruntes']}")
                print(f"  • Usuels (consultation place): {stats['livres_sur_place']}")
                print(f"  • Usagers inscrits (IIT)     : {stats['total_usagers']}")
                print(f"  • Emprunts en retard         : {len(retards_actuels)}")
                print(f"  • Réservations en attente    : {stats['reservations_actives']}")
                print(f"  • Pénalités en attente       : {stats['penalites_impayees_fcfa']} FCFA")

            else:
                print("Choix invalide. Veuillez saisir un numéro entre 0 et 9.")
    finally:
        depot.fermer()


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    executer_console()

