create table customers (id uuid primary key, email text);
alter table customers enable row level security;
create policy "open customers" on customers for select using (true);
