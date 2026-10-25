from pathlib import Path
import sys,re,json,html,shutil,subprocess
from lxml import html as LH
from course import SESSIONS
from references import REFS
from model import results
from roadmap import render_roadmap
ROOT=Path(__file__).resolve().parents[1]
DATA=results()
def escape(t):return html.escape(t,quote=True)
def citations(body,prefix=''):
 return re.sub(r'\[([A-Z0-9]+)\]',lambda m:f'<a class="cite" href="#ref-{m[1]}" title="{escape(REFS[m[1]][0])}">[{m[1]}]</a>' if m[1] in REFS else m[0],body)
def bibliography(keys):
 return '<ol class="references">'+''.join(f'<li id="ref-{k}"><b>[{k}] {escape(REFS[k][0])}.</b> {escape(REFS[k][1])} <a href="{escape(REFS[k][2])}">Consulter la source</a>.</li>' for k in keys)+'</ol>'
def nav(prefix,n=0):
 return '<nav class="topnav" aria-label="Navigation principale"><a href="'+prefix+'index.html">Module 6 · Accueil</a>'+''.join(f'<a class="{"active" if n==i else ""}" href="{prefix}seance{i}/" {"aria-current=page" if n==i else ""}>S{i}</a>' for i in range(1,7))+f'<a href="{prefix}cas/">Cas fil rouge</a><a href="{prefix}bibliographie/">Références</a><a class="download" href="{prefix}downloads/cours-complet.pdf">Cours complet PDF</a></nav>'
def page(title,body,prefix='',n=0,question='',side=''):
 return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{escape(title)} — Cours de Badr Aboufarasse, Master Finance verte."><title>{escape(title)} · Module 6</title><link rel="stylesheet" href="{prefix}assets/style.css"><script defer src="{prefix}assets/course.js"></script></head><body><a class="skip" href="#contenu">Aller au contenu</a>{nav(prefix,n)}<header><p class="eyebrow">Master Finance verte · Module 6 · Badr ABOUFARASSE, PhD</p><h1>{escape(title)}</h1><p>{escape(question)}</p><div class="coursemeta"><span class="tag">6 séances · 21 heures</span><span class="tag">Théorie et applications corrigées</span><span class="tag">Maghreb Agro-Industries</span></div></header><div class="shell">{side}<main id="contenu">{body}</main></div><footer>Badr ABOUFARASSE, PhD · Management financier et décision stratégique · 25 octobre 2026<br>Données du cas fictives. Références citées au niveau des développements.</footer></body></html>'''
def inputfield(id,label,value,min=0,max=100,step='.1'):
 return f'<label for="{id}">{label}<input id="{id}" type="number" value="{value}" min="{min}" max="{max}" step="{step}" required></label>'
def tool(n):
 if n in (2,5):
  fields=inputfield('shock','Baisse du CA (%)',10 if n==5 else 0,0,50)+inputfield('energy','Hausse du prix énergétique résiduel (%)',30 if n==5 else 0,0,100)+inputfield('debt','Nouvelle dette A1 (M MAD)',14,0,40)+inputfield('rate','Taux nouvelle dette (%)',6,0,30)+inputfield('equity','Apport A1 (M MAD)',0,0,40)
  return f'<section id="outil" class="interactive"><h2>Laboratoire — Recalculer le plan</h2><p>Modifier les hypothèses puis calculer. Un seul modèle actualise exploitation, intérêts, impôt, BFR et trésorerie. Remboursement linéaire du principal du nouveau prêt sur cinq ans ; aucun dividende.</p><form data-type="forecast"><div class="controls">{fields}</div><p><button type="submit">Recalculer le plan</button> <button type="reset">Réinitialiser</button></p></form><output id="sim-output" aria-live="polite"></output></section>'
 config={1:('diagnostic',inputfield('ca','CA (M MAD)',100,0,1000)+inputfield('variable','Charges variables / CA (%)',60,0,100)+inputfield('fixed','Charges fixes (M MAD)',24,0,500),'Explorer le levier opérationnel'),3:('financement',inputfield('capital','Capital emprunté (M MAD)',10,.1,100)+inputfield('coupon','Taux nominal annuel (%)',5.5,0,50)+inputfield('fees','Frais initiaux (M MAD)',.1,0,100),'Comparer coût affiché et coût effectif'),4:('strategie',inputfield('ppa','Paiement annuel PPA (M MAD)',1.35,0,5)+inputfield('discount','Taux d’actualisation (%)',10,0,30),'Comparer détention, contrat et leasing'),6:('pilotage',inputfield('production','Croissance de la production (%)',20,-90,200)+inputfield('intensity','Baisse de l’intensité (%)',10,-100,100),'Relier intensité et quantité totale')}
 typ,fields,title=config[n]
 return f'<section id="outil" class="interactive"><h2>Laboratoire — {title}</h2><form data-type="{typ}"><div class="controls">{fields}</div><p><button type="submit">Calculer</button> <button type="reset">Réinitialiser</button></p></form><output id="simple-output" aria-live="polite"></output></section>'
