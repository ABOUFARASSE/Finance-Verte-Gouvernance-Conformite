-- Module 10, nouvelle version 4 x 3 h. API réservée au serveur.
create table public.m10v2_settings (
 id integer primary key check (id=1), admin_hash text not null, is_open boolean not null default true
);
create table public.m10v2_access (
 id uuid primary key default gen_random_uuid(), label text not null unique,
 key_hash text not null unique, student_name text, enabled boolean not null default true,
 created_at timestamptz not null default now()
);
create table public.m10v2_questions (
 id text primary key, session integer not null check(session between 1 and 4),
 difficulty text not null default 'simple' check(difficulty in ('simple','comprehension')),
 question text not null, options jsonb not null check(jsonb_array_length(options)=4),
 correct integer not null check(correct between 0 and 3), explanation text not null, source text not null
);
create table public.m10v2_attempts (
 id uuid primary key default gen_random_uuid(), access_id uuid not null references public.m10v2_access(id),
 number integer not null check(number between 1 and 3), items jsonb not null check(jsonb_array_length(items)=20),
 answers jsonb not null default '{}'::jsonb, score integer check(score between 0 and 20),
 started_at timestamptz not null default now(), submitted_at timestamptz,
 unique(access_id,number), check((score is null)=(submitted_at is null))
);
create unique index m10v2_one_open on public.m10v2_attempts(access_id) where submitted_at is null;
alter table public.m10v2_settings enable row level security;
alter table public.m10v2_access enable row level security;
alter table public.m10v2_questions enable row level security;
alter table public.m10v2_attempts enable row level security;
revoke all on public.m10v2_settings,public.m10v2_access,public.m10v2_questions,public.m10v2_attempts from public,anon,authenticated;
grant select,insert,update,delete on public.m10v2_settings,public.m10v2_access,public.m10v2_questions,public.m10v2_attempts to service_role;

