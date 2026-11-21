"""
depot_sqlite.py — Couche de persistance SQLite du système BiblioIIT.
Institut Ivoirien de Technologie (IIT) — Séance 4.

Gère la base de données relationnelle SQLite3 :
- Création du schéma complet (livres, usagers, emprunts, reservations, sanctions)
- Amorçage initial automatique (Seed) d'un catalogue réaliste de 65 ouvrages (L001 à L065)
  et de 15 usagers de l'IIT (Étudiants et Enseignants)
- Opérations CRUD transactionnelles pour les livres, usagers, emprunts, réservations et sanctions
"""

import sqlite3
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from modeles import (
    CategorieLivre,
    Emprunt,
    EtatExemplaire,
    Livre,
    ModeConsultation,
    Reservation,
    Sanction,
    StatutReservation,
    TypeUsager,
    Usager,
)


# =============================================================================
# CATALOGUE INITIAL DE LA BIBLIOTHÈQUE DE L'IIT (65 OUVRAGES : L001 À L065)
# =============================================================================

CATALOGUE_INITIAL_65_LIVRES: List[Tuple[str, str, str, int, str, str, str, str, str, str]] = [
    # --- 1. LITTÉRATURE AFRICAINE, IVOIRIENNE & CLASSIQUE (L001 à L015) ---
    # L002 et L004 correspondent exactement à la Slide 29 du cours !
    ("L001", "Climbié", "Bernard Binlin Dadié", 1956, "978-2-7087-0101-1", CategorieLivre.LITTERATURE.value, "RAYON-LIT-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Présence Africaine"),
    ("L002", "Les Soleils des indépendances", "Ahmadou Kourouma", 1968, "978-2-02-002591-1", CategorieLivre.LITTERATURE.value, "RAYON-LIT-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Éditions du Seuil"),
    ("L003", "Monnè, outrages et défis", "Ahmadou Kourouma", 1990, "978-2-02-011426-4", CategorieLivre.LITTERATURE.value, "RAYON-LIT-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Éditions du Seuil"),
    ("L004", "Allah n'est pas obligé", "Ahmadou Kourouma", 2000, "978-2-02-041242-1", CategorieLivre.LITTERATURE.value, "RAYON-LIT-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions du Seuil"),
    ("L005", "En attendant le vote des bêtes sauvages", "Ahmadou Kourouma", 1998, "978-2-02-033443-3", CategorieLivre.LITTERATURE.value, "RAYON-LIT-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Éditions du Seuil"),
    ("L006", "Le Pagne noir", "Bernard Binlin Dadié", 1955, "978-2-7087-0102-8", CategorieLivre.LITTERATURE.value, "RAYON-LIT-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Présence Africaine"),
    ("L007", "Amkoullel, l'enfant peul", "Amadou Hampâté Bâ", 1991, "978-2-7427-0103-2", CategorieLivre.LITTERATURE.value, "RAYON-LIT-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Actes Sud"),
    ("L008", "L'Étrange Destin de Wangrin", "Amadou Hampâté Bâ", 1973, "978-2-264-00104-9", CategorieLivre.LITTERATURE.value, "RAYON-LIT-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "10/18"),
    ("L009", "L'Enfant noir", "Camara Laye", 1953, "978-2-266-00105-6", CategorieLivre.LITTERATURE.value, "RAYON-LIT-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Plon"),
    ("L010", "Une si longue lettre", "Mariama Bâ", 1979, "978-2-84261-106-3", CategorieLivre.LITTERATURE.value, "RAYON-LIT-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Nouvelles Éditions Africaines"),
    ("L011", "Le Monde s'effondre", "Chinua Achebe", 1958, "978-2-7087-0107-3", CategorieLivre.LITTERATURE.value, "RAYON-LIT-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Présence Africaine"),
    ("L012", "Reine Pokou, concerto pour un sacrifice", "Véronique Tadjo", 2005, "978-2-7427-5508-0", CategorieLivre.LITTERATURE.value, "RAYON-LIT-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Actes Sud"),
    ("L013", "Les Bouts de bois de Dieu", "Ousmane Sembène", 1960, "978-2-266-00109-4", CategorieLivre.LITTERATURE.value, "RAYON-LIT-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Pocket"),
    ("L014", "Chants d'ombre", "Léopold Sédar Senghor", 1945, "978-2-02-001110-5", CategorieLivre.LITTERATURE.value, "RAYON-LIT-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Éditions du Seuil"),
    ("L015", "Sous l'orage", "Seydou Badian", 1957, "978-2-7087-0115-8", CategorieLivre.LITTERATURE.value, "RAYON-LIT-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Présence Africaine"),

    # --- 2. CYBERSÉCURITÉ & CYBER SCIENCE (L016 à L029) ---
    ("L016", "Sécurité informatique : Ethical Hacking et Pentest", "ACISSI", 2023, "978-2-409-03816-7", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L017", "Cryptographie appliquée : Algorithmes et protocoles", "Bruce Schneier", 2015, "978-2-7117-8617-6", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Vuibert"),
    ("L018", "L'Art de la guerre cybernétique et défense SOC", "Stéphane Bortzmeyer", 2022, "978-2-212-67818-5", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L019", "Forensique numérique et réponse aux incidents", "Sébastien Larinier", 2024, "978-2-409-04219-5", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L020", "Sécurité des applications Web : Guide OWASP Top 10", "Damien Bancal", 2023, "978-2-212-67920-5", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L021", "Kali Linux : Audit de sécurité et tests d'intrusion", " Cédric Foll", 2023, "978-2-409-03921-8", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L022", "Gouvernance de la cybersécurité et norme ISO 27001", "Solange Ghernaouti", 2022, "978-2-10-083522-5", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Dunod"),
    ("L023", "Analyse de malwares et rétro-ingénierie", "Michael Sikorski", 2020, "978-1-59327-290-6", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "No Starch Press"),
    ("L024", "Sécurité Active Directory et durcissement Windows", "Paul Rascagnères", 2024, "978-2-409-04424-3", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L025", "Durcissement et sécurité des serveurs Linux", "Denis Bodor", 2023, "978-2-212-67725-6", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L026", "Détection d'intrusion avec Suricata, Zeek et SIEM", "Éric Leblond", 2023, "978-2-409-04026-9", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L027", "OSINT : Techniques d'investigation en sources ouvertes", "Michael Bazzell", 2023, "978-2-212-68027-0", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L028", "Cryptologie moderne : De César à la cryptographie post-quantique", "Jean-Philippe Aumasson", 2021, "978-2-10-082128-0", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Dunod"),
    ("L029", "Sécurité du Cloud et des conteneurs Docker/Kubernetes", "Liz Rice", 2022, "978-2-212-67629-7", CategorieLivre.CYBER_SCIENCE.value, "RAYON-CYB-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "O'Reilly"),

    # --- 3. RÉSEAUX INFORMATIQUES & TÉLÉCOMMUNICATIONS (L030 à L041) ---
    ("L030", "Réseaux informatiques : Notions fondamentales (TCP/IP, VLAN)", "José Dordoigne", 2024, "978-2-409-04330-7", CategorieLivre.RESEAUX.value, "RAYON-RES-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L031", "Réseaux — Architecture, protocoles et couches OSI", "Andrew Tanenbaum", 2021, "978-2-326-00231-9", CategorieLivre.RESEAUX.value, "RAYON-RES-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Pearson"),
    ("L032", "Préparation à la certification Cisco CCNA 200-301", "Wendell Odom", 2023, "978-2-326-00332-3", CategorieLivre.RESEAUX.value, "RAYON-RES-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Cisco Press"),
    ("L033", "Analyse de trafic réseau avec Wireshark", "Chris Sanders", 2020, "978-2-212-67533-7", CategorieLivre.RESEAUX.value, "RAYON-RES-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L034", "Administration système et réseau sous Linux Debian/Ubuntu", "Raphaël Hertzog", 2023, "978-2-212-67834-5", CategorieLivre.RESEAUX.value, "RAYON-RES-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L035", "Services réseaux : DNS, DHCP, Pare-feu pfSense et VPN", "Nicolas Bonnet", 2022, "978-2-409-03735-1", CategorieLivre.RESEAUX.value, "RAYON-RES-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L036", "Routage dynamique BGP, OSPF et architectures FAI", "Guy Pujolle", 2022, "978-2-212-67636-5", CategorieLivre.RESEAUX.value, "RAYON-RES-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L037", "Réseaux sans fil Wi-Fi 6, 5G et sécurité radio", "Pierre Lecoy", 2023, "978-2-7462-4937-0", CategorieLivre.RESEAUX.value, "RAYON-RES-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Lavoisier"),
    ("L038", "Virtualisation d'infrastructures avec Proxmox et VMware", " Philippe Nicolas", 2024, "978-2-409-04538-7", CategorieLivre.RESEAUX.value, "RAYON-RES-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L039", "IPv6 : Théorie, déploiement et sécurité", "Gisèle Cizault", 2021, "978-2-95324-039-9", CategorieLivre.RESEAUX.value, "RAYON-RES-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Institut Télécom"),
    ("L040", "Supervision réseau et IT avec Zabbix, Prometheus et Grafana", "Olivier Mazoyer", 2023, "978-2-409-04140-2", CategorieLivre.RESEAUX.value, "RAYON-RES-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L041", "Support IT, Helpdesk et gestion de parc GLPI / ITIL", "Jean-Luc Baud", 2022, "978-2-409-03641-5", CategorieLivre.RESEAUX.value, "RAYON-RES-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),

    # --- 4. GÉNIE LOGICIEL, PROGRAMMATION, WEB & BDD (L042 à L055) ---
    ("L042", "Apprendre à programmer avec Python 3", "Gérard Swinnen", 2021, "978-2-212-67542-9", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L043", "Python pour la Data Science et l'automatisation", "Wes McKinney", 2023, "978-2-212-67943-4", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "O'Reilly"),
    ("L044", "Clean Code : Coder proprement", "Robert C. Martin", 2019, "978-2-326-00144-2", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Pearson"),
    ("L045", "Design Patterns : Catalogue de modèles de conception", "Erich Gamma", 2018, "978-2-7117-4845-7", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Vuibert"),
    ("L046", "HTML5, CSS3 et Tailwind CSS : Conception Web Responsive", "Christophe Aubry", 2024, "978-2-409-04446-5", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Éditions ENI"),
    ("L047", "JavaScript moderne : Du DOM aux architectures asynchrones", "Marijn Haverbeke", 2023, "978-2-212-67847-5", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L048", "Bases de données relationnelles : SQL, SQLite et PostgreSQL", "Christian Soutou", 2022, "978-2-212-67648-8", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L049", "Algorithmique — Structures de données et complexité", "Thomas H. Cormen", 2022, "978-2-10-082949-1", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Dunod"),
    ("L050", "Git et GitHub : Gestion de versions et intégration continue", "Scott Chacon", 2023, "978-2-212-67750-8", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),
    ("L051", "Développement Web Back-End avec Django et FastAPI", "William S. Vincent", 2023, "978-1-73546-722-1", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "WelcomeToCode"),
    ("L052", "Tests logiciels en Python avec pytest et TDD", "Brian Okken", 2022, "978-1-68050-860-4", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-03", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Pragmatic Bookshelf"),
    ("L053", "Architecture logicielle propre et Hexagonale", "Robert C. Martin", 2020, "978-2-326-00253-1", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Pearson"),
    ("L054", "Systèmes d'exploitation : Processus, mémoire et fichiers", "Andrew Tanenbaum", 2020, "978-2-326-00154-1", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Pearson"),
    ("L055", "Programmation orientée objet et modélisation UML 2.5", "Pascal Roques", 2021, "978-2-212-67555-9", CategorieLivre.GENIE_LOGICIEL.value, "RAYON-DEV-03", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Eyrolles"),

    # --- 5. MATHÉMATIQUES, DATA, IA & USUELS (L056 à L065) ---
    ("L056", "Algèbre linéaire et applications pour l'informatique", "David C. Lay", 2021, "978-2-8073-0656-1", CategorieLivre.MATHS_IA.value, "RAYON-MAT-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "De Boeck"),
    ("L057", "Mathématiques discrètes, graphes et logique booléenne", "Kenneth H. Rosen", 2020, "978-2-8073-0557-1", CategorieLivre.MATHS_IA.value, "RAYON-MAT-01", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "De Boeck"),
    ("L058", "Probabilités, statistique et processus aléatoires", "Patrick Bogaert", 2021, "978-2-8073-2958-4", CategorieLivre.MATHS_IA.value, "RAYON-MAT-01", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "De Boeck"),
    ("L059", "Machine Learning avec Scikit-Learn, Keras et TensorFlow", "Aurélien Géron", 2023, "978-2-10-084959-8", CategorieLivre.MATHS_IA.value, "RAYON-MAT-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Dunod"),
    ("L060", "Intelligence Artificielle : Une approche moderne", "Stuart Russell", 2021, "978-2-326-00260-9", CategorieLivre.MATHS_IA.value, "RAYON-MAT-02", EtatExemplaire.NEUF.value, ModeConsultation.EMPRUNTABLE.value, "Pearson"),
    ("L061", "Théorie de l'information, codage et compression", "Thomas M. Cover", 2019, "978-0-471-24195-9", CategorieLivre.MATHS_IA.value, "RAYON-MAT-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Wiley"),
    ("L062", "Recherche opérationnelle et optimisation combinatoire", "Michel Bierlaire", 2020, "978-2-88915-062-5", CategorieLivre.MATHS_IA.value, "RAYON-MAT-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "PPUR"),
    ("L063", "Arithmétique modulaire et théorie des nombres pour la crypto", "Pierre Samuel", 2018, "978-2-7056-6563-0", CategorieLivre.MATHS_IA.value, "RAYON-MAT-02", EtatExemplaire.BON.value, ModeConsultation.EMPRUNTABLE.value, "Hermann"),
    ("L064", "Dictionnaire encyclopédique de l'informatique et des réseaux", "Collectif IIT", 2024, "978-2-10-085064-8", CategorieLivre.USUELS.value, "RAYON-USU-01", EtatExemplaire.NEUF.value, ModeConsultation.SUR_PLACE.value, "Dunod"),
    ("L065", "Encyclopédie de la Cybersécurité et des Normes Africaines", "Collectif IIT", 2025, "978-2-10-085065-5", CategorieLivre.USUELS.value, "RAYON-USU-01", EtatExemplaire.NEUF.value, ModeConsultation.SUR_PLACE.value, "Presses Universitaires IIT"),
]

USAGERS_INITIAUX_IIT: List[Tuple[str, str, str, str, str, str]] = [
    ("E2026-001", "Loïc Otniel ADON", TypeUsager.ETUDIANT.value, "Licence 2 Cyber Science", "loic.adon@iit.ci", "0709861624"),
    ("E2026-002", "Aya Marie Kouassi", TypeUsager.ETUDIANT.value, "Licence 2 Cyber Science", "aya.kouassi@iit.ci", "0701020304"),
    ("E2026-003", "Koffi Emmanuel Konan", TypeUsager.ETUDIANT.value, "Licence 3 Génie Logiciel", "koffi.konan@iit.ci", "0502030405"),
    ("E2026-004", "Fatou Bamba", TypeUsager.ETUDIANT.value, "Licence 1 Réseaux & Télécoms", "fatou.bamba@iit.ci", "0103040506"),
    ("E2026-005", "Jean-Marc Touré", TypeUsager.ETUDIANT.value, "Licence 2 Cyber Science", "jeanmarc.toure@iit.ci", "0704050607"),
    ("E2026-006", "Aminata Diallo", TypeUsager.ETUDIANT.value, "Master 1 Data & IA", "aminata.diallo@iit.ci", "0705060708"),
    ("E2026-007", "Cédric N'Guessan", TypeUsager.ETUDIANT.value, "Licence 3 Génie Logiciel", "cedric.nguessan@iit.ci", "0506070809"),
    ("E2026-008", "Estelle Yao", TypeUsager.ETUDIANT.value, "Licence 1 Informatique", "estelle.yao@iit.ci", "0707080910"),
    ("E2026-009", "Ibrahim Ouattara", TypeUsager.ETUDIANT.value, "Licence 2 Réseaux & Télécoms", "ibrahim.ouattara@iit.ci", "0108091011"),
    ("E2026-010", "Grâce Brou", TypeUsager.ETUDIANT.value, "Licence 3 Cyber Science", "grace.brou@iit.ci", "0709101112"),
    ("E2026-011", "Yao Stéphane Aka", TypeUsager.ETUDIANT.value, "Master 2 Cybersécurité", "stephane.aka@iit.ci", "0510111213"),
    ("E2026-012", "Mariam Coulibaly", TypeUsager.ETUDIANT.value, "Licence 2 Génie Logiciel", "mariam.coulibaly@iit.ci", "0711121314"),
    ("P2026-001", "Prof. Sedrick Gaël", TypeUsager.ENSEIGNANT.value, "Département Informatique & Génie Logiciel", "sedrick.gael@iit.ci", "0700000001"),
    ("P2026-002", "Dr. Kouamé Assi", TypeUsager.ENSEIGNANT.value, "Département Cybersécurité & Réseaux", "kouame.assi@iit.ci", "0700000002"),
    ("P2026-003", "Dr. Clarisse Zadi", TypeUsager.ENSEIGNANT.value, "Département Mathématiques & IA", "clarisse.zadi@iit.ci", "0700000003"),
]


class DepotSQLite:
    """Dépôt SQLite gérant l'ensemble des données persistantes de BiblioIIT."""

    def __init__(self, chemin_db: str = "biblio_iit.db", peupler_par_defaut: bool = True) -> None:
        self.chemin_db = chemin_db
        self._conn = sqlite3.connect(self.chemin_db)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self.initialiser_schema()
        if peupler_par_defaut:
            self.peupler_donnees_initiales()

    def fermer(self) -> None:
        """Ferme proprement la connexion SQLite."""
        if self._conn:
            self._conn.close()

    def initialiser_schema(self) -> None:
        """Crée les tables relationnelles si elles n'existent pas encore."""
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS livres (
                    code TEXT PRIMARY KEY,
                    titre TEXT NOT NULL,
                    auteur TEXT NOT NULL,
                    annee INTEGER NOT NULL,
                    isbn TEXT NOT NULL,
                    categorie TEXT NOT NULL,
                    rayon TEXT NOT NULL,
                    etat TEXT NOT NULL DEFAULT 'BON',
                    mode_consultation TEXT NOT NULL DEFAULT 'EMPRUNTABLE',
                    editeur TEXT NOT NULL DEFAULT 'Éditions Universitaires',
                    est_emprunte INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS usagers (
                    matricule TEXT PRIMARY KEY,
                    nom_complet TEXT NOT NULL,
                    type_usager TEXT NOT NULL DEFAULT 'ETUDIANT',
                    filiere_ou_departement TEXT NOT NULL DEFAULT 'Licence Cyber Science',
                    email TEXT NOT NULL DEFAULT '',
                    telephone TEXT NOT NULL DEFAULT '',
                    est_suspendu INTEGER NOT NULL DEFAULT 0,
                    penalites_impayees_fcfa INTEGER NOT NULL DEFAULT 0,
                    date_inscription TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS emprunts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_livre TEXT NOT NULL,
                    matricule TEXT NOT NULL,
                    date_emprunt TEXT NOT NULL,
                    date_retour_prevue TEXT NOT NULL,
                    date_retour_effective TEXT,
                    prolongations INTEGER NOT NULL DEFAULT 0,
                    etat_depart TEXT NOT NULL DEFAULT 'BON',
                    etat_retour TEXT,
                    penalite_fcfa INTEGER NOT NULL DEFAULT 0,
                    commentaire TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (code_livre) REFERENCES livres(code)
                );

                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_livre TEXT NOT NULL,
                    matricule TEXT NOT NULL,
                    date_reservation TEXT NOT NULL,
                    statut TEXT NOT NULL DEFAULT 'EN_ATTENTE',
                    FOREIGN KEY (code_livre) REFERENCES livres(code)
                );

                CREATE TABLE IF NOT EXISTS sanctions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matricule TEXT NOT NULL,
                    emprunt_id INTEGER,
                    motif TEXT NOT NULL,
                    montant_fcfa INTEGER NOT NULL,
                    date_sanction TEXT NOT NULL,
                    est_reglee INTEGER NOT NULL DEFAULT 0
                );
                """
            )

    def peupler_donnees_initiales(self) -> None:
        """
        Amorce la base avec 65 ouvrages réalistes et 15 usagers IIT si le catalogue est vide.
        Ajoute également un emprunt en retard sur L015 pour que l'option '4. Retards' soit
        immédiatement démonstrative tout en laissant L002 et L004 disponibles pour le scénario de la Slide 29.
        """
        cur = self._conn.execute("SELECT COUNT(*) AS nb FROM livres;")
        if cur.fetchone()["nb"] > 0:
            return

        with self._conn:
            self._conn.executemany(
                """
                INSERT INTO livres (code, titre, auteur, annee, isbn, categorie, rayon, etat, mode_consultation, editeur, est_emprunte)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
                """,
                CATALOGUE_INITIAL_65_LIVRES,
            )

            aujourdhui = date.today().isoformat()
            self._conn.executemany(
                """
                INSERT INTO usagers (matricule, nom_complet, type_usager, filiere_ou_departement, email, telephone, est_suspendu, penalites_impayees_fcfa, date_inscription)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?);
                """,
                [(*u, aujourdhui) for u in USAGERS_INITIAUX_IIT],
            )

            # Emprunt historique déjà en retard sur L015 ("Sous l'orage") par E2026-009
            date_emp_retard = (date.today() - timedelta(days=22)).isoformat()
            date_ech_retard = (date.today() - timedelta(days=8)).isoformat()
            self._conn.execute(
                """
                INSERT INTO emprunts (code_livre, matricule, date_emprunt, date_retour_prevue, etat_depart, commentaire)
                VALUES ('L015', 'E2026-009', ?, ?, 'BON', 'Emprunt initial en retard pour démonstration');
                """,
                (date_emp_retard, date_ech_retard),
            )
            self._conn.execute("UPDATE livres SET est_emprunte = 1 WHERE code = 'L015';")

    # =========================================================================
    # OPÉRATIONS SUR LES LIVRES
    # =========================================================================

    def _row_to_livre(self, row: sqlite3.Row) -> Livre:
        return Livre(
            code=row["code"],
            titre=row["titre"],
            auteur=row["auteur"],
            annee=int(row["annee"]),
            isbn=row["isbn"],
            categorie=row["categorie"],
            rayon=row["rayon"],
            etat=row["etat"],
            mode_consultation=row["mode_consultation"],
            editeur=row["editeur"],
            est_emprunte=bool(row["est_emprunte"]),
        )

    def obtenir_livre(self, code: str) -> Optional[Livre]:
        """Récupère un livre par son code (insensible à la casse)."""
        cur = self._conn.execute(
            "SELECT * FROM livres WHERE UPPER(code) = UPPER(?);",
            (code.strip(),),
        )
        row = cur.fetchone()
        return self._row_to_livre(row) if row else None

    def lister_tous_les_livres(self) -> List[Livre]:
        """Retourne l'intégralité du catalogue triée par code."""
        cur = self._conn.execute("SELECT * FROM livres ORDER BY code ASC;")
        return [self._row_to_livre(r) for r in cur.fetchall()]

    def rechercher_livres(self, mot_cle: str) -> List[Livre]:
        """
        Recherche des livres par mot-clé (titre, auteur, code, catégorie, ISBN ou rayon).
        Trié par année décroissante puis code (comme sur la Slide 29 où L004 (2000) précède L002 (1968)).
        """
        terme = f"%{mot_cle.strip()}%"
        cur = self._conn.execute(
            """
            SELECT * FROM livres
            WHERE titre LIKE ?
               OR auteur LIKE ?
               OR code LIKE ?
               OR categorie LIKE ?
               OR isbn LIKE ?
               OR rayon LIKE ?
            ORDER BY annee DESC, code DESC;
            """,
            (terme, terme, terme, terme, terme, terme),
        )
        return [self._row_to_livre(r) for r in cur.fetchall()]

    def lister_livres_par_categorie(self, categorie: str) -> List[Livre]:
        """Liste les ouvrages appartenant à une catégorie donnée."""
        cur = self._conn.execute(
            "SELECT * FROM livres WHERE categorie LIKE ? ORDER BY code ASC;",
            (f"%{categorie.strip()}%",),
        )
        return [self._row_to_livre(r) for r in cur.fetchall()]

    def ajouter_livre(self, livre: Livre) -> None:
        """Ajoute un nouvel ouvrage au catalogue de la bibliothèque."""
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO livres (code, titre, auteur, annee, isbn, categorie, rayon, etat, mode_consultation, editeur, est_emprunte)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    livre.code.upper().strip(),
                    livre.titre.strip(),
                    livre.auteur.strip(),
                    livre.annee,
                    livre.isbn.strip(),
                    livre.categorie,
                    livre.rayon.strip(),
                    livre.etat,
                    livre.mode_consultation,
                    livre.editeur.strip(),
                    1 if livre.est_emprunte else 0,
                ),
            )

    def mettre_a_jour_etat_livre(self, code_livre: str, nouvel_etat: str, est_emprunte: Optional[bool] = None) -> None:
        """Met à jour l'état physique et/ou le statut d'emprunt d'un livre."""
        with self._conn:
            if est_emprunte is None:
                self._conn.execute(
                    "UPDATE livres SET etat = ? WHERE UPPER(code) = UPPER(?);",
                    (nouvel_etat, code_livre),
                )
            else:
                self._conn.execute(
                    "UPDATE livres SET etat = ?, est_emprunte = ? WHERE UPPER(code) = UPPER(?);",
                    (nouvel_etat, 1 if est_emprunte else 0, code_livre),
                )

    # =========================================================================
    # OPÉRATIONS SUR LES USAGERS
    # =========================================================================

    def _row_to_usager(self, row: sqlite3.Row) -> Usager:
        return Usager(
            matricule=row["matricule"],
            nom_complet=row["nom_complet"],
            type_usager=row["type_usager"],
            filiere_ou_departement=row["filiere_ou_departement"],
            email=row["email"],
            telephone=row["telephone"],
            est_suspendu=bool(row["est_suspendu"]),
            penalites_impayees_fcfa=int(row["penalites_impayees_fcfa"]),
            date_inscription=row["date_inscription"],
        )

    def obtenir_usager(self, matricule: str) -> Optional[Usager]:
        """Récupère un usager par son matricule."""
        cur = self._conn.execute(
            "SELECT * FROM usagers WHERE UPPER(matricule) = UPPER(?);",
            (matricule.strip(),),
        )
        row = cur.fetchone()
        return self._row_to_usager(row) if row else None

    def lister_usagers(self) -> List[Usager]:
        """Liste tous les usagers inscrits à la bibliothèque."""
        cur = self._conn.execute("SELECT * FROM usagers ORDER BY matricule ASC;")
        return [self._row_to_usager(r) for r in cur.fetchall()]

    def ajouter_usager(self, usager: Usager) -> None:
        """Inscrit un nouvel étudiant ou enseignant dans la base."""
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO usagers (matricule, nom_complet, type_usager, filiere_ou_departement, email, telephone, est_suspendu, penalites_impayees_fcfa, date_inscription)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    usager.matricule.upper().strip(),
                    usager.nom_complet.strip(),
                    usager.type_usager,
                    usager.filiere_ou_departement.strip(),
                    usager.email.strip(),
                    usager.telephone.strip(),
                    1 if usager.est_suspendu else 0,
                    usager.penalites_impayees_fcfa,
                    usager.date_inscription,
                ),
            )

    def ajouter_penalite_usager(self, matricule: str, montant_fcfa: int, emprunt_id: Optional[int], motif: str) -> None:
        """Enregistre une sanction financière sur le dossier d'un usager."""
        if montant_fcfa <= 0:
            return
        with self._conn:
            self._conn.execute(
                """
                UPDATE usagers
                SET penalites_impayees_fcfa = penalites_impayees_fcfa + ?
                WHERE UPPER(matricule) = UPPER(?);
                """,
                (montant_fcfa, matricule),
            )
            self._conn.execute(
                """
                INSERT INTO sanctions (matricule, emprunt_id, motif, montant_fcfa, date_sanction, est_reglee)
                VALUES (?, ?, ?, ?, ?, 0);
                """,
                (matricule.upper(), emprunt_id, motif, montant_fcfa, date.today().isoformat()),
            )

    def regler_penalites_usager(self, matricule: str) -> int:
        """Solde les pénalités impayées d'un usager et retourne le montant encaissé."""
        usager = self.obtenir_usager(matricule)
        if not usager or usager.penalites_impayees_fcfa == 0:
            return 0
        montant = usager.penalites_impayees_fcfa
        with self._conn:
            self._conn.execute(
                "UPDATE usagers SET penalites_impayees_fcfa = 0, est_suspendu = 0 WHERE UPPER(matricule) = UPPER(?);",
                (matricule,),
            )
            self._conn.execute(
                "UPDATE sanctions SET est_reglee = 1 WHERE UPPER(matricule) = UPPER(?);",
                (matricule,),
            )
        return montant

    # =========================================================================
    # OPÉRATIONS SUR LES EMPRUNTS
    # =========================================================================

    def _row_to_emprunt(self, row: sqlite3.Row) -> Emprunt:
        return Emprunt(
            id=int(row["id"]),
            code_livre=row["code_livre"],
            matricule=row["matricule"],
            date_emprunt=row["date_emprunt"],
            date_retour_prevue=row["date_retour_prevue"],
            date_retour_effective=row["date_retour_effective"],
            prolongations=int(row["prolongations"]),
            etat_depart=row["etat_depart"],
            etat_retour=row["etat_retour"],
            penalite_fcfa=int(row["penalite_fcfa"]),
            commentaire=row["commentaire"],
        )

    def creer_emprunt(self, emprunt: Emprunt) -> Emprunt:
        """Enregistre un nouvel emprunt et marque le livre comme emprunté dans une transaction atomique."""
        with self._conn:
            cur = self._conn.execute(
                """
                INSERT INTO emprunts (code_livre, matricule, date_emprunt, date_retour_prevue, date_retour_effective, prolongations, etat_depart, etat_retour, penalite_fcfa, commentaire)
                VALUES (?, ?, ?, ?, NULL, ?, ?, NULL, 0, ?);
                """,
                (
                    emprunt.code_livre.upper(),
                    emprunt.matricule.upper(),
                    emprunt.date_emprunt,
                    emprunt.date_retour_prevue,
                    emprunt.prolongations,
                    emprunt.etat_depart,
                    emprunt.commentaire,
                ),
            )
            self._conn.execute(
                "UPDATE livres SET est_emprunte = 1 WHERE UPPER(code) = UPPER(?);",
                (emprunt.code_livre,),
            )
            emprunt.id = cur.lastrowid
        return emprunt

    def obtenir_emprunt_actif_par_livre(self, code_livre: str) -> Optional[Emprunt]:
        """Retourne l'emprunt en cours pour un code de livre donné."""
        cur = self._conn.execute(
            """
            SELECT * FROM emprunts
            WHERE UPPER(code_livre) = UPPER(?) AND date_retour_effective IS NULL
            ORDER BY id DESC LIMIT 1;
            """,
            (code_livre.strip(),),
        )
        row = cur.fetchone()
        return self._row_to_emprunt(row) if row else None

    def lister_emprunts_actifs_par_usager(self, matricule: str) -> List[Emprunt]:
        """Retourne la liste des emprunts actuellement en cours pour un matricule."""
        cur = self._conn.execute(
            """
            SELECT * FROM emprunts
            WHERE UPPER(matricule) = UPPER(?) AND date_retour_effective IS NULL
            ORDER BY date_retour_prevue ASC;
            """,
            (matricule.strip(),),
        )
        return [self._row_to_emprunt(r) for r in cur.fetchall()]

    def lister_tous_les_emprunts_actifs(self) -> List[Emprunt]:
        """Retourne tous les emprunts non encore restitués."""
        cur = self._conn.execute(
            "SELECT * FROM emprunts WHERE date_retour_effective IS NULL ORDER BY date_retour_prevue ASC;"
        )
        return [self._row_to_emprunt(r) for r in cur.fetchall()]

    def cloturer_emprunt(
        self,
        emprunt_id: int,
        code_livre: str,
        date_retour_effective: str,
        etat_retour: str,
        penalite_fcfa: int,
    ) -> None:
        """Enregistre le retour d'un livre et remet le livre à disposition (sauf s'il est perdu ou en réparation)."""
        est_indispo = etat_retour in (EtatExemplaire.PERDU.value, EtatExemplaire.EN_REPARATION.value)
        with self._conn:
            self._conn.execute(
                """
                UPDATE emprunts
                SET date_retour_effective = ?, etat_retour = ?, penalite_fcfa = ?
                WHERE id = ?;
                """,
                (date_retour_effective, etat_retour, penalite_fcfa, emprunt_id),
            )
            self._conn.execute(
                "UPDATE livres SET est_emprunte = ?, etat = ? WHERE UPPER(code) = UPPER(?);",
                (1 if est_indispo else 0, etat_retour, code_livre),
            )

    def prolonger_emprunt(self, emprunt_id: int, nouvelle_date_retour_prevue: str) -> None:
        """Met à jour la date de retour prévue et incrémente le compteur de prolongations."""
        with self._conn:
            self._conn.execute(
                """
                UPDATE emprunts
                SET date_retour_prevue = ?, prolongations = prolongations + 1
                WHERE id = ?;
                """,
                (nouvelle_date_retour_prevue, emprunt_id),
            )

    # =========================================================================
    # OPÉRATIONS SUR LES RÉSERVATIONS (FILE D'ATTENTE)
    # =========================================================================

    def _row_to_reservation(self, row: sqlite3.Row) -> Reservation:
        return Reservation(
            id=int(row["id"]),
            code_livre=row["code_livre"],
            matricule=row["matricule"],
            date_reservation=row["date_reservation"],
            statut=row["statut"],
        )

    def creer_reservation(self, code_livre: str, matricule: str) -> Reservation:
        """Ajoute un usager dans la file d'attente de réservation d'un livre emprunté."""
        aujourd_hui = date.today().isoformat()
        with self._conn:
            cur = self._conn.execute(
                """
                INSERT INTO reservations (code_livre, matricule, date_reservation, statut)
                VALUES (?, ?, ?, ?);
                """,
                (code_livre.upper(), matricule.upper(), aujourd_hui, StatutReservation.EN_ATTENTE.value),
            )
            return Reservation(
                id=cur.lastrowid,
                code_livre=code_livre.upper(),
                matricule=matricule.upper(),
                date_reservation=aujourd_hui,
                statut=StatutReservation.EN_ATTENTE.value,
            )

    def lister_reservations_en_attente(self, code_livre: str) -> List[Reservation]:
        """Retourne la file d'attente FIFO des réservations actives pour un livre."""
        cur = self._conn.execute(
            """
            SELECT * FROM reservations
            WHERE UPPER(code_livre) = UPPER(?) AND statut = 'EN_ATTENTE'
            ORDER BY id ASC;
            """,
            (code_livre.strip(),),
        )
        return [self._row_to_reservation(r) for r in cur.fetchall()]

    def honorer_reservation(self, reservation_id: int) -> None:
        """Marque une réservation comme honorée lorsque le réservataire emprunte le livre."""
        with self._conn:
            self._conn.execute(
                "UPDATE reservations SET statut = 'HONOREE' WHERE id = ?;",
                (reservation_id,),
            )

    # =========================================================================
    # STATISTIQUES & TABLEAU DE BORD BIBLIOTHÉCAIRE
    # =========================================================================

    def obtenir_statistiques_globales(self) -> Dict[str, int]:
        """Calcule les indicateurs clés de la bibliothèque de l'IIT."""
        total_livres = self._conn.execute("SELECT COUNT(*) FROM livres;").fetchone()[0]
        livres_empruntes = self._conn.execute("SELECT COUNT(*) FROM livres WHERE est_emprunte = 1;").fetchone()[0]
        livres_sur_place = self._conn.execute("SELECT COUNT(*) FROM livres WHERE mode_consultation = 'SUR_PLACE';").fetchone()[0]
        total_usagers = self._conn.execute("SELECT COUNT(*) FROM usagers;").fetchone()[0]
        total_emprunts_historique = self._conn.execute("SELECT COUNT(*) FROM emprunts;").fetchone()[0]
        reservations_actives = self._conn.execute("SELECT COUNT(*) FROM reservations WHERE statut = 'EN_ATTENTE';").fetchone()[0]
        penalites_totales = self._conn.execute("SELECT COALESCE(SUM(penalites_impayees_fcfa), 0) FROM usagers;").fetchone()[0]

        return {
            "total_livres": total_livres,
            "livres_disponibles": total_livres - livres_empruntes,
            "livres_empruntes": livres_empruntes,
            "livres_sur_place": livres_sur_place,
            "total_usagers": total_usagers,
            "total_emprunts_historique": total_emprunts_historique,
            "reservations_actives": reservations_actives,
            "penalites_impayees_fcfa": penalites_totales,
        }