def modeltable(name):
 rows=DATA[name]
 return '<table><tr><th>Année</th><th>CA</th><th>EBITDA</th><th>Cash final</th><th>DSCR</th></tr>'+''.join('<tr>'+''.join(f'<td>{v}</td>' for v in [f'A{x["annee"]}',f'{x["ca"]:.3f}',f'{x["ebitda"]:.3f}',f'{x["tresorerie_cloture"]:.3f}',f'{x["dscr"]:.3f}'])+'</tr>' for x in rows)+'</table>'

# Figures SVG précises, générées à partir des calculs pédagogiques.
def chart(path,series,labels,title,ylabel='M MAD'):
 w,h=760,300; left,right,top,bottom=60,20,45,50
 vals=[v for _,vs in series for v in vs];lo=min(0,min(vals));hi=max(vals);span=hi-lo or 1;lo-=span*.1;hi+=span*.1
 xx=lambda i:left+(w-left-right)*i/max(1,len(labels)-1)
 yy=lambda v:top+(h-top-bottom)*(hi-v)/(hi-lo)
 colors=['#0f766e','#346b82','#b45309'];s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}"><rect width="100%" height="100%" fill="white"/><text x="{left}" y="20" font-family="sans-serif" font-size="16" font-weight="bold">{escape(title)}</text>']
 for j in range(5):
  v=lo+(hi-lo)*j/4;y=yy(v);s.append(f'<line x1="{left}" y1="{y}" x2="{w-right}" y2="{y}" stroke="#dae2e6"/><text x="{left-8}" y="{y+4}" text-anchor="end" font-family="sans-serif" font-size="12">{v:.1f}</text>')
 for i,label in enumerate(labels):s.append(f'<text x="{xx(i)}" y="{h-bottom+22}" text-anchor="middle" font-family="sans-serif" font-size="12">{escape(str(label))}</text>')
 for j,(name,vs) in enumerate(series):
  co=colors[j%3];points=' '.join(f'{xx(i)},{yy(v)}' for i,v in enumerate(vs));s.append(f'<polyline points="{points}" fill="none" stroke="{co}" stroke-width="3"/>')
  for i,v in enumerate(vs):s.append(f'<circle cx="{xx(i)}" cy="{yy(v)}" r="4" fill="{co}"/>')
  s.append(f'<text x="{left+j*205}" y="{h-5}" font-family="sans-serif" font-size="12" fill="{co}">{escape(name)}</text>')
 s.append('</svg>');(ROOT/path).write_text(''.join(s))

