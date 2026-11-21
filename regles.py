"""
regles.py — Règles métier pures de la bibliothèque universitaire BiblioIIT.
Institut Ivoirien de Technologie (IIT) — Séance 4.

Ce module contient toutes les règles de gestion réelles d'une bibliothèque :
- Quotas et durées d'emprunt différenciés (Étudiant vs Enseignant)
- Calcul des dates de retour et formatage français (JJ/MM/AAAA)
- Contrôles d'éligibilité à l'emprunt (disponibilité, état, mode sur place, quota, retards, suspensions, amendes)
- Règles de prolongation (1 seule fois, hors retard, sans réservation concurrente)
- Calcul des jours de retard et des pénalités financières (FCFA) pour retard, dégradation ou perte
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from modeles import (
    Emprunt,
    EtatExemplaire,
    Livre,
    ModeConsultation,
    TypeUsager,
    Usager,
)

# =============================================================================
# CONSTANTES MÉTIER DE LA BIBLIOTHÈQUE DE L'IIT
# =============================================================================

QUOTA_MAX_ETUDIANT: int = 3
QUOTA_MAX_ENSEIGNANT: int = 5

DUREE_EMPRUNT_ETUDIANT_JOURS: int = 14
DUREE_EMPRUNT_ENSEIGNANT_JOURS: int = 30

DUREE_PROLONGATION_ETUDIANT_JOURS: int = 7
DUREE_PROLONGATION_ENSEIGNANT_JOURS: int = 15
MAX_PROLONGATIONS_PAR_EMPRUNT: int = 1

PENALITE_RETARD_PAR_JOUR_FCFA: int = 200
PENALITE_DEGRADATION_FCFA: int = 2500
PENALITE_PERTE_FCFA: int = 10000
SEUIL_BLOCAGE_PENALITES_FCFA: int = 2000


# =============================================================================
# FONCTIONS DE CALCUL DES QUOTAS, DATES ET RETARDS
# =============================================================================

def parser_date_iso(date_str: str) -> date:
    """Convertit une chaîne ISO 'YYYY-MM-DD' en objet datetime.date."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def formater_date_fr(d: date) -> str:
    """Formate une date au format français JJ/MM/AAAA (ex. '15/10/2026' comme sur la Slide 29)."""
    return d.strftime("%d/%m/%Y")


def obtenir_quota_max(usager: Usager) -> int:
    """Retourne le nombre maximal d'emprunts simultanés autorisés selon le profil."""
    if usager.type_usager == TypeUsager.ENSEIGNANT.value:
        return QUOTA_MAX_ENSEIGNANT
    return QUOTA_MAX_ETUDIANT


def obtenir_duree_emprunt_jours(usager: Optional[Usager] = None) -> int:
    """Retourne la durée standard d'un prêt en jours selon le profil de l'usager."""
    if usager and usager.type_usager == TypeUsager.ENSEIGNANT.value:
        return DUREE_EMPRUNT_ENSEIGNANT_JOURS
    return DUREE_EMPRUNT_ETUDIANT_JOURS


def calculer_date_retour_prevue(
    date_emprunt: date,
    usager: Optional[Usager] = None,
) -> date:
    """Calcule la date limite de retour d'un ouvrage à partir de la date d'emprunt."""
    jours = obtenir_duree_emprunt_jours(usager)
    return date_emprunt + timedelta(days=jours)


def calculer_jours_retard(
    date_retour_prevue: date,
    date_reference: Optional[date] = None,
) -> int:
    """
    Calcule le nombre de jours de retard par rapport à la date de retour prévue.
    Retourne 0 si la date de référence est antérieure ou égale à l'échéance.
    """
    ref = date_reference or date.today()
    delta = (ref - date_retour_prevue).days
    return max(0, delta)


def est_emprunt_en_retard(
    emprunt: Emprunt,
    date_reference: Optional[date] = None,
) -> bool:
    """Détermine si un emprunt actif a dépassé sa date de retour prévue."""
    if not emprunt.est_actif:
        return False
    echeance = parser_date_iso(emprunt.date_retour_prevue)
    return calculer_jours_retard(echeance, date_reference) > 0


def calculer_penalite_retour(
    jours_retard: int,
    etat_depart: str = EtatExemplaire.BON.value,
    etat_retour: str = EtatExemplaire.BON.value,
) -> Tuple[int, List[str]]:
    """
    Calcule la pénalité totale en FCFA lors du retour d'un livre,
    en tenant compte à la fois du retard et d'une éventuelle dégradation ou perte.
    Retourne (montant_total_fcfa, liste_des_motifs).
    """
    total = 0
    motifs: List[str] = []

    if jours_retard > 0:
        amende_retard = jours_retard * PENALITE_RETARD_PAR_JOUR_FCFA
        total += amende_retard
        motifs.append(f"Retard de {jours_retard} jour(s) ({amende_retard} FCFA)")

    if etat_retour == EtatExemplaire.PERDU.value:
        total += PENALITE_PERTE_FCFA
        motifs.append(f"Ouvrage déclaré perdu — forfait remplacement ({PENALITE_PERTE_FCFA} FCFA)")
    elif (
        etat_retour == EtatExemplaire.ABIME.value
        and etat_depart in (EtatExemplaire.NEUF.value, EtatExemplaire.BON.value)
    ):
        total += PENALITE_DEGRADATION_FCFA
        motifs.append(f"Dégradation constatée au retour ({PENALITE_DEGRADATION_FCFA} FCFA)")

    return total, motifs


