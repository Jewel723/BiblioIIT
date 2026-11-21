"""
service.py — Couche de service applicatif du système BiblioIIT.
Institut Ivoirien de Technologie (IIT) — Séance 4.

Orchestre les règles métier (regles.py), les modèles (modeles.py) et la base SQLite (depot_sqlite.py) :
- Recherche d'ouvrages et consultation par rayon/catégorie
- Emprunt d'un livre avec inscription automatique des nouveaux matricules ou validation complète
- Retour d'un ouvrage avec calcul des retards, inspection de l'état physique et notification de réservation
- Liste détaillée des retards et relances
- Prolongation d'emprunt et réservation en file d'attente
"""

from datetime import date
from typing import Dict, List, Optional, Tuple

from depot_sqlite import DepotSQLite
from modeles import (
    Emprunt,
    EtatExemplaire,
    Livre,
    Reservation,
    TypeUsager,
    Usager,
)
from regles import (
    calculer_date_retour_prevue,
    calculer_jours_retard,
    calculer_penalite_retour,
    est_emprunt_en_retard,
    formater_date_fr,
    parser_date_iso,
    verifier_eligibilite_emprunt,
    verifier_eligibilite_prolongation,
)


class ServiceBibliotheque:
    """Service principal de gestion de la bibliothèque universitaire de l'IIT."""

    def __init__(self, depot: DepotSQLite) -> None:
        self.depot = depot

    # =========================================================================
    # 1. RECHERCHE & CONSULTATION DU CATALOGUE
    # =========================================================================

    def rechercher(self, mot_cle: str) -> List[Livre]:
        """Recherche des livres dans le catalogue par titre, auteur, code, catégorie ou rayon."""
        if not mot_cle or not mot_cle.strip():
            return self.depot.lister_tous_les_livres()
        return self.depot.rechercher_livres(mot_cle)

    def obtenir_catalogue_complet(self) -> List[Livre]:
        """Retourne les 65+ ouvrages du catalogue de l'IIT."""
        return self.depot.lister_tous_les_livres()

    # =========================================================================
    # 2. EMPRUNT D'UN LIVRE (Conforme Slide 29 + Règles Réelles)
    # =========================================================================

    def emprunter_livre(
        self,
        code_livre: str,
        matricule: str,
        date_emprunt: Optional[date] = None,
    ) -> Tuple[bool, str]:
        """
        Tente d'enregistrer l'emprunt d'un livre pour un matricule donné.
        - Si le matricule n'est pas encore en base mais respecte le format IIT (ex. E2026-xxx ou P2026-xxx),
          l'usager est créé à la volée pour faciliter les tests rapides en console.
        - Retourne (succes: bool, message_console: str).
        """
        code_clean = code_livre.strip().upper()
        mat_clean = matricule.strip().upper()

        if not mat_clean:
            return False, "Impossible : Le matricule de l'usager est obligatoire."

        livre = self.depot.obtenir_livre(code_clean)
        usager = self.depot.obtenir_usager(mat_clean)

        # Création automatique à la volée si le professeur saisit un nouveau matricule en démo
        if usager is None and livre is not None:
            profil = TypeUsager.ENSEIGNANT.value if mat_clean.startswith("P") else TypeUsager.ETUDIANT.value
            usager = Usager(
                matricule=mat_clean,
                nom_complet=f"Usager IIT ({mat_clean})",
                type_usager=profil,
                filiere_ou_departement="IIT",
            )
            self.depot.ajouter_usager(usager)

        emprunts_actifs = self.depot.lister_emprunts_actifs_par_usager(mat_clean)
        reservations_livre = self.depot.lister_reservations_en_attente(code_clean)
        reservataire_prio = reservations_livre[0].matricule if reservations_livre else None

        jour_emprunt = date_emprunt or date.today()

        autorise, msg = verifier_eligibilite_emprunt(
            livre=livre,
            usager=usager,
            emprunts_actifs_usager=emprunts_actifs,
            matricule_reservataire_prioritaire=reservataire_prio,
            date_reference=jour_emprunt,
        )
        if not autorise:
            return False, msg

        assert livre is not None
        date_retour = calculer_date_retour_prevue(jour_emprunt, usager)

        nouvel_emprunt = Emprunt(
            id=None,
            code_livre=livre.code,
            matricule=mat_clean,
            date_emprunt=jour_emprunt.isoformat(),
            date_retour_prevue=date_retour.isoformat(),
            etat_depart=livre.etat,
        )
        self.depot.creer_emprunt(nouvel_emprunt)

        # Si l'emprunteur était le réservataire prioritaire, on marque sa réservation comme honorée
        if reservations_livre and reservations_livre[0].matricule == mat_clean and reservations_livre[0].id:
            self.depot.honorer_reservation(reservations_livre[0].id)

        date_fr = formater_date_fr(date_retour)
        return True, f"Emprunt enregistré. Retour prévu le {date_fr}."

    # =========================================================================
    # 3. RETOUR D'UN LIVRE (Inspection d'état, Retards, Pénalités & File d'attente)
    # =========================================================================

    def rendre_livre(
        self,
        code_livre: str,
        etat_retour: Optional[str] = None,
        date_retour: Optional[date] = None,
    ) -> Tuple[bool, str]:
        """
        Enregistre la restitution d'un livre, calcule d'éventuelles pénalités de retard
        ou de dégradation, et avertit si un autre étudiant a réservé l'ouvrage.
        """
        code_clean = code_livre.strip().upper()
        livre = self.depot.obtenir_livre(code_clean)
        if livre is None:
            return False, f"Impossible : Aucun livre trouvé avec le code {code_clean}."

        emprunt = self.depot.obtenir_emprunt_actif_par_livre(code_clean)
        if emprunt is None or not livre.est_emprunte:
            return False, f"Impossible : Le livre « {livre.titre} » n'est pas actuellement emprunté."

        jour_retour = date_retour or date.today()
        echeance = parser_date_iso(emprunt.date_retour_prevue)
        jours_retard = calculer_jours_retard(echeance, jour_retour)

        etat_final = (etat_retour or emprunt.etat_depart or EtatExemplaire.BON.value).upper().strip()
        if etat_final not in [e.value for e in EtatExemplaire]:
            etat_final = emprunt.etat_depart

        penalite_fcfa, motifs = calculer_penalite_retour(
            jours_retard=jours_retard,
            etat_depart=emprunt.etat_depart,
            etat_retour=etat_final,
        )

        assert emprunt.id is not None
        self.depot.cloturer_emprunt(
            emprunt_id=emprunt.id,
            code_livre=livre.code,
            date_retour_effective=jour_retour.isoformat(),
            etat_retour=etat_final,
            penalite_fcfa=penalite_fcfa,
        )

        if penalite_fcfa > 0:
            self.depot.ajouter_penalite_usager(
                matricule=emprunt.matricule,
                montant_fcfa=penalite_fcfa,
                emprunt_id=emprunt.id,
                motif=" ; ".join(motifs),
            )

        msg = f"Retour enregistré pour « {livre.titre} » ({livre.code}) par {emprunt.matricule}."
        if penalite_fcfa > 0:
            msg += f" Pénalité appliquée : {penalite_fcfa} FCFA ({', '.join(motifs)})."

        # Vérifier si une réservation est en attente sur ce livre
        reservations = self.depot.lister_reservations_en_attente(livre.code)
        if reservations:
            prochain = reservations[0]
            msg += f" [AVIS RÉSERVATION : Mis de côté pour {prochain.matricule}]."

        return True, msg

    # =========================================================================
    # 4. GESTION DES RETARDS
    # =========================================================================

    def lister_retards(self, date_reference: Optional[date] = None) -> List[Dict[str, object]]:
        """
        Retourne la liste détaillée de tous les emprunts actuellement en retard,
        avec le livre, l'usager, le nombre de jours de retard et l'amende encourue.
        """
        ref = date_reference or date.today()
        emprunts_actifs = self.depot.lister_tous_les_emprunts_actifs()
        retards: List[Dict[str, object]] = []

        for emp in emprunts_actifs:
            if est_emprunt_en_retard(emp, ref):
                echeance = parser_date_iso(emp.date_retour_prevue)
                nb_jours = calculer_jours_retard(echeance, ref)
                livre = self.depot.obtenir_livre(emp.code_livre)
                usager = self.depot.obtenir_usager(emp.matricule)
                amende, _ = calculer_penalite_retour(nb_jours)
                retards.append(
                    {
                        "emprunt": emp,
                        "livre": livre,
                        "usager": usager,
                        "jours_retard": nb_jours,
                        "amende_estimee_fcfa": amende,
                        "echeance_fr": formater_date_fr(echeance),
                    }
                )
        return retards

    # =========================================================================
    # 5. RÉSERVATION & PROLONGATION D'EMPRUNT
    # =========================================================================

    def reserver_livre(self, code_livre: str, matricule: str) -> Tuple[bool, str]:
        """Place une réservation sur un ouvrage actuellement emprunté."""
        code_clean = code_livre.strip().upper()
        mat_clean = matricule.strip().upper()

        livre = self.depot.obtenir_livre(code_clean)
        if livre is None:
            return False, f"Impossible : Livre {code_clean} introuvable."

        if not livre.est_emprunte:
            return False, f"Information : Le livre « {livre.titre} » est disponible en rayon, empruntez-le directement."

        emp_actif = self.depot.obtenir_emprunt_actif_par_livre(code_clean)
        if emp_actif and emp_actif.matricule == mat_clean:
            return False, "Impossible : Vous détenez déjà cet ouvrage."

        existantes = self.depot.lister_reservations_en_attente(code_clean)
        for r in existantes:
            if r.matricule == mat_clean:
                return False, "Impossible : Vous avez déjà une réservation active sur ce livre."

        if self.depot.obtenir_usager(mat_clean) is None:
            self.depot.ajouter_usager(Usager(matricule=mat_clean, nom_complet=f"Usager IIT ({mat_clean})"))

        res = self.depot.creer_reservation(code_clean, mat_clean)
        position = len(existantes) + 1
        return True, f"Réservation enregistrée sur « {livre.titre} » pour {res.matricule} (Position #{position} en file d'attente)."

    def prolonger_emprunt_livre(
        self,
        code_livre: str,
        date_reference: Optional[date] = None,
    ) -> Tuple[bool, str]:
        """Prolonge la durée d'un emprunt en cours si toutes les conditions métier sont réunies."""
        code_clean = code_livre.strip().upper()
        emp = self.depot.obtenir_emprunt_actif_par_livre(code_clean)
        if emp is None:
            return False, f"Impossible : Aucun emprunt actif pour le livre {code_clean}."

        usager = self.depot.obtenir_usager(emp.matricule)
        reservations = self.depot.lister_reservations_en_attente(code_clean)

        autorise, msg, nouvelle_date = verifier_eligibilite_prolongation(
            emprunt=emp,
            usager=usager,
            a_des_reservations_en_attente=(len(reservations) > 0),
            date_reference=date_reference,
        )
        if not autorise or nouvelle_date is None:
            return False, msg

        assert emp.id is not None
        self.depot.prolonger_emprunt(emp.id, nouvelle_date.isoformat())
        return True, f"{msg} Nouveau retour prévu le {formater_date_fr(nouvelle_date)}."

