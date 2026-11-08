// Only the edge handler holds the service credential. Students use individual random codes.
const cors={"Access-Control-Allow-Origin":"https://aboufarasse.github.io","Access-Control-Allow-Headers":"content-type,apikey","Access-Control-Allow-Methods":"POST,OPTIONS","Vary":"Origin"};
const headers={...cors,"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"};
Deno.serve(async(req:Request)=>{
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers:cors});
 if(req.method!=='POST')return new Response(JSON.stringify({error:'Méthode non autorisée'}),{status:405,headers});
 const origin=req.headers.get('Origin');
 if(origin && origin!=='https://aboufarasse.github.io')return new Response(JSON.stringify({error:'Origine non autorisée'}),{status:403,headers});
 try{
  const raw=await req.text();if(raw.length>12000)throw Error('Requête trop longue');
  const b=JSON.parse(raw);
  if(typeof b.key!=='string'||b.key.length<16||b.key.length>160)throw Error('Code individuel requis');
  if(!['status','start','save','submit','review','admin','toggle'].includes(b.action))throw Error('Action inconnue');
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(b.key.trim().toUpperCase()));
  const hash=Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,'0')).join('');
  const secret=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  const response=await fetch(Deno.env.get('SUPABASE_URL')+'/rest/v1/rpc/m10v2_api',{
   method:'POST',headers:{'apikey':secret,'Authorization':'Bearer '+secret,'Content-Type':'application/json'},
   body:JSON.stringify({p_action:b.action,p_key_hash:hash,p_payload:b.payload||{}})
  });
  const result=await response.json();
  if(!response.ok){const msg=result.code==='P0001'?result.message:'Impossible de traiter cette demande. Réessayez ou contactez l’enseignant.';return new Response(JSON.stringify({error:msg}),{status:400,headers});}
  return new Response(JSON.stringify(result),{headers});
 }catch(e){return new Response(JSON.stringify({error:e instanceof SyntaxError?'Requête invalide':e.message||'Erreur de traitement'}),{status:400,headers});}
});
