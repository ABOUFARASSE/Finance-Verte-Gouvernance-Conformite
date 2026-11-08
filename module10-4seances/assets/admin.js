'use strict';
const ENDPOINT='https://qrkzgapnevjzwkosgsnx.supabase.co/functions/v1/module10-qcm-v2';
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let key='',data=null;
async function call(action,payload={}){const r=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key,action,payload})});const d=await r.json();if(!r.ok||d.error)throw Error(d.error||'Erreur de connexion');return d;}
async function load(){
 try{data=await call('admin');$('admin-work').hidden=false;$('error').textContent='';$('toggle').textContent=data.open?'Fermer les nouvelles tentatives':'Ouvrir les nouvelles tentatives';
 const rows=data.students.filter(s=>s.started>0);$('summary').textContent=`${rows.length} accès utilisé(s) · ${rows.filter(s=>s.validated>0).length} étudiant(s) avec au moins une tentative validée · nouvelles tentatives ${data.open?'ouvertes':'fermées'}.`;
 $('rows').innerHTML=rows.map(s=>`<tr><td>${esc(s.label)}</td><td>${esc(s.student_name)}</td><td>${s.started}</td><td>${s.attempts.map(a=>'T'+a.number+' : '+(a.score===null?'en cours':a.score+'/20')).join('<br>')}</td><td>${s.best===null?'—':s.best+' / 20'}</td></tr>`).join('')||'<tr><td colspan="5">Aucune tentative pour le moment.</td></tr>';
 }catch(e){$('error').textContent=e.message;}
}
$('admin-form').onsubmit=e=>{e.preventDefault();key=$('admin-key').value.trim().toUpperCase();load()};
$('refresh').onclick=load;
$('toggle').onclick=async()=>{if(!confirm('Modifier l’ouverture des nouvelles tentatives ? Les tentatives déjà commencées resteront reprenables et validables.'))return;try{await call('toggle',{open:!data.open});await load()}catch(e){$('error').textContent=e.message}};
$('export').onclick=()=>{
 if(!data)return;
 const safe=v=>{let s=String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"'};
 const rows=[['Repère','Nom déclaré','Tentatives commencées','Tentatives validées','Tentative 1 /20','Tentative 2 /20','Tentative 3 /20','Meilleur score /20','Dernière validation UTC']];
 data.students.filter(s=>s.started>0).forEach(s=>rows.push([s.label,s.student_name,s.started,s.validated,...[1,2,3].map(n=>s.attempts.find(a=>a.number===n)?.score??''),s.best??'',s.attempts.filter(a=>a.submitted_at).at(-1)?.submitted_at??'']));
 const blob=new Blob(['\ufeff'+rows.map(r=>r.map(safe).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Module10_Resultats_QCM.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
};
$('admin-logout').onclick=()=>location.reload();
