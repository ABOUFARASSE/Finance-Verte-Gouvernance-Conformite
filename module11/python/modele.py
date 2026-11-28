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


def prevision(demande=0, energie=0, pret=14, apport=0, ppa=False, retard=0, retard_solaire=0):
    """Plan A1–A5. Chocs proportionnels constants versus trajectoire de base.

    Intérêts sur la dette d'ouverture plus le tirage de début A1.
    Les coûts énergie sont déjà dans les charges variables de référence.
    Le PPA garde le même volume substitué à plein régime dans ce stress.
    Après mise en service il gagne 0,95, contre 2 en détention. Les frais
    d'entrée de 0,5 sont décaissés en A1, hors CFADS, et non déductibles.
    retard décale E et S ensemble. retard_solaire ajoute un décalage pour S seul.
    Le PPA commence à facturer à la livraison. Les frais d'entrée, le CAPEX
    programmé et les tirages restent aux dates de référence dans ce test.
    Sur la base énergétique, E évite 1,8 et S évite 2,0, qu'il soit détenu
    ou acheté via PPA. Ce sont les économies de réseau avant paiement du PPA.
    """
    if not (0 <= demande <= 1 and energie >= 0 and pret >= 0 and apport >= 0
            and isinstance(retard, int) and isinstance(retard_solaire, int)
            and retard >= 0 and retard_solaire >= 0 and retard + retard_solaire <= 4):
        raise ValueError("Vérifiez le domaine des chocs, du financement et du retard.")
    cash, bfr, dette_historique, dette_nouvelle = 4, 20, 22, 0
    lignes = []
    for annee in range(1, 6):
        efficacite_active = annee >= 2 + retard
        solaire_actif = annee >= 2 + retard + retard_solaire
        ca = 100 * 1.05**annee * (1 - demande)
        economie = (1.8 * efficacite_active + (0.95 if ppa else 2) * solaire_actif
                    + 0.7 * (annee >= 3))
        exposition_reseau = max(0, 8 * 1.02**annee - 1.8 * efficacite_active - 2 * solaire_actif)
        surcout = energie * exposition_reseau
        ebitda = 0.4 * ca - 24 * 1.02**annee + economie - surcout
        amort = (4 + 0.6 * efficacite_active + (not ppa) * solaire_actif
                 + 0.4 * (annee >= 3))
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


def exporter(resultats, nom=None):
    """Affiche la sortie JSON et, si un nom est fourni, enregistre le PDF local."""
    print(json.dumps(resultats, ensure_ascii=False, indent=2, allow_nan=False))
    if nom is not None:
        try:
            exporter_pdf(resultats, f"{nom}_resultats.pdf")
        except ModuleNotFoundError as erreur:
            if erreur.name != "matplotlib":
                raise
            import sys
            print("Pour générer le PDF, installez Matplotlib : python -m pip install matplotlib",
                  file=sys.stderr)