# =============================================================================
# CONTRÔLES D'ÉLIGIBILITÉ À L'EMPRUNT & À LA PROLONGATION
# =============================================================================

def verifier_eligibilite_emprunt(
    livre: Optional[Livre],
    usager: Optional[Usager],
    emprunts_actifs_usager: List[Emprunt],
    matricule_reservataire_prioritaire: Optional[str] = None,
    date_reference: Optional[date] = None,
) -> Tuple[bool, str]:
    """
    Vérifie toutes les règles métier avant d'autoriser un emprunt.
    Retourne (autorise: bool, message_explicatif: str).
    Respecte à la lettre le message de la Slide 29 lorsqu'un livre est déjà emprunté :
    'Impossible : Le livre « <Titre> » est déjà emprunté'
    """
    if livre is None:
        return False, "Impossible : Code de livre introuvable dans le catalogue."

    # 1. Livre déjà emprunté (Message exact de la Slide 29)
    if livre.est_emprunte:
        return False, f"Impossible : Le livre « {livre.titre} » est déjà emprunté"

    # 2. État physique du livre
    if livre.etat == EtatExemplaire.EN_REPARATION.value:
        return False, f"Impossible : Le livre « {livre.titre} » est actuellement en atelier de reliure/réparation."
    if livre.etat == EtatExemplaire.PERDU.value:
        return False, f"Impossible : Le livre « {livre.titre} » est signalé comme perdu."

    # 3. Ouvrage en consultation sur place uniquement (usuels, dictionnaires)
    if livre.mode_consultation == ModeConsultation.SUR_PLACE.value:
        return False, f"Impossible : « {livre.titre} » est un usuel consultable uniquement sur place."

    # 4. File de réservation prioritaire
    if (
        matricule_reservataire_prioritaire is not None
        and usager is not None
        and matricule_reservataire_prioritaire != usager.matricule
    ):
        return (
            False,
            f"Impossible : Le livre « {livre.titre} » est réservé en priorité pour le matricule {matricule_reservataire_prioritaire}.",
        )

    # 5. Vérifications sur l'usager (si l'usager est fourni)
    if usager is not None:
        if usager.est_suspendu:
            return False, f"Impossible : Le compte usager {usager.matricule} ({usager.nom_complet}) est suspendu."

        if usager.penalites_impayees_fcfa >= SEUIL_BLOCAGE_PENALITES_FCFA:
            return (
                False,
                f"Impossible : Pénalités impayées ({usager.penalites_impayees_fcfa} FCFA) supérieures au seuil autorisé ({SEUIL_BLOCAGE_PENALITES_FCFA} FCFA).",
            )

        # Blocage si l'usager a au moins un emprunt actuellement en retard
        for emp in emprunts_actifs_usager:
            if est_emprunt_en_retard(emp, date_reference):
                return (
                    False,
                    f"Impossible : L'usager {usager.matricule} possède un emprunt en retard ({emp.code_livre}). Régularisez d'abord ce retour.",
                )

        # Vérification du quota maximal d'emprunts simultanés
        quota_max = obtenir_quota_max(usager)
        if len(emprunts_actifs_usager) >= quota_max:
            return (
                False,
                f"Impossible : Quota maximal atteint ({len(emprunts_actifs_usager)}/{quota_max} livres empruntés pour le profil {usager.type_usager}).",
            )

    return True, "Emprunt autorisé."


def verifier_eligibilite_prolongation(
    emprunt: Optional[Emprunt],
    usager: Optional[Usager],
    a_des_reservations_en_attente: bool,
    date_reference: Optional[date] = None,
) -> Tuple[bool, str, Optional[date]]:
    """
    Vérifie si un emprunt actif peut être prolongé.
    Retourne (autorise, message, nouvelle_date_retour_prevue).
    """
    if emprunt is None or not emprunt.est_actif:
        return False, "Impossible : Aucun emprunt actif trouvé pour ce livre.", None

    if emprunt.prolongations >= MAX_PROLONGATIONS_PAR_EMPRUNT:
        return (
            False,
            f"Impossible : Cet emprunt a déjà fait l'objet du maximum autorisé de {MAX_PROLONGATIONS_PAR_EMPRUNT} prolongation(s).",
            None,
        )

    if est_emprunt_en_retard(emprunt, date_reference):
        return False, "Impossible : Un emprunt déjà en retard ne peut pas être prolongé.", None

    if a_des_reservations_en_attente:
        return (
            False,
            "Impossible : Un autre usager a réservé ce livre, la prolongation est refusée.",
            None,
        )

    jours_bonus = (
        DUREE_PROLONGATION_ENSEIGNANT_JOURS
        if (usager and usager.type_usager == TypeUsager.ENSEIGNANT.value)
        else DUREE_PROLONGATION_ETUDIANT_JOURS
    )
    echeance_actuelle = parser_date_iso(emprunt.date_retour_prevue)
    nouvelle_echeance = echeance_actuelle + timedelta(days=jours_bonus)
    return True, f"Prolongation de {jours_bonus} jours accordée.", nouvelle_echeance