for n,s in enumerate(SESSIONS,1):
 out=ROOT/f'seance{n}';out.mkdir(exist_ok=True)
 raw=''.join(b for _,b in s['sections']);keys=list(dict.fromkeys(re.findall(r'\[([A-Z0-9]+)\]',raw)))
 sides='<aside class="side" aria-label="Sommaire de la séance"><b>Dans cette séance</b>'+''.join(f'<a href="#part{i}">{escape(title)}</a>' for i,(title,_) in enumerate(s['sections'],1))+'<a href="#outil">Laboratoire de calcul</a><a href="#references">Références</a><a href="../glossaire/">Glossaire</a></aside>'
 application_minutes,case_minutes=(65,35) if n==6 else (70,30)
 schedule=f'problème initial (15 min), concepts et approfondissements (55 min), exemples résolus (30 min), applications chiffrées ({application_minutes} min), cas de synthèse ({case_minutes} min), synthèse et transition (10 min)'
 body=f'<section><p class="smallcaps">Séance {n} · 3 h 30 · Cours et approfondissements</p><h2>Objectifs et parcours</h2><ul class="objective">'+''.join(f'<li>{escape(o)}</li>' for o in s['objectives'])+f'</ul><p>Parcours conseillé : {schedule}. Total : 210 minutes. Les sept applications sont organisées en deux séries progressives ; les corrigés et le laboratoire accompagnent la relecture.</p><div class="quick">'+f'<a href="polycopie-seance{n}.pdf">Télécharger le polycopié PDF</a><a href="polycopie-seance{n}.tex">Source LaTeX</a><a href="../downloads/dossier-cas.csv">Données communes CSV</a></div><button id="show-solutions" aria-expanded="false">Déplier les corrigés</button></section>'
 for i,(title,b) in enumerate(s['sections'],1):
  if 'data-model-table' in b:b=re.sub(r'<div data-model-table="(.*?)"></div>',lambda m:modeltable(m[1]),b)
  body+=f'<section id="part{i}"><h2>{escape(title)}</h2>{citations(b)}</section>'
  if i==5 and n in [1,2,3,5]:
   name='base' if n in [1,2,3] else 'stress'
   if n!=1:body+=f'<section><h2>Lecture graphique</h2><figure><img class="chart" src="../assets/{name}.svg" alt="Trajectoires de trésorerie calculées à partir du modèle commun"><figcaption>Données pédagogiques, M MAD. Calculs non arrondis dans les CSV. Les seuils et le calendrier restent propres au cas.</figcaption></figure></section>'
 body+=tool(n)+f'<section id="references"><h2>Références mobilisées</h2>{bibliography(keys)}<p class="small">Les calculs, exercices et données du cas sont des constructions pédagogiques originales. Les sources fondent les concepts et précautions indiqués, sans constituer une validation des paramètres fictifs.</p></section>'
 body+='<div class="pager">'+(f'<a href="../seance{n-1}/">← Séance {n-1}</a>' if n>1 else '<a href="../">← Accueil</a>')+(f'<a href="../seance{n+1}/">Séance {n+1} →</a>' if n<6 else '<a href="../cas/">Revenir au dossier commun →</a>')+'</div>'
 (out/'index.html').write_text(page(s['title'],body,'../',n,s['question'],sides))

chart('assets/base.svg',[('Trésorerie de référence',[x['tresorerie_cloture'] for x in DATA['base']]),('Réserve minimale',[3]*5)],['A1','A2','A3','A4','A5'],'Trajectoire de trésorerie — référence')
chart('assets/stress.svg',[(name,[x['tresorerie_cloture'] for x in DATA[key]]) for name,key in [('Référence','base'),('Défavorable','adverse'),('Sévère','severe')]],['A1','A2','A3','A4','A5'],'Cash final selon les scénarios')

