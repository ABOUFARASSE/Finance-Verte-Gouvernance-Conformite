'use strict';
const ENDPOINT='https://qrkzgapnevjzwkosgsnx.supabase.co/functions/v1/module10-qcm-v2';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let key='',state=null,current=null,answers={},timer=null,chain=Promise.resolve(),busy=false,dirty=false,seq=0,lastResult=null;
async function api(action,payload={}){
 const r=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key,action,payload})});
 const d=await r.json();if(!r.ok||d.error)throw Error(d.error||'Demande refusée');return d;
}
function message(text,error=false){$('message').textContent=text;$('message').className='notice'+(error?' error':'');$('message').hidden=!text;}
function controls(disabled){document.querySelectorAll('button').forEach(b=>b.disabled=disabled);document.querySelectorAll('#quiz input').forEach(e=>e.disabled=disabled);}
function progress(){const n=Object.keys(answers).length;$('progress').value=n;$('progress-label').textContent=`${n} / 20 réponses renseignées`;}
function persist(){
 if(!current)return chain;
 const version=++seq,id=current.id,snapshot={...answers};
 $('save-state').textContent='Sauvegarde en cours…';
 chain=chain.catch(()=>{}).then(()=>api('save',{attempt:id,answers:snapshot}));
 chain.then(()=>{if(version===seq){dirty=false;$('save-state').textContent='Réponses enregistrées.';}}).catch(()=>{$('save-state').textContent='Sauvegarde interrompue. Gardez cette page ouverte et réessayez.';});
 return chain;
}
function renderStatus(d){
 state=d;current=d.current;$('workspace').hidden=false;$('login').hidden=true;
 $('identity').textContent=d.name?`${d.name} · ${d.label}`:d.label;
 $('best').textContent=d.best===null?'Aucun score validé':`Meilleur score retenu : ${d.best} / 20`;
 $('remaining').textContent=`${d.started} tentative(s) commencée(s) sur 3 · ${d.remaining} nouvelle(s) tentative(s) disponible(s).`;
 $('name-label').hidden=!!d.name;$('start').hidden=!!current||d.remaining===0||!d.open;
 $('closed').hidden=d.open||!!current;
 $('history').innerHTML=d.history.length?'<h3>Vos tentatives</h3><ul>'+d.history.map(x=>`<li>Tentative ${x.number} : ${x.score===null?'en cours':esc(x.score)+' / 20 <button type="button" data-review="'+esc(x.id)+'">Revoir le corrigé</button>'}</li>`).join('')+'</ul>':'';
 $('history').querySelectorAll('[data-review]').forEach(b=>b.onclick=async()=>{try{controls(true);showCorrection(await api('review',{attempt:b.dataset.review}));message('');}catch(e){message(e.message,true)}finally{controls(false)}});
 $('quiz-wrap').hidden=!current;
 if(!current){$('quiz').innerHTML='';return;}
 answers=current.answers||{};
 $('attempt-title').textContent=`Tentative ${current.number} / 3`;
 $('quiz').innerHTML=current.questions.map((q,i)=>`<fieldset id="question-${i+1}"><legend>${i+1}. ${esc(q.question)}</legend><p class="muted">Séance ${q.session}${q.difficulty ? " · "+(q.difficulty === "simple" ? "Repérage simple" : "Compréhension") : ""}</p>${q.options.map((o,j)=>`<label class="option"><input type="radio" name="${esc(q.id)}" value="${j}" ${answers[q.id]===j?'checked':''}><span>${esc(o)}</span></label>`).join('')}</fieldset>`).join('');
 $('quiz').querySelectorAll('input').forEach(e=>e.onchange=()=>{answers[e.name]=Number(e.value);dirty=true;progress();clearTimeout(timer);timer=setTimeout(persist,400);});
 $('save-state').textContent='Tentative reprise ; les réponses enregistrées sont affichées.';progress();
}
function showCorrection(d){
 lastResult=d;$('result').hidden=false;
 $('result-title').textContent=`Tentative ${d.number} : ${d.score} / 20 · meilleur score : ${d.best} / 20`;
 $('corrections').innerHTML=d.corrections.map((q,i)=>`<article class="card ${q.is_correct?'right':'wrong'}"><h3>${i+1}. ${esc(q.question)}</h3><p><strong>Votre réponse :</strong> ${q.selected===null?'Non renseignée':esc(q.options[q.selected])}</p><p><strong>Bonne réponse :</strong> ${esc(q.options[q.correct])}</p><p><strong>Explication :</strong> ${esc(q.explanation)}</p><a href="${esc(q.source)}" target="_blank" rel="noopener">Revoir le passage du cours · séance ${q.session}</a></article>`).join('');
 $('result').scrollIntoView({behavior:'smooth'});
}
$('login-form').onsubmit=async e=>{e.preventDefault();key=$('access-code').value.trim().toUpperCase();try{controls(true);renderStatus(await api('status'));sessionStorage.setItem('m10v2-key',key);message('');}catch(err){message(err.message,true)}finally{controls(false)}};
$('start').onclick=async()=>{
 const name=$('student-name').value.trim();
 if(!state.name&&name.length<2){message('Indiquez votre nom complet avant de commencer.',true);return;}
 if(!confirm('Commencer une tentative ? Elle sera décomptée parmi les trois disponibles. Vous pourrez la reprendre avant validation.'))return;
 try{controls(true);$('result').hidden=true;renderStatus(await api('start',{name}));message('');$('quiz-wrap').scrollIntoView();}catch(e){message(e.message,true)}finally{controls(false)}
};
$('save').onclick=async()=>{clearTimeout(timer);try{controls(true);await persist();message('Réponses enregistrées. Vous pouvez reprendre cette tentative avec le même code.');}catch(e){message('Enregistrement impossible. Gardez cette page ouverte et réessayez.',true)}finally{controls(false)}};
$('validate').onclick=async()=>{
 const missing=20-Object.keys(answers).length;
 if(!confirm((missing?`${missing} question(s) sans réponse compteront zéro. `:'')+'Valider définitivement cette tentative et afficher le corrigé ?'))return;
 clearTimeout(timer);busy=true;controls(true);
 try{await chain.catch(()=>{});const d=await api('submit',{attempt:current.id,answers:{...answers}});dirty=false;renderStatus(await api('status'));showCorrection(d);message('Tentative validée et score enregistré.');}
 catch(e){message(e.message+' Si la validation a abouti malgré une interruption réseau, reconnectez-vous pour retrouver le résultat.',true)}
 finally{busy=false;controls(false)}
};
$('logout').onclick=()=>{if((dirty||busy)&&!confirm('Des modifications ne sont peut-être pas encore enregistrées. Quitter quand même ?'))return;clearTimeout(timer);sessionStorage.removeItem('m10v2-key');location.reload();};
$('download').onclick=()=>{if(!lastResult)return;const content={module:'Module 10',student:state.name,reference:state.label,...lastResult};const blob=new Blob([JSON.stringify(content,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`Module10_${state.label}_tentative_${lastResult.number}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
$('print').onclick=()=>window.print();
window.addEventListener('beforeunload',e=>{if(dirty||busy){e.preventDefault();e.returnValue='';}});
const remembered=sessionStorage.getItem('m10v2-key');if(remembered){$('access-code').value=remembered;$('login-form').requestSubmit();}

