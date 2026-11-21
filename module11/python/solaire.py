"""Atelier 4. Valoriser détenir, acheter via PPA et louer un service solaire."""
from modele import van, tableau, graphique, exporter

VOLUME_UTILE = .80       # Part de 0 à 1 du volume contracté, utilisée par l’usine.
INDEXATION_PPA = 0       # Taux annuel d’indexation après la première année.
TAUX, IMPOT, HORIZON = .10, .25, 10
if not 0 <= VOLUME_UTILE <= 1 or INDEXATION_PPA <= -1 or TAUX <= -1:
    raise ValueError("Vérifiez la part utile et les taux du modèle.")

def flux_ppa(volume):
    # Dépense réseau évitée proportionnelle au volume utile. Paiement PPA fixe
    # en quantité et indexé en prix. L’avantage fiscal peut être utilisé.
    return [-.5] + [(2.4 * volume - .10 - 1.35 * (1 + INDEXATION_PPA)**(t-1))
                     * (1 - IMPOT) for t in range(1, HORIZON + 1)]

flux_detention = [-10] + [(2.4 - .4) * (1 - IMPOT) + 1 * IMPOT] * HORIZON
flux_location = [0] + [(2.4 - 1.65 - .4) * (1 - IMPOT)] * HORIZON
flux = [flux_detention, flux_ppa(VOLUME_UTILE), flux_location]
noms = ["Détention", "PPA", "Location"]
vans = [van(TAUX, x) for x in flux]
# La pente de la VAN du PPA est la VAN supplémentaire entre volume 0 et 1.
ppa_zero = van(TAUX, flux_ppa(0))
pente = van(TAUX, flux_ppa(1)) - ppa_zero
seuil = (vans[0] - ppa_zero) / pente
grille = [i / 10 for i in range(11)]
gagnant = noms[max(range(3), key=vans.__getitem__)]
RESULTATS = {
    "tableaux": [tableau("Flux incrémentaux et VAN à t0",
        ["Modalité", "F₀", "F₁", "F₁₀", "VAN"],
        [[nom, fr[0], fr[1], fr[-1], v] for nom, fr, v in zip(noms, flux, vans)]),
        tableau("Points de comparaison à taux et prix donnés",
        ["PPA à volume intégral", "Seuil PPA = détention (%)"],
        [[van(TAUX, flux_ppa(1)), 100 * seuil]])],
    "graphiques": [graphique("VAN selon la part du PPA réellement utilisée", "M MAD",
        [f"{100*u:.0f} %" for u in grille],
        [("PPA", [van(TAUX, flux_ppa(u)) for u in grille]),
         ("Détention", [vans[0]]*len(grille)), ("Location", [vans[2]]*len(grille))])],
    "commentaires": [
        f"À {100*VOLUME_UTILE:.0f} % d’utilisation, la meilleure VAN est celle de l’option {gagnant.lower()}. La comparaison suppose les volumes de la détention et de la location inchangés ; l’électricité réseau remplace la part non utile du PPA.",
        f"Le PPA égale la détention à {100*seuil:.2f} % de volume utile. Un seuil hors de 0–100 % signale que le classement de ces deux formes n’est jamais inversé dans l’intervalle étudié. La location reste à comparer séparément.",
        "Le cash-flow est incrémental par rapport au réseau. La détention inclut le gain fiscal d’amortissement ; le PPA fait apparaître le paiement contractuel à chaque période. Les intérêts restent hors de ces flux lorsque le taux d’actualisation intègre déjà le financement."
    ],
}
if __name__ == "__main__":
    exporter(RESULTATS)
