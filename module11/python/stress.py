"""Atelier 5. Produire un stress à deux facteurs et comparer les réponses."""
from modele import prevision, tableau, graphique, exporter

CHOC_DEMANDE, CHOC_ENERGIE = .20, .50
APPORT, COUSSIN, DSCR_MIN = 8, 3, 1.20
# Le scénario de taux et les paramètres du prêt restent ceux du cas.
options = [
    ("Détention, prêt 14", dict()),
    ("PPA, prêt 5", dict(ppa=True, pret=5)),
    ("PPA, fonds propres", dict(ppa=True, pret=0, apport=APPORT)),
]
trajectoires = [(nom, prevision(CHOC_DEMANDE, CHOC_ENERGIE, **fin))
                for nom, fin in options]

def scenario(demande, energie):
    return prevision(demande, energie, ppa=True, pret=5)[0]

def seuil(critere, limite, demande=.10):
    """Premier choc énergie qui amène l’indicateur A1 à sa limite.
    À demande fixée, le prix réduit le flux, avec une pente qui change à impôt nul.
    """
    bas, haut = 0.0, 1.0
    if scenario(demande, bas)[critere] <= limite:
        return 0.0
    while scenario(demande, haut)[critere] > limite:
        haut *= 2
    for _ in range(60):
        milieu = (bas + haut) / 2
        if scenario(demande, milieu)[critere] > limite:
            bas = milieu
        else:
            haut = milieu
    return haut

limite_dscr, limite_cash = seuil("dscr", DSCR_MIN), seuil("cash", COUSSIN)
grille = [[100*d, 100*e, ligne["cash"], ligne["dscr"],
           "Oui" if ligne["cash"] >= COUSSIN and ligne["dscr"] >= DSCR_MIN else "Non"]
          for d in (0, .10, .20) for e in (0, .30, .50, .70)
          for ligne in [scenario(d, e)]]

def minimum(lignes, cle):
    return min(lignes, key=lambda ligne: ligne[cle])

synthese = []
for nom, lignes in trajectoires:
    cash, dscr = minimum(lignes, "cash"), minimum(lignes, "dscr")
    synthese.append([nom, cash["cash"], f"A{cash['annee']}", dscr["dscr"],
                     f"A{dscr['annee']}", "Oui" if cash["cash"] >= COUSSIN
                     and dscr["dscr"] >= DSCR_MIN else "Non"])

sans_apport = prevision(CHOC_DEMANDE, CHOC_ENERGIE, pret=0, ppa=True)
apport_min = max(0, COUSSIN - minimum(sans_apport, "cash")["cash"])
annees = [f"A{i}" for i in range(1, 6)]
RESULTATS = {
    "tableaux": [
        tableau("Grille A1 • PPA et prêt de 5", ["Baisse demande (%)", "Choc énergie (%)",
                "Cash", "DSCR (×)", "Deux seuils respectés"], grille),
        tableau("Bilan des financements sur A1–A5", ["Montage", "Cash min.", "Année",
                "DSCR min. (×)", "Année", "Deux seuils respectés"], synthese)],
    "graphiques": [
        graphique("Trajectoires de trésorerie", "M MAD", annees,
           [(nom, [x["cash"] for x in lignes]) for nom, lignes in trajectoires]
           + [("Coussin", [COUSSIN]*5)]),
        graphique("Trajectoires de couverture de la dette", "DSCR (×)", annees,
           [(nom, [x["dscr"] for x in lignes]) for nom, lignes in trajectoires]
           + [("Seuil", [DSCR_MIN]*5)])],
    "commentaires": [
        f"Pour une demande en baisse de 10 %, le PPA avec prêt de 5 atteint le seuil de DSCR à +{100*limite_dscr:.2f} % d’énergie et le coussin à +{100*limite_cash:.2f} %. Le premier seuil est celui de {'couverture' if limite_dscr <= limite_cash else 'trésorerie'}.",
        f"En l’absence de nouveau prêt, il faut au moins {apport_min:.2f} M MAD d’apport en A1 pour atteindre le coussin sur les cinq clôtures. Le DSCR minimal sans nouveau prêt vaut {minimum(sans_apport, 'dscr')['dscr']:.2f}× ; injecter davantage de fonds propres sans modifier le service de la dette ne change pas ce ratio.",
        "La baisse de demande réduit l’EBITDA mais libère du BFR dans ce modèle à ratio de 20 %. Le surcoût d’énergie frappe l’exposition résiduelle. Comparer séparément l’année de la contrainte de couverture et celle de la contrainte de cash ; les tests ne donnent pas une probabilité de défaut."
    ],
}
if __name__ == "__main__":
    exporter(RESULTATS, "stress")
