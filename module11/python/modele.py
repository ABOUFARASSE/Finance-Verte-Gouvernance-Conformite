"""Conventions communes du cas Maghreb Agro-Industries. Montants en M MAD."""
import json
from math import isfinite


def van(taux, flux):
    """Flux à t=0 puis à chaque fin de période."""
    if taux <= -1:
        raise ValueError("Le taux doit être supérieur à −100 %.")
    return sum(montant / (1 + taux)**annee for annee, montant in enumerate(flux))


def cout_effectif(flux_emprunteur):
    """Un encaissement initial positif, puis uniquement des remboursements."""
    if flux_emprunteur[0] <= 0 or any(x >= 0 for x in flux_emprunteur[1:]):
        raise ValueError("Utiliser un encaissement initial et des échéances négatives.")
    bas, haut = -0.99, 1.0
    while van(haut, flux_emprunteur) < 0:
        haut *= 2
    for _ in range(80):
        milieu = (bas + haut) / 2
        if van(milieu, flux_emprunteur) < 0:
            bas = milieu
        else:
            haut = milieu
    return (bas + haut) / 2


def prevision(demande=0, energie=0, pret=14, apport=0, ppa=False, retard=0):
    """Plan A1–A5. Chocs proportionnels constants versus trajectoire de base.

    Intérêts sur la dette d'ouverture plus le tirage de début A1.
    Les coûts énergie sont déjà dans les charges variables de référence.
    Le PPA garde le même volume substitué à plein régime dans ce stress.
    Après mise en service il gagne 0,95, contre 2 en détention. Les frais
    d'entrée de 0,5 sont décaissés en A1, hors CFADS, et non déductibles.
    """
    if not (0 <= demande <= 1 and energie >= 0 and pret >= 0 and apport >= 0
            and isinstance(retard, int) and 0 <= retard <= 4):
        raise ValueError("Vérifiez le domaine des chocs, du financement et du retard.")
    cash, bfr, dette_historique, dette_nouvelle = 4, 20, 22, 0
    lignes = []
    for annee in range(1, 6):
        actif = annee >= 2 + retard
        ca = 100 * 1.05**annee * (1 - demande)
        economie = (1.8 + (0.95 if ppa else 2)) * actif + 0.7 * (annee >= 3)
        surcout = energie * (8 * 1.02**annee - 3.8 * actif)
        ebitda = 0.4 * ca - 24 * 1.02**annee + economie - surcout
        amort = 4 + (0.6 if ppa else 1.6) * actif + 0.4 * (annee >= 3)
        tirage = pret if annee == 1 else 0
        interets = 0.06 * (dette_historique + dette_nouvelle + tirage)
        impot = 0.25 * max(0, ebitda - amort - interets)
        variation_bfr = 0.2 * ca - bfr
        cfo = ebitda - interets - impot - variation_bfr
        # Entretien 4, transition E et S en A1, W en A2.
        capex = 4 + (6 if ppa else 16) * (annee == 1) + 4 * (annee == 2)
        frais = 0.5 if ppa and annee == 1 else 0
        principal = 2 + pret / 5
        service = interets + principal
        fond_propre = apport if annee == 1 else 0
        cfads = ebitda - impot - variation_bfr - 4
        cloture = cash + cfo - capex - frais + tirage + fond_propre - principal
        controle = cloture - (cash + cfads - service - (capex - 4)
                              - frais + tirage + fond_propre)
        assert abs(controle) < 1e-9, "Le pont de trésorerie doit se réconcilier."
        dette_historique -= 2
        dette_nouvelle += tirage - pret / 5
        lignes.append(dict(annee=annee, ca=ca, ebitda=ebitda,
                            delta_bfr=variation_bfr, cfo=cfo, capex=capex,
                            tirage=tirage, apport=fond_propre, service=service,
                            cfads=cfads, cash=cloture, dscr=cfads / service,
                            dette=dette_historique + dette_nouvelle))
        cash, bfr = cloture, 0.2 * ca
    return lignes


def tableau(titre, colonnes, lignes):
    return dict(titre=titre, colonnes=colonnes, lignes=lignes)


def graphique(titre, unite, abscisses, series, type_="ligne"):
    """Une série est un couple (libellé, valeurs)."""
    if not all(len(valeurs) == len(abscisses) and all(map(isfinite, valeurs))
               for _, valeurs in series):
        raise ValueError("Vérifiez les valeurs numériques du graphique.")
    return dict(titre=titre, unite=unite, categories=abscisses,
                series=[dict(nom=nom, valeurs=valeurs) for nom, valeurs in series],
                type=type_)


def exporter(resultats):
    """Sortie JSON pour une exécution locale ou externe à la page."""
    print(json.dumps(resultats, ensure_ascii=False, indent=2, allow_nan=False))
