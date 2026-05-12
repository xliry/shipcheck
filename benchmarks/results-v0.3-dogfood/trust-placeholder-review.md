# ShipCheck v0.3 Dogfood: `trust.placeholder_copy` Manual Review

Review date: 2026-05-12

Source:

- `benchmarks/results-v0.3-dogfood/*.json`

## Summary

Manual review of the 15 `trust.placeholder_copy` findings shows a real precision bottleneck.

| Classification | Count | Read |
|---|---:|---|
| true positive | 5 | Real unfinished launch/template copy. |
| false positive | 10 | Code identifiers, type aliases, icon names, Tailwind placeholder classes, or normal UI type declarations. |

Precision in this dogfood slice: 5/15 = 33%.

This is now the clearest candidate for a narrow v0.4 rule-hardening task.

## Reviewed Findings

| Repo | File | Line | Classification | Evidence | Note |
|---|---|---:|---|---|---|
| `DanieII/instant-saas` | `components/home/FAQ.tsx` | 15 | true_positive | `Lorem ipsum dolor sit amet consectetur adipisicing elit.` | Real placeholder prose. |
| `DanieII/instant-saas` | `components/home/Features.tsx` | 25 | true_positive | `<p className=text-xl font-bold>Lorem ipsum dolor sit amet</p>` | Real placeholder prose. |
| `dzlau/stripe-supabase-saas-template` | `app/page.tsx` | 47 | true_positive | `<span className=sr-only>Acme Inc</span>` | Template company name in visible/a11y brand copy. |
| `dzlau/stripe-supabase-saas-template` | `app/subscribe/page.tsx` | 16 | true_positive | `<span className=sr-only>Acme Inc</span>` | Template company name in visible/a11y brand copy. |
| `nextjs/saas-starter` | `app/(dashboard)/layout.tsx` | 87 | true_positive | `<span className=ml-2 text-xl font-semibold text-gray-900>ACME</span>` | Template brand copy. |
| `nextjs/saas-starter` | `app/(login)/actions.ts` | 454 | false_positive | `// TODO: Send invitation email and include ?inviteId={id} to sign-up URL` | This is a code TODO, not launch-copy placeholder. Another rule could cover TODO comments, but not trust copy. |
| `nextjs/saas-starter` | `app/(login)/login.tsx` | 57 | false_positive | `placeholder-gray-500 ...` | Tailwind placeholder class slipped through. |
| `Razikus/supabase-nextjs-template` | `nextjs/src/app/app/table/page.tsx` | 25 | false_positive | `type Task = Database[public][Tables][todo_list][Row];` | `todo_list` schema/table identifier, not copy. |
| `Razikus/supabase-nextjs-template` | `nextjs/src/app/page.tsx` | 32 | false_positive | `description: Built-in todo system with real-time updates and priority management,` | Product/demo feature copy; not unfinished placeholder by itself. |
| `Razikus/supabase-nextjs-template` | `nextjs/src/components/AppLayout.tsx` | 12 | false_positive | `Key, Files, LucideListTodo,` | Icon import name. |
| `Razikus/supabase-nextjs-template` | `nextjs/src/components/HomePricing.tsx` | 17 | true_positive | `IT'S PLACEHOLDER NO PRICING FOR THIS TEMPLATE` | Explicit placeholder pricing copy. |
| `Razikus/supabase-nextjs-template` | `nextjs/src/lib/supabase/unified.ts` | 78 | false_positive | `async getMyTodoList(...)` | Function name and database concept, not copy. |
| `Razikus/supabase-nextjs-template` | `supabase-expo-template/app/(app)/_layout.tsx` | 4 | false_positive | `import { FolderOpen, Home, ListTodo, Settings } from lucide-react-native` | Icon import name. |
| `Razikus/supabase-nextjs-template` | `supabase-expo-template/app/(app)/tasks.tsx` | 14 | false_positive | `type Task = Database[public][Tables][todo_list][Row]` | Type alias/schema reference. |
| `Razikus/supabase-nextjs-template` | `supabase-expo-template/components/ui/input.tsx` | 9 | false_positive | `placeholder?: string` | Component prop type declaration. |

## Pattern Diagnosis

Keep detecting:

- `Lorem ipsum`
- obvious template company names in rendered brand copy: `Acme`, `ACME`, `Acme Inc`
- explicit placeholder text in visible pricing/marketing copy
- fake testimonials / fake customer names in rendered UI

Stop detecting as `trust.placeholder_copy`:

- TypeScript prop declarations such as `placeholder?: string`
- Tailwind classes such as `placeholder-gray-500`, `placeholder:text-muted-foreground`
- table/type/function identifiers containing `todo`, e.g. `todo_list`, `getMyTodoList`, `LucideListTodo`
- import statements
- code comments containing TODO unless a separate code-quality rule is intentionally added
- generic demo feature copy mentioning a todo system

## Recommendation

Create a narrow ShipCheck v0.4 spec for trust placeholder precision.

Scope should be limited to:

1. classify visible/rendered copy vs code identifiers/imports/types/comments
2. tighten `todo` matching so it does not hit schema/function/icon names
3. catch Tailwind placeholder utility variants missed by v0.2
4. keep `Lorem ipsum`, `Acme`, explicit placeholder pricing, and fake testimonial signals
5. rerun only the 5-repo dogfood set plus existing tests before deciding whether to rerun the full 8-target benchmark

Do not add an LLM or broad copywriting analyzer.

