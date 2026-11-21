"""
Tests unitaires et d'intégration complets pour le projet BiblioIIT.
Couvre les 5 modules : modeles.py, regles.py, depot_sqlite.py, service.py et console.py.
"""

from datetime import date, timedelta
import os
import tempfile
import pytest

from modeles import (
    CategorieLivre,
    Emprunt,
    EtatExemplaire,
    Livre,
    ModeConsultation,
    TypeUsager,
    Usager,
)
from regles import (
    PENALITE_DEGRADATION_FCFA,
    PENALITE_PERTE_FCFA,
    PENALITE_RETARD_PAR_JOUR_FCFA,
    QUOTA_MAX_ENSEIGNANT,
    QUOTA_MAX_ETUDIANT,
    calculer_date_retour_prevue,
    calculer_jours_retard,
    calculer_penalite_retour,
    est_emprunt_en_retard,
    formater_date_fr,
    obtenir_quota_max,
    verifier_eligibilite_emprunt,
    verifier_eligibilite_prolongation,
)
from depot_sqlite import DepotSQLite
from service import ServiceBibliotheque
from console import executer_console


# =============================================================================
# 1. TESTS DU MODULE modeles.py
# =============================================================================

def test_modele_livre_disponibilite_et_format_slide29():
    l4 = Livre(code="L004", titre="Allah n'est pas obligé", auteur="Ahmadou Kourouma", annee=2000)
    l2 = Livre(code="L002", titre="Les Soleils des indépendances", auteur="Ahmadou Kourouma", annee=1968)

    assert l4.est_disponible_pour_emprunt() is True
    assert l4.format_console(None) == "  L004  Allah n'est pas obligé — Ahmadou Kourouma (2000)"
    # Lorsque l'auteur précédent est identique, le format utilise le ditto „ comme sur la Slide 29
    assert l2.format_console("Ahmadou Kourouma") == "  L002  Les Soleils des indépendances — „ (1968)"

    l_sur_place = Livre(
        code="L064",
        titre="Dictionnaire Informatique",
        auteur="Collectif IIT",
        annee=2024,
        mode_consultation=ModeConsultation.SUR_PLACE.value,
    )
    assert l_sur_place.est_disponible_pour_emprunt() is False


# =============================================================================
# 2. TESTS DU MODULE regles.py
# =============================================================================

def test_regles_quotas_et_dates():
    etudiant = Usager(matricule="E2026-001", nom_complet="Loïc ADON", type_usager=TypeUsager.ETUDIANT.value)
    enseignant = Usager(matricule="P2026-001", nom_complet="Prof. Sedrick", type_usager=TypeUsager.ENSEIGNANT.value)

    assert obtenir_quota_max(etudiant) == QUOTA_MAX_ETUDIANT == 3
    assert obtenir_quota_max(enseignant) == QUOTA_MAX_ENSEIGNANT == 5

    d_emp = date(2026, 10, 1)
    d_ret_etu = calculer_date_retour_prevue(d_emp, etudiant)
    assert d_ret_etu == date(2026, 10, 15)
    assert formater_date_fr(d_ret_etu) == "15/10/2026"


def test_regles_calcul_retards_et_penalites():
    echeance = date(2026, 10, 15)
    assert calculer_jours_retard(echeance, date(2026, 10, 15)) == 0
    assert calculer_jours_retard(echeance, date(2026, 10, 20)) == 5

    montant, motifs = calculer_penalite_retour(
        jours_retard=5,
        etat_depart=EtatExemplaire.BON.value,
        etat_retour=EtatExemplaire.ABIME.value,
    )
    assert montant == 5 * PENALITE_RETARD_PAR_JOUR_FCFA + PENALITE_DEGRADATION_FCFA
    assert len(motifs) == 2

    montant_perte, _ = calculer_penalite_retour(
        jours_retard=0,
        etat_depart=EtatExemplaire.NEUF.value,
        etat_retour=EtatExemplaire.PERDU.value,
    )
    assert montant_perte == PENALITE_PERTE_FCFA


def test_regles_eligibilite_emprunt_et_blocages():
    livre = Livre(code="L002", titre="Les Soleils des indépendances", auteur="Ahmadou Kourouma", annee=1968, est_emprunte=True)
    etu = Usager(matricule="E2026-002", nom_complet="Aya Kouassi")

    ok, msg = verifier_eligibilite_emprunt(livre, etu, [])
    assert ok is False
    assert msg == "Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté"

    # Test quota atteint (3 emprunts actifs)
    livre.est_emprunte = False
    trois_emprunts = [
        Emprunt(id=i, code_livre=f"L00{i}", matricule="E2026-002", date_emprunt="2026-10-01", date_retour_prevue="2099-12-31")
        for i in range(1, 4)
    ]
    ok_quota, msg_quota = verifier_eligibilite_emprunt(livre, etu, trois_emprunts)
    assert ok_quota is False
    assert "Quota maximal atteint" in msg_quota


