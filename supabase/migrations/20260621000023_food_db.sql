-- Banco de información de alimentos para el módulo Dieta (búsqueda + alta directa).
-- Macros POR 100 g (a diferencia de `foods`, que guarda porciones absolutas).
-- Filas curadas globales: user_id NULL (visibles para todos). Filas del usuario
-- (p. ej. cacheadas desde Open Food Facts): user_id = auth.uid().
-- Degradación total: si esta tabla no existe aún, el cliente cae a Open Food Facts.

create table public.food_db (
  id uuid primary key default gen_random_uuid(),
  user_id uuid default auth.uid() references auth.users(id) on delete cascade,  -- NULL = curado global
  name text not null,
  brand text,
  kcal_100 numeric(6,1) not null,
  protein_100 numeric(5,1) not null default 0,
  carbs_100 numeric(5,1) not null default 0,
  fat_100 numeric(5,1) not null default 0,
  source text not null default 'curado',     -- curado | off | propio
  off_code text,                              -- código de barras Open Food Facts (caché)
  created_at timestamptz not null default now()
);

create index idx_food_db_name on public.food_db (lower(name));
-- evita duplicados: nombres curados únicos globalmente; y por usuario en sus propias filas
create unique index uq_food_db_global_name on public.food_db (lower(name)) where user_id is null;
create unique index uq_food_db_user_name on public.food_db (user_id, lower(name)) where user_id is not null;

alter table public.food_db enable row level security;

-- lectura: filas globales (curadas) + las propias
create policy "read_global_or_own" on public.food_db
  for select using (user_id is null or auth.uid() = user_id);
-- escritura: solo filas propias (las curadas son de solo lectura para el cliente)
create policy "insert_own" on public.food_db
  for insert with check (auth.uid() = user_id);
create policy "update_own" on public.food_db
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "delete_own" on public.food_db
  for delete using (auth.uid() = user_id);

-- ---------- Siembra curada (es-MX / dieta de gym) · valores por 100 g ----------
-- user_id se omite → NULL (global, ya que la migración corre sin sesión).
insert into public.food_db (name, kcal_100, protein_100, carbs_100, fat_100) values
  -- Proteínas
  ('Pechuga de pollo a la plancha', 165, 31, 0, 3.6),
  ('Muslo de pollo cocido', 209, 26, 0, 11),
  ('Carne molida de res 90/10 cocida', 176, 26, 0, 8),
  ('Carne molida de res 80/20 cocida', 254, 26, 0, 17),
  ('Bistec de res asado', 217, 27, 0, 12),
  ('Lomo de cerdo cocido', 173, 27, 0, 7),
  ('Huevo entero', 143, 13, 1.1, 9.5),
  ('Clara de huevo', 52, 11, 0.7, 0.2),
  ('Atún en agua drenado', 116, 26, 0, 1),
  ('Salmón cocido', 206, 22, 0, 13),
  ('Tilapia cocida', 128, 26, 0, 2.7),
  ('Camarón cocido', 99, 24, 0.2, 0.3),
  ('Pavo molido cocido', 203, 27, 0, 10),
  ('Jamón de pavo', 104, 17, 3, 3),
  -- Lácteos
  ('Leche entera', 61, 3.2, 4.8, 3.3),
  ('Leche semidescremada (light)', 50, 3.4, 4.9, 1.8),
  ('Yogur griego natural', 59, 10, 3.6, 0.4),
  ('Queso panela', 215, 18, 3, 14),
  ('Queso Oaxaca', 350, 24, 3, 27),
  ('Queso fresco', 145, 12, 4, 9),
  ('Requesón', 130, 11, 3, 8),
  ('Queso cottage', 98, 11, 3.4, 4.3),
  -- Carbohidratos
  ('Arroz blanco cocido', 130, 2.7, 28, 0.3),
  ('Arroz integral cocido', 112, 2.6, 24, 0.9),
  ('Avena en hojuelas (seca)', 389, 17, 66, 7),
  ('Tortilla de maíz', 218, 5.7, 45, 2.8),
  ('Tortilla de harina', 304, 8, 51, 7),
  ('Pan integral', 247, 13, 41, 3.4),
  ('Pan blanco (bolillo)', 274, 9, 53, 3.3),
  ('Pasta cocida', 158, 5.8, 31, 0.9),
  ('Papa cocida', 87, 1.9, 20, 0.1),
  ('Camote cocido', 90, 2, 21, 0.1),
  ('Frijoles cocidos', 127, 9, 23, 0.5),
  ('Frijoles refritos', 145, 6, 18, 5),
  ('Lentejas cocidas', 116, 9, 20, 0.4),
  ('Elote (grano)', 96, 3.4, 21, 1.5),
  ('Quinoa cocida', 120, 4.4, 21, 1.9),
  ('Hojuelas de maíz (corn flakes)', 357, 7, 84, 0.9),
  ('Granola', 471, 10, 64, 20),
  ('Tostada horneada', 434, 9, 73, 12),
  -- Frutas
  ('Plátano', 89, 1.1, 23, 0.3),
  ('Manzana', 52, 0.3, 14, 0.2),
  ('Fresa', 32, 0.7, 7.7, 0.3),
  ('Mango', 60, 0.8, 15, 0.4),
  ('Papaya', 43, 0.5, 11, 0.3),
  ('Naranja', 47, 0.9, 12, 0.1),
  ('Uvas', 69, 0.7, 18, 0.2),
  ('Piña', 50, 0.5, 13, 0.1),
  ('Sandía', 30, 0.6, 8, 0.2),
  ('Melón', 34, 0.8, 8, 0.2),
  -- Verduras
  ('Brócoli', 34, 2.8, 7, 0.4),
  ('Espinaca', 23, 2.9, 3.6, 0.4),
  ('Jitomate', 18, 0.9, 3.9, 0.2),
  ('Nopal', 16, 1.3, 3.3, 0.1),
  ('Zanahoria', 41, 0.9, 10, 0.2),
  ('Calabacita', 17, 1.2, 3.1, 0.3),
  ('Lechuga', 15, 1.4, 2.9, 0.2),
  ('Pepino', 15, 0.7, 3.6, 0.1),
  ('Chayote', 19, 0.8, 4.5, 0.1),
  ('Champiñón', 22, 3.1, 3.3, 0.3),
  ('Cebolla', 40, 1.1, 9, 0.1),
  ('Pimiento morrón', 31, 1, 6, 0.3),
  -- Grasas y semillas
  ('Aguacate', 160, 2, 9, 15),
  ('Almendras', 579, 21, 22, 50),
  ('Cacahuate', 567, 26, 16, 49),
  ('Crema de cacahuate', 588, 25, 20, 50),
  ('Aceite de oliva', 884, 0, 0, 100),
  ('Nuez', 654, 15, 14, 65),
  ('Semilla de chía', 486, 17, 42, 31),
  ('Linaza', 534, 18, 29, 42),
  ('Mantequilla', 717, 0.9, 0.1, 81),
  ('Mayonesa', 680, 1, 0.6, 75),
  -- Suplementos y otros
  ('Proteína de suero (whey)', 380, 80, 8, 6),
  ('Miel', 304, 0.3, 82, 0),
  ('Azúcar', 387, 0, 100, 0),
  ('Chocolate amargo 70%', 598, 7.8, 46, 43),
  ('Galleta María', 436, 7, 78, 10),
  ('Catsup', 101, 1.3, 26, 0.2),
  ('Jugo de naranja', 45, 0.7, 10, 0.2),
  ('Refresco de cola', 42, 0, 11, 0);
