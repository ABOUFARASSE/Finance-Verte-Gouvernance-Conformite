'use strict';
(() => {
  const URL = 'https://qrkzgapnevjzwkosgsnx.supabase.co';
  const KEY = 'sb_publishable_RLbKPgnOBNWnLtbTfc6XJw_vq9WIpU7';
  const BUCKET = 'module5-audit';
  const TABLE = 'module5_audit_submissions';
  const MAX = 50 * 1024 * 1024;
  const allowed = new Set(['pdf','doc','docx','zip','rar']);
  const form = document.getElementById('submission-form');
  const membersEl = document.getElementById('group-members');
  const emailEl = document.getElementById('submitter-email');
  const fileEl = document.getElementById('submission-file');
  const btn = document.getElementById('upload-submit');
  const statusEl = document.getElementById('upload-status');
  const receiptBtn = document.getElementById('receipt-download');
  let pending = null, receipt = null, complete = false;
  const headers = {apikey:KEY, Authorization:'Bearer '+KEY};
  function status(text, error=false) {
    statusEl.textContent=text;
    statusEl.className=error?'error':'';
  }
  function cleanName(name) {
    return name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^A-Za-z0-9._-]/g,'_').slice(-150);
  }
  function resetPending() { if(!complete) pending=null; }
  [membersEl,emailEl,fileEl].forEach(el=>el.addEventListener('change',resetPending));
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    if(complete || btn.disabled) return;
    if(!form.reportValidity()) return;
    const file=fileEl.files[0], email=emailEl.value.trim(), members=membersEl.value.trim();
    if(members.length<3) {status('Indiquez les noms et prénoms des membres du binôme.',true);return;}
    const ext=(file.name.split('.').pop()||'').toLowerCase();
    if(!allowed.has(ext)) {status('Format non accepté : PDF, Word, ZIP ou RAR uniquement.',true);return;}
    if(file.size===0 || file.size>MAX) {status('Le fichier doit être non vide et ne pas dépasser 50 Mo.',true);return;}
    if(!pending) {
      const id=crypto.randomUUID();
      pending={id,path:'rendus/'+id+'/'+cleanName(file.name),uploaded:false};
    }
    const p=pending;
    btn.disabled=true;
    [emailEl,membersEl,fileEl].forEach(el=>el.disabled=true);
    btn.textContent='Envoi en cours…';
    status('Envoi du fichier. Gardez cette page ouverte jusqu’à la confirmation.');
    try {
      if(!p.uploaded) {
        const res=await fetch(URL+'/storage/v1/object/'+BUCKET+'/'+p.path,{method:'POST',headers:{...headers,'Content-Type':file.type||'application/octet-stream','x-upsert':'false'},body:file});
        if(!res.ok) {
          const detail=await res.json().catch(()=>({}));
          // A retry after a lost response reuses the same random path.
          if(res.status===409 || detail.error==='Duplicate' || detail.statusCode==='409') p.uploaded=true;
          else throw new Error('upload');
        } else p.uploaded=true;
      }
      status('Fichier reçu. Enregistrement du dépôt en cours…');
      const meta={id:p.id,email,group_members:members,original_filename:file.name,storage_path:p.path,mime_type:file.type||null,size_bytes:file.size};
      const res=await fetch(URL+'/rest/v1/'+TABLE,{method:'POST',headers:{...headers,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify(meta)});
      if(!res.ok) {
        const detail=await res.json().catch(()=>({}));
        // Same ID/path on retry: unique violation means the earlier insert succeeded.
        if(!(res.status===409 && detail.code==='23505')) throw new Error('metadata');
      }
      receipt={module:'Module 5 — Gouvernance, conformité et finance durable',evaluation:'Audit critique SolarOne',reference:p.id,confirmation_utc:new Date().toISOString(),binome:members,email_depot:email,fichier:file.name,taille_octets:file.size};
      complete=true;
      const receiptText=Object.entries(receipt).map(([key,value])=>key+' : '+value).join('\n');
      receiptBtn.href=window.URL.createObjectURL(new Blob([receiptText],{type:'text/plain;charset=utf-8'}));
      receiptBtn.download='Recu_Module5_'+receipt.reference+'.txt';
      status('Dépôt enregistré avec succès.\nRéférence : '+p.id+'\nFichier : '+file.name+'\nConservez le reçu : votre rapport et ses annexes ont été transmis pour correction.');
      receiptBtn.hidden=false;
      btn.textContent='Travail déposé';
    } catch(error) {
      console.error('Module5 submission failed at',p.uploaded?'metadata':'upload');
      status(p.uploaded ? 'Le fichier a été envoyé, mais la confirmation du dépôt n’a pas pu être obtenue. Référence : '+p.id+'. Gardez la page ouverte et cliquez à nouveau pour terminer l’enregistrement. Si le problème persiste, communiquez cette référence à l’enseignant.' : 'Le dépôt n’a pas pu être confirmé. Vérifiez la connexion puis réessayez sur cette page. Aucun succès n’est annoncé avant l’enregistrement complet.',true);
    } finally {
      if(!complete) {
        btn.disabled=false;btn.textContent=p.uploaded?'Terminer le dépôt':'Déposer mon travail';
        [emailEl,membersEl,fileEl].forEach(el=>el.disabled=false);
      }
    }
  });
})();
