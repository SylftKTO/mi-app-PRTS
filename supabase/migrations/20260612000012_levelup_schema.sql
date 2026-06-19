-- Apartado LevelUp (academia de idiomas): maestros, alumnos, clases, pagos.
-- Mini-CRM/ERP. Dinero self-contained (no toca el módulo Finanzas personal).
-- Convención del repo: user_id default auth.uid(), RLS owner_all, TZ MX.

-- ---------- MAESTROS ----------
create table public.levelup_teachers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null,
  languages text[] not null default '{}',                 -- idiomas que imparte
  formats text[] not null default '{}',                   -- {grupal, particular}
  pay_type text not null default 'mensual' check (pay_type in ('mensual', 'por_hora')),
  pay_rate numeric(10,2) not null default 0,              -- sueldo mensual o tarifa por hora
  notes text,
  created_at timestamptz not null default now()
);

-- ---------- ALUMNOS ----------
create table public.levelup_students (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null,
  language text,                                           -- idioma planeado
  level text,                                              -- nivel planeado (A1…C2)
  hours_per_week numeric(4,1) not null default 0,
  teacher_id uuid references public.levelup_teachers(id) on delete set null,
  monthly_fee numeric(10,2) not null default 0,           -- cobro mensual
  status text not null default 'activo' check (status in ('activo', 'inactivo')),
  notes text,
  created_at timestamptz not null default now()
);

-- ---------- CLASES (recurrentes o sesiones sueltas) ----------
create table public.levelup_classes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  teacher_id uuid references public.levelup_teachers(id) on delete set null,
  title text not null,
  language text,
  level text,                                              -- tema o nivel de la clase
  format text not null default 'grupal' check (format in ('grupal', 'particular')),
  kind text not null default 'recurrente' check (kind in ('recurrente', 'sesion')),
  weekday int check (weekday between 0 and 6),             -- recurrente (getDay 0=dom)
  class_date date,                                         -- sesión puntual
  start_time time not null,
  duration_min int not null default 60,
  week_block_id uuid references public.week_blocks(id) on delete set null,  -- enlace a Semana
  google_event_id text,                                   -- enlace al evento GCal
  created_at timestamptz not null default now(),
  check ((kind = 'recurrente' and weekday is not null) or (kind = 'sesion' and class_date is not null))
);

-- ---------- ROSTER (alumnos por clase, para grupales) ----------
create table public.levelup_class_students (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  class_id uuid not null references public.levelup_classes(id) on delete cascade,
  student_id uuid not null references public.levelup_students(id) on delete cascade,
  primary key (class_id, student_id)
);

-- ---------- PAGOS MENSUALES ----------
create table public.levelup_payments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  student_id uuid not null references public.levelup_students(id) on delete cascade,
  period text not null,                                    -- "YYYY-MM"
  amount_due numeric(10,2) not null default 0,
  amount_paid numeric(10,2) not null default 0,
  paid_at date,
  created_at timestamptz not null default now(),
  unique (user_id, student_id, period)
);

create index idx_lu_students_teacher on public.levelup_students (user_id, teacher_id);
create index idx_lu_classes_teacher on public.levelup_classes (user_id, teacher_id);
create index idx_lu_payments_student on public.levelup_payments (user_id, student_id, period);

alter table public.levelup_teachers enable row level security;
alter table public.levelup_students enable row level security;
alter table public.levelup_classes enable row level security;
alter table public.levelup_class_students enable row level security;
alter table public.levelup_payments enable row level security;

create policy "owner_all" on public.levelup_teachers
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.levelup_students
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.levelup_classes
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.levelup_class_students
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.levelup_payments
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
