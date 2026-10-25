"""Modèle pédagogique unique. Montants en millions de MAD. Aucune donnée réelle."""
import json,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def forecast(shock=0,energy=0,new_debt=14,rate=.06,equity=0):
    out=[];cash=4;bfr=20;old=22;new=0
    for y in range(1,6):
        ca=100*1.05**y*(1-shock); fixed=24*1.02**y
        es=3.8 if y>=2 else 0;ws=.7 if y>=3 else 0
        energy_extra=energy*max(0,8*1.02**y-es)
        ebitda=.4*ca-fixed+es+ws-energy_extra
        dep=4+(1.6 if y>=2 else 0)+(.4 if y>=3 else 0)
        draw=new_debt if y==1 else 0
        interest=old*.06+(new+draw)*rate
        tax=max(0,(ebitda-dep-interest)*.25)
        newbfr=.2*ca;dbfr=newbfr-bfr
        capex=20 if y==1 else (8 if y==2 else 4)
        rpold=min(2,old);rpnew=min(new_debt/5,new+draw)
        cfo=ebitda-interest-tax-dbfr
        cfads=ebitda-tax-dbfr-4
        close=cash+cfo-capex+draw+(equity if y==1 else 0)-rpold-rpnew
        old-=rpold;new+=draw-rpnew
        out.append(dict(annee=y,ca=ca,couts_variables=.6*ca,couts_fixes=fixed,economies_energie=es,economies_eau=ws,surcout_energie=energy_extra,ebitda=ebitda,amortissement=dep,ebit=ebitda-dep,interets=interest,impot=tax,resultat_net=ebitda-dep-interest-tax,bfr=newbfr,delta_bfr=dbfr,cfo=cfo,capex=capex,dette_nouvelle=draw,apport=equity if y==1 else 0,principal=rpold+rpnew,tresorerie_ouverture=cash,tresorerie_cloture=close,dette_cloture=old+new,cfads=cfads,dscr=cfads/(interest+rpold+rpnew),marge_tresorerie=close-3))
        cash=close;bfr=newbfr
    return out
def af(r=.1,n=10):return sum((1+r)**(-t) for t in range(1,n+1))
def results():
    return dict(base=forecast(),adverse=forecast(.1,.3),severe=forecast(.2,.5),annuity_factor=af(),npv_solaire=-10+1.75*af(),npv_ppa=-.5+.7125*af(),npv_leasing=.2625*af(),npv_efficacite=-6+1.5*af(),npv_eau=-4+.625*af())
if __name__=='__main__':
    d=results(); dest=ROOT/'downloads'; dest.mkdir(exist_ok=True)
    (dest/'resultats-verifies.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
    for name in ['base','adverse','severe']:
        with (dest/f'prevision-{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=d[name][0].keys(),delimiter=';');w.writeheader();w.writerows(d[name])
    for name in ['base','adverse','severe']:
        print(name,[(x['annee'],round(x['tresorerie_cloture'],3),round(x['dscr'],3)) for x in d[name]])
    print({k:round(v,5) for k,v in d.items() if isinstance(v,float)})
