'use strict';
const ENDPOINT='https://qrkzgapnevjzwkosgsnx.supabase.co/functions/v1/module10-qcm-v2';
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let key='',data=null,clockOffset=0,busy=false;
async function call(action,payload={}){const r=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key,action,payload})});const d=await r.json();if(!r.ok||d.error)throw Error(d.error||'Erreur de connexion');return d;}
function duration(seconds){seconds=Math.max(0,Math.floor(seconds));const h=Math.floor(seconds/3600),m=Math.floor(seconds%3600/60),s=seconds%60;return `${h} h ${String(m).padStart(2,'0')} min ${String(s).padStart(2,'0')} s`;}
function date(iso){return iso?new Date(iso).toLocaleString('fr-FR'):'En cours';}
function tick(){document.querySelectorAll('[data-clock-start]').forEach(el=>{const end=el.dataset.clockEnd?Date.parse(el.dataset.clockEnd):Date.now()+clockOffset;el.textContent=duration((end-Date.parse(el.dataset.clockStart))/1000);});}
function lock(on){busy=on;document.querySelectorAll('#admin-work button,#admin-form button').forEach(b=>b.disabled=on);}
async function load(){
 if(busy)return;
 lock(true);
 try{
  data=await call('admin');clockOffset=Date.parse(data.server_now)-Date.now();$('admin-work').hidden=false;$('error').textContent='';$('toggle').textContent=data.open?'Fermer les nouvelles tentatives':'Ouvrir les nouvelles tentatives';
  const rows=data.students.filter(s=>s.started>0);$('summary').textContent=`${rows.length} accès utilisé(s) · ${rows.filter(s=>s.validated>0).length} étudiant(s) avec au moins une tentative validée · nouvelles tentatives ${data.open?'ouvertes':'fermées'}.`;
  $('rows').innerHTML=rows.map(s=>`<tr><td>${esc(s.label)}</td><td>${esc(s.student_name)}</td><td>${s.started} / 3</td><td>${s.attempts.map(a=>`<div style="border-bottom:1px solid #dae2e6;padding:12px 0"><strong>Tentative ${a.number} : ${a.score===null?'en cours':a.score+' / 20'}</strong><br><span>Début : ${esc(date(a.started_at))}</span><br><span>${a.submitted_at?'Validation : '+esc(date(a.submitted_at)):'Non validée'}</span><br><strong>Durée écoulée : <span data-clock-start="${esc(a.started_at)}" data-clock-end="${esc(a.submitted_at||'')}">${duration(a.elapsed_seconds)}</span></strong><p><button type="button" style="background:#9c3232" data-delete="${esc(a.id)}" data-label="${esc(s.label)}" data-number="${a.number}">Supprimer cette tentative</button></p></div>`).join('')}</td><td>${s.best===null?'—':s.best+' / 20'}</td></tr>`).join('')||'<tr><td colspan="5">Aucune tentative pour le moment.</td></tr>';
  $('rows').querySelectorAll('[data-delete]').forEach(button=>button.onclick=async()=>{
   if(busy)return;
   if(!confirm(`Supprimer définitivement la tentative ${button.dataset.number} de ${button.dataset.label} ?\n\nSes réponses et son score seront supprimés. Une tentative sera libérée et le meilleur score sera recalculé. Cette action est irréversible.`))return;
   lock(true);
   try{await call('delete_attempt',{attempt:button.dataset.delete,confirmed:true});lock(false);await load();$('error').textContent='Tentative supprimée. Le quota et le meilleur score ont été recalculés.';}
   catch(e){$('error').textContent=e.message;}
   finally{lock(false)}
  });
  tick();
 }catch(e){$('error').textContent=e.message;}
 finally{lock(false)}
}
$('admin-form').onsubmit=e=>{e.preventDefault();key=$('admin-key').value.trim().toUpperCase();load()};
$('refresh').onclick=load;
$('toggle').onclick=async()=>{if(busy||!confirm('Modifier l’ouverture des nouvelles tentatives ? Les tentatives déjà commencées resteront reprenables et validables.'))return;lock(true);try{await call('toggle',{open:!data.open});lock(false);await load()}catch(e){$('error').textContent=e.message}finally{lock(false)}};
$('export').onclick=()=>{
 if(!data)return;
 const safe=v=>{let s=String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"'};
 const rows=[['Repère','Nom déclaré','Tentative','Score /20','Début UTC','Validation UTC','Durée écoulée (secondes)','Durée écoulée','Meilleur score /20','Tentatives utilisées']];
 const now=Date.now()+clockOffset;
 data.students.filter(s=>s.started>0).forEach(s=>s.attempts.forEach(a=>{const secs=Math.max(0,Math.floor(((a.submitted_at?Date.parse(a.submitted_at):now)-Date.parse(a.started_at))/1000));rows.push([s.label,s.student_name,a.number,a.score??'',a.started_at,a.submitted_at??'',secs,duration(secs),s.best??'',s.started]);}));
 const blob=new Blob(['\ufeff'+rows.map(r=>r.map(safe).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Module10_Resultats_Durees_QCM.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
};
$('admin-logout').onclick=()=>location.reload();
setInterval(tick,1000);

setInterval(()=>{if(data&&!busy)load()},20000);