CREATE OR REPLACE FUNCTION public.m10v2_api(p_action text, p_key_hash text, p_payload jsonb DEFAULT '{}'::jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare a public.m10v2_access; t public.m10v2_attempts; cfg public.m10v2_settings;
 n integer; b integer; items jsonb; hist jsonb; cur jsonb; ans jsonb; corrections jsonb;
begin
 select * into cfg from public.m10v2_settings where id=1;
 if p_action in ('admin','toggle') then
  if p_key_hash is distinct from cfg.admin_hash then raise exception 'Accès refusé'; end if;
  if p_action='toggle' then
   if jsonb_typeof(p_payload->'open') is distinct from 'boolean' then raise exception 'Paramètre invalide'; end if;
   update public.m10v2_settings set is_open=(p_payload->>'open')::boolean where id=1;
   return jsonb_build_object('open',(p_payload->>'open')::boolean);
  end if;
  return jsonb_build_object('open',cfg.is_open,'students',coalesce((select jsonb_agg(r order by r.label) from (
   select x.label,x.student_name,count(y.id)::int as started,
    count(y.submitted_at)::int as validated,max(y.score) as best,
    coalesce(jsonb_agg(jsonb_build_object('number',y.number,'score',y.score,'started_at',y.started_at,'submitted_at',y.submitted_at) order by y.number) filter(where y.id is not null),'[]'::jsonb) as attempts
   from public.m10v2_access x left join public.m10v2_attempts y on y.access_id=x.id
   group by x.id
  )r),'[]'::jsonb));
 end if;
 select * into a from public.m10v2_access where key_hash=p_key_hash and enabled for update;
 if not found then raise exception 'Code individuel invalide ou désactivé'; end if;
 if p_action='start' then
  select * into t from public.m10v2_attempts where access_id=a.id and submitted_at is null;
  if not found then
   if not cfg.is_open then raise exception 'Les nouvelles tentatives sont fermées'; end if;
   select count(*) into n from public.m10v2_attempts where access_id=a.id;
   if n>=3 then raise exception 'Trois tentatives déjà utilisées'; end if;
   if a.student_name is null then
    if length(trim(coalesce(p_payload->>'name',''))) not between 2 and 100 then raise exception 'Indiquez votre nom complet (2 à 100 caractères)'; end if;
    update public.m10v2_access set student_name=trim(p_payload->>'name') where id=a.id returning * into a;
   end if;
   if (select count(*) from public.m10v2_questions)<>100 then raise exception 'Banque en préparation'; end if;
   if exists(select 1 from generate_series(1,4) s(v) where
     (select count(*) from public.m10v2_questions where session=s.v and difficulty='simple')<>20 or
     (select count(*) from public.m10v2_questions where session=s.v and difficulty='comprehension')<>5)
    then raise exception 'Répartition de la banque en préparation'; end if;
   select jsonb_agg(to_jsonb(q)||jsonb_build_object('options',sh.opts,'correct',sh.answer)
      order by case q.difficulty when 'simple' then 0 else 1 end,random())
    into items from generate_series(1,4) as s(v)
    cross join (values ('simple'::text,4),('comprehension'::text,1)) as levels(difficulty,quota)
    cross join lateral (
      select z.* from public.m10v2_questions z
      where z.session=s.v and z.difficulty=levels.difficulty
      order by random() limit levels.quota
    )q
    cross join lateral (
      select jsonb_agg(v order by newpos) as opts,
        max(newpos-1) filter(where oldpos-1=q.correct)::integer as answer
      from (
        select v,ord as oldpos,row_number() over(order by random()) as newpos
        from jsonb_array_elements(q.options) with ordinality as a(v,ord)
      ) shuffled
    )sh;
   insert into public.m10v2_attempts(access_id,number,items) values(a.id,n+1,items) returning * into t;
  end if;
 elsif p_action in ('save','submit','review') then
  select * into t from public.m10v2_attempts where id=(p_payload->>'attempt')::uuid and access_id=a.id for update;
  if not found then raise exception 'Tentative introuvable'; end if;
  if p_action in ('save','submit') and t.submitted_at is null then
   ans:=p_payload->'answers';
   if jsonb_typeof(ans) is distinct from 'object' then raise exception 'Réponses invalides'; end if;
   if exists(select 1 from jsonb_each(ans) e where jsonb_typeof(e.value)<>'number' or e.value::text not in ('0','1','2','3') or not exists(select 1 from jsonb_array_elements(t.items) q where q->>'id'=e.key)) then raise exception 'Réponse hors périmètre'; end if;
   update public.m10v2_attempts set answers=ans where id=t.id returning * into t;
   if p_action='submit' then
    select count(*) into n from jsonb_array_elements(t.items) q where (t.answers->>(q->>'id'))=(q->>'correct');
    update public.m10v2_attempts set score=n,submitted_at=now() where id=t.id returning * into t;
   end if;
  end if;
  if p_action='review' and t.submitted_at is null then raise exception 'Le corrigé sera disponible après validation'; end if;
  if p_action='submit' or p_action='review' then
   select jsonb_agg(q||jsonb_build_object('selected',t.answers->(q->>'id'),'is_correct',(t.answers->>(q->>'id'))=(q->>'correct')) order by ord) into corrections from jsonb_array_elements(t.items) with ordinality as x(q,ord);
   select max(score) into b from public.m10v2_attempts where access_id=a.id;
   return jsonb_build_object('attempt',t.id,'number',t.number,'score',t.score,'best',b,'submitted_at',t.submitted_at,'corrections',corrections);
  end if;
 elsif p_action<>'status' then raise exception 'Action inconnue';
 end if;
 select count(*),max(score) into n,b from public.m10v2_attempts where access_id=a.id;
 select coalesce(jsonb_agg(jsonb_build_object('id',id,'number',number,'score',score,'submitted_at',submitted_at) order by number),'[]'::jsonb) into hist from public.m10v2_attempts where access_id=a.id;
 select jsonb_build_object('id',u.id,'number',u.number,'answers',u.answers,'questions',(select jsonb_agg(q-'correct'-'explanation' order by ord) from jsonb_array_elements(u.items) with ordinality as x(q,ord))) into cur from public.m10v2_attempts u where access_id=a.id and submitted_at is null;
 return jsonb_build_object('name',a.student_name,'label',a.label,'open',cfg.is_open,'started',n,'remaining',3-n,'best',b,'history',hist,'current',cur);
end;$function$

;
revoke all on function public.m10v2_api(text,text,jsonb) from public,anon,authenticated;
grant execute on function public.m10v2_api(text,text,jsonb) to service_role;

