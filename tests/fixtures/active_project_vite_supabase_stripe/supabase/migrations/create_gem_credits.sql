create table public.gem_credit_costs (
  id uuid primary key,
  label text not null,
  credits integer not null
);

alter table public.gem_credit_costs enable row level security;

create policy "Allow read access"
on public.gem_credit_costs
for select
using (true);