home='<section><h2>Décider et financer une trajectoire de transition</h2><p>Comment transformer un diagnostic en stratégie finançable, résistante aux chocs et suivie dans le temps ? Six séances combinent mécanismes théoriques, exemples résolus, sept applications corrigées, un cas de synthèse et un laboratoire de calcul.</p><div class="quick"><a href="#feuille-de-route">Voir la feuille de route</a><a href="seance1/">Commencer la séance 1</a><a href="cas/">Ouvrir le cas fil rouge</a><a href="downloads/cours-complet.pdf">Télécharger le cours complet</a></div><p class="callout">Les montants et paramètres de Maghreb Agro-Industries sont fictifs. L’évaluation formelle sera préparée ultérieurement ; ce site présente le cours et les exercices d’apprentissage.</p></section>'
home+=render_roadmap(SESSIONS)
home+='<section><h2>Un dossier qui évolue avec les décisions</h2><p>Maghreb Agro-Industries doit moderniser sa production, réduire sa dépendance à l’énergie et à l’eau et préserver sa capacité de financement. Les six séances utilisent les mêmes comptes et conventions ; chaque nouvelle information appelle un recalcul argumenté.</p><div class="quick"><a href="cas/">Données et conventions</a><a href="glossaire/">Glossaire et formules</a><a href="bibliographie/">Bibliographie commentée</a><a href="downloads/prevision-base.csv">Prévision de référence CSV</a></div></section><section><h2>Comment travailler</h2><p>Lire la question initiale, étudier les concepts, refaire les calculs puis ouvrir les corrections. Utiliser les laboratoires pour tester une hypothèse et expliquer le mécanisme qui change le résultat. Les corrigés sont accessibles librement pour l’apprentissage. Les polycopiés et leurs sources LaTeX sont disponibles dans chaque séance.</p><p>Les CSV s’importent dans Excel avec le séparateur point-virgule et le point comme séparateur décimal d’origine. Le code Python du modèle et les résultats JSON permettent de reproduire les calculs sans dépendance externe.</p><div class="quick"><a href="scripts/model.py">Modèle Python</a><a href="downloads/resultats-verifies.json">Résultats détaillés JSON</a></div></section>'
(ROOT/'index.html').write_text(page('Management financier et prise de décision stratégique',home,question='Diagnostiquer, planifier, financer, arbitrer, adapter et piloter.'))

(ROOT/'bibliographie').mkdir(exist_ok=True)
bib='<section><h2>Sources et usages</h2><p>Les références sont citées dans les développements concernés et à la fin de chaque séance. Les manuels encadrent les méthodes ; les articles explicitent les mécanismes théoriques ; les institutions fournissent les cadres de finance durable et de scénarios.</p><p>Lecture de départ : Schoenmaker et Schramade pour l’articulation finance–durabilité ; Berk et DeMarzo et Vernimmen pour les méthodes ; Damodaran pour les applications. Les programmes MIT servent de repères pédagogiques. Les paramètres du cas ne sont pas des estimations extraites de ces sources.</p>'+bibliography(list(REFS))+'</section>'
(ROOT/'bibliographie/index.html').write_text(page('Bibliographie et sources',bib,'../',question='Des références identifiées, reliées à leurs usages.'))

