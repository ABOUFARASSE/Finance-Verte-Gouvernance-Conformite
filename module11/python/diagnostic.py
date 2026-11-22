"""Atelier 1. Calculer la création de valeur et la liquidité historique."""
from modele import tableau, graphique, exporter

# À modifier après avoir reproduit la situation N.
JOURS_CLIENTS_EN_PLUS = 15
COUT_DU_CAPITAL = 0.10
CA, CHARGES_VARIABLES, CHARGES_FIXES = 100, 60, 24
STOCKS, CLIENTS, FOURNISSEURS, BFR_INITIAL = 14, 18, 12, 18
IMMOBILISATIONS, AMORTISSEMENT, INTERETS, PRINCIPAL = 40, 4, 1.8, 2
CASH_INITIAL, CAPEX, DIVIDENDES, IMPOT = 3, 4, 2.65, 0.25

def diagnostic(jours):
    ebitda = CA - CHARGES_VARIABLES - CHARGES_FIXES
    ebit = ebitda - AMORTISSEMENT
    impot = (ebit - INTERETS) * IMPOT
    resultat_net = ebit - INTERETS - impot
    # Ventes à crédit : la base conventionnelle de l’exercice est de 360 jours.
    bfr = STOCKS + CLIENTS + CA * jours / 360 - FOURNISSEURS
    variation_bfr = bfr - BFR_INITIAL
    cfo = resultat_net + AMORTISSEMENT - variation_bfr
    cash = CASH_INITIAL + cfo - CAPEX - PRINCIPAL - DIVIDENDES
    capital = IMMOBILISATIONS + bfr
    nopat = ebit * (1 - IMPOT)
    cfads = ebitda - impot - variation_bfr - CAPEX
    return [ebitda, resultat_net, bfr, cfo, cash, 100 * nopat / capital,
            nopat - COUT_DU_CAPITAL * capital, cfads / (INTERETS + PRINCIPAL)]

base, variante = diagnostic(0), diagnostic(JOURS_CLIENTS_EN_PLUS)
RESULTATS = {
    "tableaux": [tableau("Diagnostic financier en N",
        ["Scénario", "EBITDA", "Résultat net", "BFR", "CFO", "Cash final",
         "ROIC (%)", "Profit économique", "DSCR (×)"],
        [["Référence", *base], [f"Clients +{JOURS_CLIENTS_EN_PLUS:g} j", *variante]])],
    "graphiques": [graphique("Effet du délai de paiement sur les flux", "M MAD",
        ["Résultat net", "CFO", "Cash final"],
        [("Référence", [base[1], base[3], base[4]]),
         ("Délai modifié", [variante[1], variante[3], variante[4]])], "barres")],
    "commentaires": [
        f"Le délai testé fait varier le BFR de {variante[2]-base[2]:+.2f} M MAD. Le résultat net reste à {base[1]:.2f}, mais le CFO passe de {base[3]:.2f} à {variante[3]:.2f}.",
        f"Le cash final atteint {variante[4]:.2f} M MAD. Un solde négatif indique un besoin de financement. Sous toutes les autres hypothèses de N, 14,4 jours supplémentaires suffisent à absorber les 4 M MAD de trésorerie.",
        f"Le ROIC passe de {base[5]:.2f} % à {variante[5]:.2f} % parce que davantage de capitaux sont immobilisés à NOPAT constant. Le coût du capital affecte le profit économique, pas le CFO."
    ],
}
if __name__ == "__main__":
    exporter(RESULTATS, "diagnostic")
