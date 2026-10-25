'use strict';
const fmt=(x,n=3)=>Number(x).toLocaleString('fr-FR',{minimumFractionDigits:n,maximumFractionDigits:n});
const val=id=>Number(document.getElementById(id).value);
function forecast({shock=0,energy=0,debt=14,rate=.06,equity=0}={}){
 let cash=4,bfr=20,old=22,loan=0,out=[];
 for(let y=1;y<=5;y++){
  const ca=100*1.05**y*(1-shock),es=y>=2?3.8:0,ws=y>=3?.7:0;
  const ebitda=.4*ca-24*1.02**y+es+ws-energy*Math.max(0,8*1.02**y-es);
  const dep=4+(y>=2?1.6:0)+(y>=3?.4:0),draw=y===1?debt:0;
  const interest=old*.06+(loan+draw)*rate,tax=Math.max(0,(ebitda-dep-interest)*.25);
  const dbfr=.2*ca-bfr,capex=y===1?20:y===2?8:4;
  const po=Math.min(2,old),pn=Math.min(debt/5,loan+draw);
  const cfo=ebitda-interest-tax-dbfr,cfads=ebitda-tax-dbfr-4;
  cash+=cfo-capex+draw+(y===1?equity:0)-po-pn;
  old-=po;loan+=draw-pn;bfr=.2*ca;
  out.push({y,ca,ebitda,cash,dscr:cfads/(interest+po+pn),debt:old+loan});
 }return out;
}
function table(rows){return '<div class="scroll"><table><caption>Prévisions annuelles — montants en M MAD</caption><thead><tr><th scope="col">Année</th><th scope="col">CA</th><th scope="col">EBITDA</th><th scope="col">Cash final</th><th scope="col">DSCR</th><th scope="col">Dette finale</th></tr></thead><tbody>'+rows.map(r=>`<tr><th scope="row">A${r.y}</th><td>${fmt(r.ca)}</td><td>${fmt(r.ebitda)}</td><td>${fmt(r.cash)}</td><td>${fmt(r.dscr)}</td><td>${fmt(r.debt)}</td></tr>`).join('')+'</tbody></table></div>';}
function runForecast(){const rows=forecast({shock:val('shock')/100,energy:val('energy')/100,debt:val('debt'),rate:val('rate')/100,equity:val('equity')});
 const min=Math.min(...rows.map(r=>r.cash)),ds=Math.min(...rows.map(r=>r.dscr));
 document.getElementById('sim-output').innerHTML=`${table(rows)}<p class="status">Cash minimum aux clôtures : ${fmt(min)} M MAD ; DSCR minimum : ${fmt(ds)}.</p><p>${min<3?'Réserve de trésorerie de 3 non respectée.':'Réserve annuelle de 3 respectée.'} ${ds<1.2?'Seuil pédagogique de DSCR 1,20 non respecté.':'Seuil pédagogique de DSCR 1,20 respecté.'}</p><p>Les intérêts des nouveaux tirages et leur impôt sont recalculés. Ce modèle annuel ne teste pas les pics mensuels, les reports fiscaux, les frais de crédit ou les covenants réels.</p>`;
}
function runSimple(type){let text='';if(type==='diagnostic'){
 const ca=val('ca'),v=val('variable')/100,f=val('fixed');const e=(1-v)*ca-f;const threshold=v<1?f/(1-v):NaN;
 text=`EBITDA : ${fmt(e)} M MAD. Marge : ${ca>0?fmt(e/ca*100,2)+' %':'non définie'}. Seuil d’EBITDA nul : ${Number.isFinite(threshold)?fmt(threshold):'non défini'} M MAD de CA. Hypothèses : part variable constante, coûts fixes inchangés.`;
 }else if(type==='financement'){
 const p=val('capital'),r=val('coupon')/100,f=val('fees'),net=p-f;
 text=net>0?`Produit net reçu : ${fmt(net)} M MAD. Remboursement dans un an : ${fmt(p*(1+r))}. Coût annuel effectif : ${fmt((p*(1+r)/net-1)*100,3)} %. Prêt in fine d’un an ; hors fiscalité et autres coûts.`:'Les frais doivent être inférieurs au capital.';
 }else if(type==='strategie'){
 const p=val('ppa'),r=val('discount')/100;let a=0;for(let t=1;t<=10;t++)a+=(1+r)**(-t);
 text=`VAN détention : ${fmt(-10+1.75*a)} M MAD ; PPA : ${fmt(-.5+(2.3-p)*.75*a)} ; leasing : ${fmt(.2625*a)}. Horizon 10 ans ; taux et flux nominaux ; hypothèses fiscales et contractuelles de la séance. Ce calcul ne refait pas le financement A1–A5.`;
 }else if(type==='pilotage'){
 const growth=val('production')/100,eff=val('intensity')/100;const delta=(1+growth)*(1-eff)-1;
 text=`Variation de la quantité totale : ${fmt(delta*100,2)} %. Calcul : (1 + croissance de production) × (1 − baisse d’intensité) − 1. Suivre simultanément intensité, total et périmètre.`;
 }document.getElementById('simple-output').textContent=text;
}
if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>{
 document.querySelectorAll('[data-model-table]').forEach(e=>{const c=e.dataset.modelTable;e.innerHTML=table(forecast(c==='adverse'?{shock:.1,energy:.3}:{}));});
 document.querySelectorAll('.interactive form').forEach(f=>{f.addEventListener('submit',e=>{e.preventDefault();if(f.dataset.type==='forecast')runForecast();else runSimple(f.dataset.type);});f.addEventListener('reset',()=>setTimeout(()=>{if(f.dataset.type==='forecast')runForecast();else runSimple(f.dataset.type);},0));});
 const f=document.querySelector('.interactive form');if(f){if(f.dataset.type==='forecast')runForecast();else runSimple(f.dataset.type);}
 const reveal=document.getElementById('show-solutions');if(reveal)reveal.addEventListener('click',()=>{const list=[...document.querySelectorAll('details')];const open=list.some(x=>!x.open);list.forEach(x=>x.open=open);reveal.textContent=open?'Replier les corrigés':'Déplier les corrigés';reveal.setAttribute('aria-expanded',String(open));});
});
if(typeof module!=='undefined')module.exports={forecast};
