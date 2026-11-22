"""Atelier 2. Refaire le budget annuel et localiser le besoin hebdomadaire."""
from modele import prevision, tableau, graphique, exporter

RETARD_MISE_EN_SERVICE_ANS = 1
REPORT_TIRAGE = 1  # Nombre de semaines de retard du tirage prévu en semaine 4.
RESERVE = 3
if not isinstance(REPORT_TIRAGE, int) or not 0 <= REPORT_TIRAGE <= 2:
    raise ValueError("Choisissez un report de 0, 1 ou 2 semaines dans cet extrait.")

def calendrier(report):
    encaissements = [1.4, 2.2, 1.7, 2, 2.3, 1.8]
    exploitation = [1.65, 1.8, 1.6, 1.55, 1.7, 1.65]
    capex = [0, 3, 0, 5, 0, 0]
    service = [0, 0, .6, 0, 0, 0]
    tirages = [0, 0, 0, 0, 0, 4]
    tirages[3 + report] += 10
    cash = 4
    sorties = []
    for i in range(6):
        cash += encaissements[i] - exploitation[i] - capex[i] - service[i] + tirages[i]
        sorties.append([f"S{i+1}", encaissements[i], exploitation[i],
                        capex[i], service[i], tirages[i], cash])
    return sorties

reference, retard = prevision(), prevision(retard=RETARD_MISE_EN_SERVICE_ANS)
central, decale = calendrier(0), calendrier(REPORT_TIRAGE)
point_bas = min(decale, key=lambda ligne: ligne[-1])
ligne_credit = max(0, RESERVE - point_bas[-1])
RESULTATS = {
    "tableaux": [
        tableau("Pont financier annuel", ["Année", "EBITDA central", "CFO central",
                "Dette fin", "Cash central", "Cash avec retard des gains", "DSCR central (×)"],
            [[f"A{a['annee']}", a["ebitda"], a["cfo"], a["dette"], a["cash"],
              b["cash"], a["dscr"]] for a, b in zip(reference, retard)]),
        tableau("Calendrier hebdomadaire simulé",
                ["Semaine", "Encaissements", "Exploitation", "CAPEX", "Dette payée",
                 "Tirage", "Cash final"], decale)],
    "graphiques": [graphique("Calendrier de trésorerie avant ligne de secours", "M MAD",
        [x[0] for x in central], [("Tirage prévu", [x[-1] for x in central]),
        ("Tirage simulé", [x[-1] for x in decale]), ("Coussin", [RESERVE]*6)])],
    "commentaires": [
        f"Le scénario annuel central clôture A1 à {reference[0]['cash']:.2f} M MAD et A2 à {reference[1]['cash']:.2f}. Le retard E+S ramène le cash d’A2 à {retard[1]['cash']:.2f} en décalant les économies et l’amortissement, sans modifier le CAPEX.",
        f"Dans l’extrait hebdomadaire, le point bas est {point_bas[-1]:.2f} M MAD en {point_bas[0]}. Le montant minimal pour rester à {RESERVE:g} en fin de semaine est {ligne_credit:.2f} M MAD, hors intérêts et frais.",
        f"La trésorerie de fin de S6 est {decale[-1][-1]:.2f} M MAD. L’extrait représente six semaines, avec des encaissements et échéances propres à cette période. Pour dimensionner une ligne réelle, vérifier l’ordre des paiements et tirages à l’intérieur d’une semaine."
    ],
}
if __name__ == "__main__":
    exporter(RESULTATS, "plan")