# =============================================================================
# 3. TESTS DU MODULE depot_sqlite.py (Catalogue de 65+ livres)
# =============================================================================

@pytest.fixture
def service_temp():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    depot = DepotSQLite(chemin_db=path, peupler_par_defaut=True)
    srv = ServiceBibliotheque(depot)
    yield srv
    depot.fermer()
    if os.path.exists(path):
        os.remove(path)


def test_depot_catalogue_contient_au_moins_60_livres(service_temp: ServiceBibliotheque):
    tous_les_livres = service_temp.obtenir_catalogue_complet()
    assert len(tous_les_livres) >= 60

    # Vérifier la présence de Kourouma (L002 et L004 de la Slide 29)
    res_kourouma = service_temp.rechercher("Kourouma")
    codes = [l.code for l in res_kourouma]
    assert "L004" in codes
    assert "L002" in codes


# =============================================================================
# 4. TESTS DU MODULE service.py (Scénario exact Slide 29 + Règles avancées)
# =============================================================================

def test_scenario_exact_slide_29(service_temp: ServiceBibliotheque):
    # 1. Emprunt de L002 par E2026-001 le 01/10/2026 -> retour prévu le 15/10/2026
    ok1, msg1 = service_temp.emprunter_livre("L002", "E2026-001", date_emprunt=date(2026, 10, 1))
    assert ok1 is True
    assert msg1 == "Emprunt enregistré. Retour prévu le 15/10/2026."

    # 2. Tentative d'emprunt du même livre L002 par E2026-002 -> refusé avec le message exact
    ok2, msg2 = service_temp.emprunter_livre("L002", "E2026-002", date_emprunt=date(2026, 10, 1))
    assert ok2 is False
    assert msg2 == "Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté"

    # 3. Réservation de L002 par E2026-002 puis retour par E2026-001
    ok_res, msg_res = service_temp.reserver_livre("L002", "E2026-002")
    assert ok_res is True
    assert "Position #1" in msg_res

    # La prolongation doit être refusée car L002 est réservé par E2026-002
    ok_prol, msg_prol = service_temp.prolonger_emprunt_livre("L002", date_reference=date(2026, 10, 5))
    assert ok_prol is False
    assert "réservé" in msg_prol

    # Retour de L002 avec 3 jours de retard (le 18/10/2026) -> pénalité + avis de réservation
    ok_ret, msg_ret = service_temp.rendre_livre("L002", date_retour=date(2026, 10, 18))
    assert ok_ret is True
    assert "600 FCFA" in msg_ret
    assert "E2026-002" in msg_ret


def test_consultation_sur_place_et_prolongation(service_temp: ServiceBibliotheque):
    # L064 est un dictionnaire consultable uniquement sur place
    ok_usu, msg_usu = service_temp.emprunter_livre("L064", "E2026-001")
    assert ok_usu is False
    assert "uniquement sur place" in msg_usu

    # Emprunt normal de L016 et prolongation
    ok_emp, _ = service_temp.emprunter_livre("L016", "E2026-003", date_emprunt=date(2026, 10, 1))
    assert ok_emp is True
    ok_prol, msg_prol = service_temp.prolonger_emprunt_livre("L016", date_reference=date(2026, 10, 10))
    assert ok_prol is True
    assert "22/10/2026" in msg_prol


# =============================================================================
# 5. TEST DE LA CONSOLE INTERACTIVE (console.py)
# =============================================================================

def test_session_interactive_console(capsys):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)

    reponses = iter([
        "1", "Kourouma",
        "2", "L002", "E2026-001",
        "2", "L002", "E2026-002",
        "4",
        "0",
    ])
    executer_console(chemin_db=path, input_fn=lambda _: next(reponses))
    sortie = capsys.readouterr().out

    assert "Allah n'est pas obligé — Ahmadou Kourouma (2000)" in sortie
    assert "Les Soleils des indépendances — „ (1968)" in sortie
    assert "Emprunt enregistré. Retour prévu le" in sortie
    assert "Impossible : Le livre « Les Soleils des indépendances » est déjà emprunté" in sortie

    if os.path.exists(path):
        os.remove(path)

