create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  imported_payloads jsonb not null default '[]'::jsonb,
  progress jsonb not null default '{}'::jsonb,
  answers jsonb not null default '[]'::jsonb,
  reviews jsonb not null default '{}'::jsonb,
  last_situation_slug text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_touch_updated_at on public.profiles;
create trigger profiles_touch_updated_at
before update on public.profiles
for each row execute function public.touch_updated_at();

drop trigger if exists user_state_touch_updated_at on public.user_state;
create trigger user_state_touch_updated_at
before update on public.user_state
for each row execute function public.touch_updated_at();

alter table public.profiles enable row level security;
alter table public.user_state enable row level security;

drop policy if exists "Profiles are readable by their owner" on public.profiles;
create policy "Profiles are readable by their owner"
on public.profiles for select
to authenticated
using (auth.uid() = id);

drop policy if exists "Profiles are insertable by their owner" on public.profiles;
create policy "Profiles are insertable by their owner"
on public.profiles for insert
to authenticated
with check (auth.uid() = id);

drop policy if exists "Profiles are updatable by their owner" on public.profiles;
create policy "Profiles are updatable by their owner"
on public.profiles for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);

drop policy if exists "User state is readable by its owner" on public.user_state;
create policy "User state is readable by its owner"
on public.user_state for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "User state is insertable by its owner" on public.user_state;
create policy "User state is insertable by its owner"
on public.user_state for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "User state is updatable by its owner" on public.user_state;
create policy "User state is updatable by its owner"
on public.user_state for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    coalesce(
      nullif(new.raw_user_meta_data ->> 'display_name', ''),
      nullif(split_part(new.email, '@', 1), ''),
      'Utilisateur'
    )
  )
  on conflict (id) do nothing;

  insert into public.user_state (user_id)
  values (new.id)
  on conflict (user_id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_auth_user();

insert into public.profiles (id, display_name)
select
  users.id,
  coalesce(
    nullif(users.raw_user_meta_data ->> 'display_name', ''),
    nullif(split_part(users.email, '@', 1), ''),
    'Utilisateur'
  )
from auth.users
on conflict (id) do nothing;

insert into public.user_state (user_id)
select users.id
from auth.users
on conflict (user_id) do nothing;
