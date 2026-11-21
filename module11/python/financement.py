"""Atelier 3. Comparer coût effectif, échéances et coût du capital."""
from modele import van, cout_effectif, tableau, graphique, exporter

MONTANT = 14
COMMISSION_A = 0.02
TAUX_A, TAUX_B = 0.06, 0.07
PART_DETTE_MARCHE, COUT_FONDS_PROPRES, IMPOT = 0.40, 0.14, 0.25
if not 0 <= COMMISSION_A < 1:
    raise ValueError("La commission initiale doit être comprise entre 0 et 100 % (exclu).")

def echeancier(taux, differe):
    encours = MONTANT
    lignes = []
    for annee in range(1, 6):
        interets = encours * taux
        principal = 0 if annee <= differe else MONTANT / (5 - differe)
        encours -= principal
        lignes.append([interets, principal, interets + principal, encours])
    return lignes

a, b = echeancier(TAUX_A, 0), echeancier(TAUX_B, 1)
flux_a = [MONTANT * (1 - COMMISSION_A), *[-x[2] for x in a]]
flux_b = [MONTANT, *[-x[2] for x in b]]
cout_a, cout_b = cout_effectif(flux_a), cout_effectif(flux_b)
wacc = (1 - PART_DETTE_MARCHE) * COUT_FONDS_PROPRES + PART_DETTE_MARCHE * TAUX_A * (1 - IMPOT)
assert abs(van(cout_a, flux_a)) < 1e-8 and abs(van(cout_b, flux_b)) < 1e-8
RESULTATS = {
    "tableaux": [tableau("Dette nouvelle seulement • M MAD",
        ["Année", "Intérêts A", "Principal A", "Service A", "Dette A fin",
         "Intérêts B", "Principal B", "Service B", "Dette B fin"],
        [[f"A{i+1}", *x, *y] for i, (x, y) in enumerate(zip(a, b))]),
        tableau("Conditions économiques",
        ["Offre", "Décaissement net reçu", "Coût effectif (%)", "Pic de service"],
        [["A", flux_a[0], 100*cout_a, max(x[2] for x in a)],
         ["B", flux_b[0], 100*cout_b, max(x[2] for x in b)]])],
    "graphiques": [graphique("Service annuel de la dette nouvelle", "M MAD",
        [f"A{i}" for i in range(1,6)], [("A : amortissement immédiat", [x[2] for x in a]),
        ("B : différé de principal", [x[2] for x in b])], "barres")],
    "commentaires": [
        f"L’offre A verse {flux_a[0]:.2f} M MAD net de commission. Le taux actuariel qui égalise ce montant et la valeur des paiements atteint {100*cout_a:.2f} % contre {100*cout_b:.2f} % pour B. La méthode a remis chaque VAN d’emprunt à zéro.",
        f"B ramène le service d’A1 de {a[0][2]:.2f} à {b[0][2]:.2f}, puis le porte à {b[1][2]:.2f} en A2. Reprendre les flux disponibles et le service de la dette historique avant de calculer un DSCR d’entreprise.",
        f"Avec les pondérations de marché hypothétiques et la dette au taux marginal facial de {100*TAUX_A:g} %, le WACC illustratif vaut {100*wacc:.2f} %. Ce calcul suppose l’avantage fiscal utilisable et une structure cible stable. Il mesure le coût des ressources du projet, tandis que le TRI de l’offre mesure son coût contractuel dans cet exemple."
    ],
}
if __name__ == "__main__":
    exporter(RESULTATS)
