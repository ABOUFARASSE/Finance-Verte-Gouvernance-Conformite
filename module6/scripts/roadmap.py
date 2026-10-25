"""Feuille de route du module, générée depuis les objectifs des six séances."""
from html import escape

def render_roadmap(sessions):
    phases=[
        ('Comprendre et prévoir','Établir le diagnostic, puis traduire la transition en besoins et en flux.',(1,2)),
        ('Financer et arbitrer','Choisir les ressources et les engagements qui rendent la stratégie réalisable.',(3,4)),
        ('Sécuriser et piloter','Tester la résistance du plan, décider sous conditions et organiser le suivi.',(5,6)),
    ]
    verbs=['Diagnostiquer','Planifier','Financer','Arbitrer','Adapter','Piloter']
    outputs=['Diagnostic financier argumenté','Plan financier et trésorerie prévisionnelle','Recommandation de financement','Matrice d’arbitrage stratégique','Scénarios, seuils et actions','Note de décision et tableau de bord']
    text='''<section id="feuille-de-route" class="course-route" aria-labelledby="route-title">
<p class="smallcaps">Le parcours en un regard · 6 séances · 21 heures</p>
<h2 id="route-title">Feuille de route du cours</h2>
<p class="route-purpose"><b>Objectif final :</b> construire et défendre une stratégie de transition finançable, résistante aux chocs et pilotable dans le temps.</p>
<ol class="route-phases">'''
    for i,(title,desc,nums) in enumerate(phases,1):
        text+=f'<li class="route-phase"><div class="route-phase-head"><span class="route-phase-number">Étape {i}</span><div><h3>{escape(title)}</h3><p>{escape(desc)}</p></div></div><div class="route-pair">'
        for j,n in enumerate(nums):
            if j:text+='<span class="route-arrow" aria-hidden="true">→</span>'
            s=sessions[n-1]
            text+=f'<a class="route-session" href="seance{n}/" aria-label="Séance {n} : {escape(s["title"],quote=True)}"><div class="route-session-meta"><span class="route-number">S{n}</span><span class="route-verb">{verbs[n-1]}</span><span class="route-duration">3 h 30</span></div><h4>{escape(s["title"])}</h4><p class="route-objective-label">Objectifs de la séance</p><ul>'+''.join(f'<li>{escape(o)}</li>' for o in s['objectives'])+f'</ul><div class="route-output"><span>Résultat attendu</span><strong>{outputs[n-1]}</strong></div><span class="route-open">Ouvrir la séance <span aria-hidden="true">↗</span></span></a>'
        text+='</div></li>'
    text+='''</ol><div class="route-thread"><b>Fil rouge : Maghreb Agro-Industries</b><p>Le même dossier relie les six séances : comptes, investissements énergie/eau, financements, scénarios et décision finale. Chaque séance apporte une pièce supplémentaire à la recommandation.</p><a href="cas/">Consulter le dossier commun →</a></div>
<div class="route-feedback"><span aria-hidden="true">↻</span><p><b>Une démarche à réviser :</b> les résultats du pilotage conduisent à actualiser le diagnostic, le plan financier et les arbitrages lorsque les hypothèses changent.</p></div></section>'''
    return text