(ROOT/'cas').mkdir(exist_ok=True)
case='<section><h2>Le mandat de la direction financière</h2><p>Maghreb Agro-Industries, entreprise fictive au Maroc, transforme des produits agricoles pour les marchés intérieur et d’exportation. Elle veut préserver la qualité du service tout en réduisant ses dépendances à l’énergie et à l’eau. Son comité doit choisir un programme, un financement et des règles d’adaptation.</p><p class="callout">Aucune donnée ne décrit une entreprise réelle. Les taux, seuils, facteurs et contrats sont des hypothèses pédagogiques. Les conclusions ne sont pas des recommandations d’investissement.</p></section>'
case+='<section><h2>Pièce 1 — Comptes de départ</h2>'+SESSIONS[0]['sections'][1][1]+'</section><section><h2>Pièce 2 — Programme et calendrier</h2>'+SESSIONS[1]['sections'][1][1]+'</section><section><h2>Pièce 3 — Offres de financement</h2>'+SESSIONS[2]['sections'][3][1]+'</section><section><h2>Pièce 4 — Scénarios</h2>'+SESSIONS[4]['sections'][1][1]+'</section>'
case+='<section><h2>Pièce 5 — Conventions de calcul et fichiers</h2><ul><li>Montants : M MAD ; CA et coûts nominaux ; A1 à A5 après l’année N historique.</li><li>Impôt pédagogique : 25 %, sans crédit immédiat en cas de perte ni report fiscal.</li><li>Dette existante à 6 %, remboursement 2/an ; nouveau prêt de référence 14 à 6 %, remboursement 2,8/an.</li><li>Intérêts sur ouverture incluant le nouveau tirage dès A1 ; principal remboursé en fin d’année.</li><li>Pas de dividendes prévisionnels ; BFR = 20 % du CA ; amortissement distinct du CAPEX.</li><li>Seuils pédagogiques : cash de réserve 3 ; DSCR d’alerte 1,20.</li><li>Comparaison S4 à une date de mise en service commune et sur dix ans ; ne pas confondre avec le plan A1–A5.</li></ul><div class="quick"><a href="../downloads/dossier-cas.csv">Dossier numérique CSV</a><a href="../downloads/prevision-base.csv">Référence</a><a href="../downloads/prevision-adverse.csv">Défavorable</a><a href="../downloads/prevision-severe.csv">Sévère</a><a href="../scripts/model.py">Code du modèle</a></div></section>'
(ROOT/'cas/index.html').write_text(page('Maghreb Agro-Industries — Dossier commun',case,'../',question='Un même cas pour les six séances de 3 h 30.'))

GLOSS=[('BFR','Besoin en fonds de roulement : stocks + créances d’exploitation − dettes d’exploitation. Sa variation est un flux.'),('CAPEX / OPEX','Dépenses d’investissement / charges d’exploitation. Le classement dépend de la nature de la dépense.'),('CFO','Flux de trésorerie d’exploitation ; ici après intérêts et impôt, selon la convention explicite du cas.'),('EBITDA / EBIT','Résultat opérationnel avant / après amortissements dans le modèle simplifié. L’EBITDA n’est pas un flux de cash.'),('NOPAT / ROIC','Résultat opérationnel après impôt théorique / rentabilité des capitaux investis.'),('FCFF','Flux disponibles pour l’ensemble des apporteurs de capitaux avant le service de dette ; cohérence requise avec le taux.'),('CFADS / DSCR','Flux disponible au service de la dette / rapport de ce flux aux intérêts et remboursements, selon une définition contractuelle.'),('WACC / CAPM','Coût moyen pondéré du capital / modèle d’estimation du rendement requis des fonds propres sous hypothèses.'),('VAN','Valeur actuelle nette des flux incrémentaux, à une date et à un taux explicités.'),('PPA','Contrat d’achat d’électricité ; prix, volumes, durée, risques et attributs à examiner.'),('Covenant','Engagement contractuel, financier ou opérationnel, à reproduire selon les termes du contrat.'),('Option réelle','Faculté d’adapter une décision d’investissement après information nouvelle.'),('Intensité / absolu','Impact par unité de production / impact total. Leur évolution peut diverger.'),('Prix interne du carbone','Paramètre de décision ou prélèvement interne selon le dispositif ; pas automatiquement un flux externe.')]
(ROOT/'glossaire').mkdir(exist_ok=True)
(ROOT/'glossaire/index.html').write_text(page('Glossaire et conventions', '<section><h2>Les notions du module</h2><table><tr><th>Terme</th><th>Définition</th></tr>'+''.join(f'<tr><th scope="row">{escape(a)}</th><td>{escape(b)}</td></tr>' for a,b in GLOSS)+'</table><p>Les formules et leurs conditions d’emploi sont développées dans les séances. Sources : manuels Berk–DeMarzo et Vernimmen, ressources Damodaran et références sectorielles citées.</p></section>','../'))

