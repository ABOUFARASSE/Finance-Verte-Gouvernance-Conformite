"""Contrôles du cas : identités financières, équivalence Python/JS et liens locaux."""
import json,subprocess,sys,random,re
from pathlib import Path
from lxml import html
from model import forecast,results
from course import SESSIONS
ROOT=Path(__file__).resolve().parents[1]
cases=[dict(shock=0,energy=0,new_debt=14,rate=.06,equity=0),dict(shock=.1,energy=.3,new_debt=14,rate=.06,equity=0),dict(shock=.2,energy=.5,new_debt=14,rate=.06,equity=0)]
rng=random.Random(42)
cases += [dict(shock=rng.uniform(0,.4),energy=rng.uniform(0,1),new_debt=rng.uniform(0,30),rate=rng.uniform(0,.2),equity=rng.uniform(0,10)) for _ in range(20)]
node=sys.argv[1] if len(sys.argv)>1 else 'node'
js="const m=require(process.argv[1]);const p=JSON.parse(process.argv[2]);process.stdout.write(JSON.stringify(p.map(x=>m.forecast({shock:x.shock,energy:x.energy,debt:x.new_debt,rate:x.rate,equity:x.equity}))));"
out=json.loads(subprocess.check_output([node,'-e',js,str(ROOT/'assets/course.js'),json.dumps(cases)],text=True))
for c,jsrows in zip(cases,out):
 rows=forecast(**c)
 for x,j in zip(rows,jsrows):
  for pykey,jkey in [('ca','ca'),('ebitda','ebitda'),('tresorerie_cloture','cash'),('dscr','dscr'),('dette_cloture','debt')]:
   assert abs(x[pykey]-j[jkey])<1e-9,(pykey,x,j)
  assert abs(x['cfo']-(x['resultat_net']+x['amortissement']-x['delta_bfr']))<1e-9
  assert abs(x['tresorerie_cloture']-(x['tresorerie_ouverture']+x['cfo']-x['capex']+x['dette_nouvelle']+x['apport']-x['principal']))<1e-9
d=results();assert abs(d['base'][0]['tresorerie_cloture']-4.72)<1e-9
assert abs(d['adverse'][0]['tresorerie_cloture']-1.834)<1e-9
assert abs(d['npv_solaire']-.752992435)<1e-8
broken=[];links=0
for p in ROOT.rglob('*.html'):
 tree=html.fromstring(p.read_text());ids=tree.xpath('//@id');assert len(ids)==len(set(ids)),p
 for a in tree.xpath('//*[@href or @src]'):
  url=a.get('href') or a.get('src');links+=1
  if url.startswith(('http:','https:','mailto:')):continue
  parts=url.split('#',1);target=(p.parent/parts[0]).resolve() if parts[0] else p.resolve()
  if target.is_dir():target=target/'index.html'
  if not target.exists():broken.append((str(p),url));continue
  if len(parts)>1 and parts[1] and target.suffix=='.html':
   dest=html.fromstring(target.read_text());assert parts[1] in dest.xpath('//@id'),(p,url)
assert not broken,broken
assert len(SESSIONS)==6
assert sum(b.count('class="exercise"') for s in SESSIONS for _,b in s['sections'])==18
print(json.dumps({'statut':'OK','jeux_hypotheses_python_js':len(cases),'periodes_comparees':len(cases)*5,'liens_locaux_et_externes_recenses':links,'liens_locaux_rompus':len(broken),'seances':6,'applications':18},ensure_ascii=False))
