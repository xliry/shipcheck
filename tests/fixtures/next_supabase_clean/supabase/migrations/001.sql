create table customers (id uuid primary key, user_id uuid not null, email text);
alter table customers enable row level security;
create policy "own customers" on customers for select using (auth.uid() = user_id);