rows=[['parametre','valeur','unite','statut'],['CA_N',100,'M MAD','fictif'],['variable_CA',.6,'ratio','hypothese'],['fixes_N',24,'M MAD','fictif'],['amort_N',4,'M MAD','fictif'],['cash_N',4,'M MAD','fictif'],['dette_N',22,'M MAD','fictif'],['BFR_N',20,'M MAD','fictif'],['croissance_CA',.05,'ratio annuel','hypothese'],['croissance_fixes',.02,'ratio annuel','hypothese'],['BFR_CA',.2,'ratio','hypothese'],['impot',.25,'ratio','hypothese fiscale pedagogique'],['nouvelle_dette',14,'M MAD A1','hypothese'],['taux_dette',.06,'ratio annuel','hypothese'],['maintenance',4,'M MAD/an','hypothese'],['E',6,'M MAD A1','hypothese'],['S',10,'M MAD A1','hypothese'],['W',4,'M MAD A2','hypothese'],['gain_E',1.8,'M MAD/an des A2','hypothese'],['gain_S',2,'M MAD/an des A2','hypothese'],['gain_W',.7,'M MAD/an des A3','hypothese'],['seuil_cash',3,'M MAD','politique du cas'],['seuil_DSCR',1.2,'ratio','alerte du cas']]
import csv
with (ROOT/'downloads/dossier-cas.csv').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f,delimiter=';').writerows(rows)

