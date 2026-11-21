"""
modeles.py — Modèles de données du système de gestion de bibliothèque BiblioIIT.
Institut Ivoirien de Technologie (IIT) — Séance 4.

Représente fidèlement les entités réelles d'une bibliothèque universitaire :
- Livre (code, ISBN, titre, auteur, année, catégorie, rayon/cote, état physique, mode de consultation)
- Usager (matricule, nom, profil Étudiant/Enseignant, filière, statut actif/suspendu, solde pénalités)
- Emprunt (id, code_livre, matricule, dates d'emprunt/échéance/retour, prolongations, état au retour)
- Reservation (file d'attente horodatée sur un ouvrage emprunté)
- Sanction (amende de retard, dégradation ou perte en FCFA)
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class CategorieLivre(str, Enum):
    """Grandes catégories thématiques du fonds documentaire de l'IIT."""
    LITTERATURE = "Littérature Africaine & Classique"
    CYBER_SCIENCE = "Cybersécurité & Cyber Science"
    RESEAUX = "Réseaux & Télécommunications"
    GENIE_LOGICIEL = "Génie Logiciel, Web & Base de Données"
    MATHS_IA = "Mathématiques, Data & IA"
    USUELS = "Usuels, Dictionnaires & Références"


class EtatExemplaire(str, Enum):
    """État physique réel d'un ouvrage en bibliothèque."""
    NEUF = "NEUF"
    BON = "BON"
    ABIME = "ABIME"
    EN_REPARATION = "EN_REPARATION"
    PERDU = "PERDU"


class ModeConsultation(str, Enum):
    """Politique de prêt d'un ouvrage (prêt à domicile ou consultation sur place uniquement)."""
    EMPRUNTABLE = "EMPRUNTABLE"
    SUR_PLACE = "SUR_PLACE"


class TypeUsager(str, Enum):
    """Profil d'usager au sein de l'Institut Ivoirien de Technologie."""
    ETUDIANT = "ETUDIANT"
    ENSEIGNANT = "ENSEIGNANT"


class StatutReservation(str, Enum):
    """Statut d'une réservation dans la file d'attente."""
    EN_ATTENTE = "EN_ATTENTE"
    HONOREE = "HONOREE"
    ANNULEE = "ANNULEE"


@dataclass
class Livre:
    """Représente un ouvrage physique du catalogue de la bibliothèque de l'IIT."""
    code: str
    titre: str
    auteur: str
    annee: int
    isbn: str = "978-2-00000-000-0"
    categorie: str = CategorieLivre.LITTERATURE.value
    rayon: str = "RAYON-GEN-01"
    etat: str = EtatExemplaire.BON.value
    mode_consultation: str = ModeConsultation.EMPRUNTABLE.value
    editeur: str = "Éditions Universitaires"
    est_emprunte: bool = False

    def est_disponible_pour_emprunt(self) -> bool:
        """Vérifie si l'ouvrage peut quitter la bibliothèque."""
        return (
            not self.est_emprunte
            and self.mode_consultation == ModeConsultation.EMPRUNTABLE.value
            and self.etat in (EtatExemplaire.NEUF.value, EtatExemplaire.BON.value, EtatExemplaire.ABIME.value)
        )

    def format_console(self, auteur_precedent: Optional[str] = None) -> str:
        """
        Formatage exact conforme à la session réelle de la Slide 29 :
        L004  Allah n'est pas obligé — Ahmadou Kourouma (2000)
        L002  Les Soleils des indépendances — „ (1968)
        """
        aff_auteur = "„" if (auteur_precedent and auteur_precedent == self.auteur) else self.auteur
        return f"  {self.code}  {self.titre} — {aff_auteur} ({self.annee})"


@dataclass
class Usager:
    """Représente un membre inscrit à la bibliothèque de l'IIT (Étudiant ou Enseignant)."""
    matricule: str
    nom_complet: str
    type_usager: str = TypeUsager.ETUDIANT.value
    filiere_ou_departement: str = "Licence Cyber Science"
    email: str = ""
    telephone: str = ""
    est_suspendu: bool = False
    penalites_impayees_fcfa: int = 0
    date_inscription: str = field(default_factory=lambda: date.today().isoformat())


@dataclass
class Emprunt:
    """Représente un prêt d'ouvrage enregistré à la banque de prêt."""
    id: Optional[int]
    code_livre: str
    matricule: str
    date_emprunt: str  # Format ISO YYYY-MM-DD
    date_retour_prevue: str  # Format ISO YYYY-MM-DD
    date_retour_effective: Optional[str] = None
    prolongations: int = 0
    etat_depart: str = EtatExemplaire.BON.value
    etat_retour: Optional[str] = None
    penalite_fcfa: int = 0
    commentaire: str = ""

    @property
    def est_actif(self) -> bool:
        """Un emprunt est actif tant qu'il n'a pas de date de retour effective."""
        return self.date_retour_effective is None


@dataclass
class Reservation:
    """Représente une réservation en file d'attente sur un livre actuellement emprunté."""
    id: Optional[int]
    code_livre: str
    matricule: str
    date_reservation: str
    statut: str = StatutReservation.EN_ATTENTE.value


@dataclass
class Sanction:
    """Représente une pénalité financière ou disciplinaire liée à un retard, une dégradation ou une perte."""
    id: Optional[int]
    matricule: str
    emprunt_id: Optional[int]
    motif: str
    montant_fcfa: int
    date_sanction: str
    est_reglee: bool = False