def exporter_pdf(resultats, destination):
    """Écrit uniquement les tableaux et figures. Destination : chemin ou flux binaire."""
    from numbers import Real
    from textwrap import fill

    import matplotlib as mpl
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.figure import Figure
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    # Toutes les dimensions du gabarit sont exprimées en points.
    largeur, hauteur, marge = 595, 842, 48
    utile = largeur - 2 * marge

    def nombre(valeur):
        if not isinstance(valeur, Real):
            return "" if valeur is None else str(valeur)
        if abs(valeur) < 0.0005:
            valeur = 0
        return f"{valeur:,.3f}".rstrip("0").rstrip(".").replace(",", " ").replace(".", ",").replace("-", "−")

    def texte(page, x, y, libelle, **style):
        page.text(x / largeur, 1 - y / hauteur, libelle, va="top", **style)

    def construire_tableau(t):
        en_tetes = t["colonnes"]
        lignes = t["lignes"]
        valeurs = [[nombre(v) for v in ligne] for ligne in lignes]
        numeriques = [all(isinstance(ligne[i], Real) for ligne in lignes)
                      for i in range(len(en_tetes))]
        poids = [min(22, max(8, len(en_tetes[i]),
                            *(len(ligne[i]) for ligne in valeurs)))
                 for i in range(len(en_tetes))]
        largeurs = [utile * p / sum(poids) for p in poids]
        cellules = [[fill(v, width=max(5, int((l - 10) / 5)))
                     for v, l in zip(ligne, largeurs)]
                    for ligne in [en_tetes, *valeurs]]
        hauteurs = [max(s.count("\n") + 1 for s in row) * 12 + 8
                    for row in cellules]
        return numeriques, largeurs, cellules, hauteurs

    def filet(page, y, epaisseur):
        page.add_artist(mpl.lines.Line2D(
            [marge / largeur, 1 - marge / largeur], [1 - y / hauteur] * 2,
            transform=page.transFigure, color="black", linewidth=epaisseur))

    def dessiner_tableau(page, y, donnees):
        numeriques, largeurs, cellules, hauteurs = donnees
        filet(page, y, .9)
        for index, (ligne, h) in enumerate(zip(cellules, hauteurs)):
            x = marge
            for cellule, l, numerique in zip(ligne, largeurs, numeriques):
                texte(page, x + l - 5 if numerique else x + 5, y + 5, cellule,
                      ha="right" if numerique else "left", fontsize=9,
                      multialignment="right" if numerique else "left",
                      weight="bold" if index == 0 else "normal")
                x += l
            y += h
            if index == 0:
                filet(page, y, .5)
        filet(page, y, .9)

    def dessiner_figure(page, y, bloc):
        axe = page.add_axes([(marge + 48) / largeur, 1 - (y + 163) / hauteur,
                             (utile - 64) / largeur, 163 / hauteur])
        categories = bloc["categories"]
        abscisses = list(range(len(categories)))
        series = bloc["series"]
        styles = [("-", "o"), ("--", "s"), ("-.", "^"), (":", "D")]
        hachures = ["", "///", "...", "\\\\"]
        for j, serie in enumerate(series):
            valeurs, nom = serie["valeurs"], serie["nom"]
            if bloc["type"] == "barres":
                pas = .72 / len(series)
                axe.bar([x + (j - (len(series) - 1) / 2) * pas for x in abscisses],
                        valeurs, width=pas * .92, label=nom, color=".24" if j == 0 else "white",
                        edgecolor="black", linewidth=.7, hatch=hachures[j % len(hachures)])
            else:
                trait, marqueur = styles[j % len(styles)]
                axe.plot(abscisses, valeurs, label=nom, color="black", linestyle=trait,
                         marker=marqueur, markersize=3.5, markerfacecolor="white", linewidth=1.15)
        axe.set_xticks(abscisses, categories)
        axe.set_ylabel(bloc["unite"])
        axe.tick_params(length=3, width=.6, labelsize=9)
        axe.spines[["top", "right"]].set_visible(False)
        axe.yaxis.set_major_locator(MaxNLocator(nbins=5))
        axe.yaxis.set_major_formatter(FuncFormatter(lambda v, _: nombre(v)))
        axe.set_axisbelow(True)
        axe.grid(axis="y", color=".86", linewidth=.5)
        if axe.get_ylim()[0] < 0 < axe.get_ylim()[1]:
            axe.axhline(0, color=".38", linewidth=.65)
        axe.legend(loc="upper center", bbox_to_anchor=(.5, -.19), frameon=False,
                   ncol=min(2, len(series)), fontsize=9)

    with mpl.rc_context({"font.family": "DejaVu Serif", "pdf.fonttype": 42,
                         "axes.linewidth": .65, "axes.labelsize": 10}):
        with PdfPages(destination, metadata={"Title": "Résultats de l’atelier Python"}) as pdf:
            page = Figure(figsize=(largeur / 72, hauteur / 72), facecolor="white")
            y = marge
            for cle, nom in [("tableaux", "Tableau"), ("graphiques", "Figure")]:
                for index, bloc in enumerate(resultats.get(cle, []), 1):
                    titre = fill(f"{nom} {index}. {bloc['titre']}", width=83)
                    espace_titre = 16 * (titre.count("\n") + 1) + 5
                    donnees = construire_tableau(bloc) if cle == "tableaux" else None
                    h = sum(donnees[3]) if donnees else 232
                    if y + espace_titre + h > hauteur - marge and y > marge:
                        pdf.savefig(page)
                        page = Figure(figsize=(largeur / 72, hauteur / 72), facecolor="white")
                        y = marge
                    texte(page, largeur / 2, y, titre, ha="center", fontsize=11, weight="bold")
                    y += espace_titre
                    if donnees:
                        dessiner_tableau(page, y, donnees)
                    else:
                        dessiner_figure(page, y + 5, bloc)
                    y += h + 26
            if y != marge:
                pdf.savefig(page)