# Conversion des mêmes sources HTML vers un document LaTeX autonome.
def tex(t):
 t=t.replace('\u202f',' ').replace('\xa0',' ').replace('−','-').replace('–','--').replace('—','---')
 mapping={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','Δ':r'$\Delta$','×':r'$\times$','→':r'$\rightarrow$','←':r'$\leftarrow$','≤':r'$\leq$','≥':r'$\geq$','≈':r'$\approx$'}
 return ''.join(mapping.get(c,c) for c in t)
def walk(el):
 tag=el.tag if isinstance(el.tag,str) else ''
 inner=tex(el.text or '')+''.join(walk(ch)+tex(ch.tail or '') for ch in el)
 if tag in ('b','strong'):return r'\textbf{'+inner+'}'
 if tag in ('i','em'):return r'\textit{'+inner+'}'
 if tag=='br':return r'\newline '
 if tag in ('p','figcaption'):return inner+'\n\n'
 if tag in ('h2','h3'):return '\n\\subsection*{'+inner+'}\n'
 if tag=='li':return '\\item '+inner+'\n'
 if tag in ('ul','ol'):return '\n\\begin{itemize}\n'+inner+'\\end{itemize}\n'
 if tag=='summary':return '\n\\paragraph{'+inner+'}\n'
 if tag=='div' and el.get('class')=='formula':return '\n\\begin{quote}\\small '+inner+'\\end{quote}\n'
 if tag=='table':
  rows=el.xpath('.//tr');n=max(len(row) for row in rows);width=(16.7-.5*n)/n
  parts=['\n\\Needspace{'+str(min(430,40+len(rows)*35))+'pt}\n\\begin{longtable}{'+''.join('p{'+f'{width:.2f}'+'cm}' for _ in range(n))+'}\n\\toprule\n']
  for i,row in enumerate(rows):parts.append(' & '.join(walk(c) for c in row)+r' \\'+'\n'+('\\midrule\\endhead\n' if i==0 else ''))
  return ''.join(parts)+'\\bottomrule\n\\end{longtable}\n'
 return inner
PRE=r'''\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage[provide=*,french]{babel}
\usepackage{lmodern,microtype,longtable,booktabs,array,enumitem,fancyhdr,needspace}
\usepackage[margin=2.1cm,headheight=16pt]{geometry}
\usepackage[hidelinks,breaklinks=true]{hyperref}
\setlength{\parindent}{0pt}\setlength{\parskip}{6pt}\setlength{\emergencystretch}{3em}
\setlist[itemize]{leftmargin=1.3em,itemsep=3pt}
\pagestyle{fancy}\fancyhf{}\fancyhead[L]{\small Master Finance verte — Module 6}\fancyhead[R]{\small Badr Aboufarasse}\fancyfoot[C]{\thepage}
\begin{document}
'''
def latexbody(n,s):
 text='\\begin{center}{\\small MASTER FINANCE VERTE -- MODULE 6}\\par\\vspace{8pt}{\\Large\\bfseries Séance '+str(n)+' -- '+tex(s['title'])+'}\\par\\vspace{6pt}Badr Aboufarasse\\par{\\small Cours et applications corrigées -- 25 octobre 2026}\\end{center}\n'
 text+='\\begin{quote}\\itshape '+tex(s['question'])+'\\end{quote}\n'
 text+='\\textbf{Données du cas fictives.} Montants en M MAD ; taux et seuils pédagogiques.\\par Durée : 3 h 30 par séance ; 21 heures pour le module.\n\n\\subsection*{Objectifs}\n\\begin{itemize}'+''.join('\\item '+tex(o) for o in s['objectives'])+'\\end{itemize}\n'
 text+='\\subsection*{Déroulé de 3 h 30}\nProblème initial : 15 min ; concepts : 55 min ; exemples résolus : 30 min ; applications : '+str(65 if n==6 else 70)+' min ; cas : '+str(35 if n==6 else 30)+' min ; synthèse : 10 min. Total : 210 min.\n\n'
 raw=''
 for title,b in s['sections']:
  b=re.sub(r'<div data-model-table="(.*?)"></div>',lambda m:modeltable(m[1]),b)
  el=LH.fragment_fromstring(b,create_parent='div');text+='\\section*{'+tex(title)+'}\n'+walk(el);raw+=b
 keys=list(dict.fromkeys(re.findall(r'\[([A-Z0-9]+)\]',raw)))
 text+='\\section*{Références mobilisées}\n\\small\n\\begin{itemize}\n'
 for k in keys:text+='\\item \\textbf{['+k+'] '+tex(REFS[k][0])+'.} '+tex(REFS[k][1])+' \\href{'+REFS[k][2].replace('%',r'\%')+'}{Source officielle}.\n'
 return text+'\\end{itemize}\\normalsize\n'
alltex=PRE
for n,s in enumerate(SESSIONS,1):
 body=latexbody(n,s);p=ROOT/f'seance{n}/polycopie-seance{n}.tex';p.write_text(PRE+body+'\\end{document}\n');alltex+=('\\clearpage\n' if n>1 else '')+body
(ROOT/'downloads/cours-complet.tex').write_text(alltex+'\\end{document}\n')
(ROOT/'README.md').write_text('''# Module 6 — Management financier et prise de décision stratégique

Cours de Badr Aboufarasse. Six séances, 21 heures, Master Finance verte.
Site statique autonome : ouvrir `index.html` ou publier le dossier via GitHub Pages.
L’évaluation formelle est différée. Les données du cas sont fictives.
Le parcours enrichi comporte sept applications chiffrées par séance et conserve les sections initiales. Les approfondissements et variantes sont dans `scripts/enrichment.py`.

## Sources et reproduction
Le texte original est dans `scripts/course.py`, les références dans `scripts/references.py`.
Le modèle annuel sans dépendance externe : `python3 scripts/model.py`.
Le site et les sources LaTeX se reconstruisent avec `python3 scripts/build.py` (nécessite lxml).
Les PDF se compilent avec pdfLaTeX ; le fichier complet est dans `downloads/`.
Les calculs navigateur et Python utilisent les mêmes conventions ; les tests comparent leurs sorties.
Les CSV utilisent UTF-8 BOM, séparateur point-virgule et décimales avec point.

## Conventions
Tous les montants monétaires du modèle sont en millions de MAD. L’impôt de 25 %, les financements, les gains, les seuils et les facteurs physiques sont des hypothèses pédagogiques.
Le modèle annuel ne garantit pas la liquidité intra-annuelle. Aucun conseil d’investissement réel n’est formulé.
''')
print(json.dumps({'sessions':len(SESSIONS),'words':sum(len(re.sub('<[^>]+>',' ',b).split()) for s in SESSIONS for _,b in s['sections']),'references':len(REFS),'html':len(list(ROOT.rglob('*.html')))},ensure_ascii=False))
