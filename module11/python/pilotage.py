"""Atelier 6. Corriger la référence énergie et actualiser la décision de comité."""
from modele import prevision, tableau, graphique, exporter

VOLUME_TONNES, MWH_MESURES, TARIF_MAD_KWH = 12_000, 2080, .80
PERTE_EBITDA, HAUSSE_BFR, DEPENSE_PONCTUELLE = .28, .35, .45
MWH_RESEAU, MWH_ATTRIBUTS = 5000, 2700
COUSSIN, DSCR_MIN = 3, 1.20
if not 0 <= MWH_ATTRIBUTS <= MWH_RESEAU or MWH_MESURES < 0 or VOLUME_TONNES <= 0:
    raise ValueError("Vérifiez les volumes, le compteur et les attributs contractuels.")

reference_historique = 600 + .15 * 10_000
reference_ajustee = 600 + .15 * VOLUME_TONNES
economie = reference_ajustee - MWH_MESURES
gain_variable_mad = economie * 1000 * TARIF_MAD_KWH
reseau = MWH_RESEAU * .60
marche = (MWH_RESEAU - MWH_ATTRIBUTS) * .65

# A2 du PPA avec fonds propres, sous le scénario sévère étudié à la séance 3.
a2 = prevision(.20, .50, ppa=True, pret=0, apport=8)[1]
# À A2 dans cet exemple, le résultat imposable initial vaut 4,9988 M MAD.
# Le gain fiscal d’une perte d’EBITDA est plafonné à l’impôt initial.
impot_initial = .25 * (a2["ebitda"] - 4.6 - 1.2)
gain_fiscal = min(impot_initial, .25 * PERTE_EBITDA)
variation_cfo = -PERTE_EBITDA + gain_fiscal - HAUSSE_BFR
cash_maj = a2["cash"] + variation_cfo
cash_final = cash_maj - DEPENSE_PONCTUELLE
dscr = (a2["cfads"] + variation_cfo) / a2["service"]
avis = "Visa possible sous conditions" if cash_final >= COUSSIN and dscr >= DSCR_MIN else "Réviser le plan avant engagement"
besoin = max(0, COUSSIN - cash_final)

RESULTATS = {
    "tableaux": [
        tableau("Mesure de l’énergie et inventaire indirect", ["Indicateur", "Mesure", "Unité"],
            [["Référence historique", reference_historique, "MWh"],
             ["Référence ajustée", reference_ajustee, "MWh"],
             ["Électricité mesurée", MWH_MESURES, "MWh"],
             ["Économie corrigée", economie, "MWh"],
             ["Facture variable évitée", gain_variable_mad, "MAD"],
             ["Scope 2 méthode réseau", reseau, "tCO₂e"],
             ["Scope 2 méthode marché", marche, "tCO₂e"]]),
        tableau("Révision du plan A2", ["Étape", "Cash A2 (M MAD)", "DSCR (×)"],
            [["Budget stressé", a2["cash"], a2["dscr"]],
             ["EBITDA et BFR révisés", cash_maj, dscr],
             ["Décaissement hors CFADS", cash_final, dscr]])],
    "graphiques": [
        graphique("Référence d’énergie et compteur", "MWh",
            ["Historique", "Référence ajustée", "Mesure"], [("Énergie",
            [reference_historique, reference_ajustee, MWH_MESURES])], "barres"),
        graphique("Trésorerie A2 après mise à jour", "M MAD",
            ["Budget", "Prévision révisée", "Après dépense"],
            [("Cash final", [a2["cash"], cash_maj, cash_final]), ("Coussin", [COUSSIN]*3)])],
    "commentaires": [
        f"La comparaison brute donne {reference_historique-MWH_MESURES:.0f} MWh d’économie, alors que l’ajustement pour la production donne {economie:.0f} MWh. Le tarif variable appliqué à l’économie corrigée aboutit à {gain_variable_mad:,.0f} MAD.",
        f"Les méthodes réseau et marché donnent {reseau:.0f} et {marche:.0f} tCO₂e. Le second chiffre suppose que les attributs couvrant {MWH_ATTRIBUTS:g} MWh satisfont les critères de qualité. Les deux chiffres décrivent le même périmètre d’inventaire et ne s’additionnent pas.",
        f"{avis}. La perte d’EBITDA réduit l’impôt de {gain_fiscal:.2f} M MAD, le BFR absorbe {HAUSSE_BFR:.2f} et le décaissement final affecte le cash hors CFADS par convention. Le cash final est de {cash_final:.3f} pour un DSCR de {dscr:.3f}× ; l’écart au coussin à financer est de {besoin:.3f} M MAD."
    ],
}
if __name__ == "__main__":
    exporter(RESULTATS, "pilotage")
