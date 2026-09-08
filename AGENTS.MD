AGENTS.md

1. Project Identity

Project name: Finance Copilot
Type: Personal finance management web application / future SaaS
Primary goal: Build an extremely user-friendly personal finance platform that helps users understand, control, and improve their finances with minimal manual work.

This project is being built as part of the Laboratório de Programação Full Stack discipline and must respect the academic stack and scope while still being designed as a serious real-world product that can continue evolving after the course.

The product should feel like a financial assistant, not like an ERP, accounting suite, spreadsheet, or administrative system.

The core product promise is:

“Understand your money without having to spend your life feeding a finance app.”

The user should be able to open the application and quickly understand:

how much money came in;

how much went out;

how much is still available;

where the money went;

whether they are on track with their budgets;

what recurring expenses exist;

what is likely to happen by the end of the month;

what actions could improve their financial situation.

2. Academic Constraints — MUST FOLLOW

The course stack is intentionally based on:

Backend: Python + Django

Database: PostgreSQL

Frontend: Django Templates + HTML + CSS + JavaScript

ORM: Django ORM

Future API layer: Django REST Framework (DRF)

Do not replace the main frontend with:

React

Next.js

Vue

Angular

Svelte

SPA frameworks

Do not split the project into a separate frontend and backend application unless explicitly requested later.

The project must remain a Django-first MPA, where Django renders HTML server-side using templates.

The academic project chosen is Controle Financeiro.

The required academic entities are:

Conta

Categoria

Lançamento

Orçamento

Parcela

The required P1 scope is:

CRUD

budget by category/month

automatic installment generation

The expected later P2 evolution includes:

multiple financial spaces

user roles

dashboard

REST API using Django REST Framework

Any extra feature must complement, not replace, these requirements.

3. Product Vision

Build a personal finance application that is:

extremely simple;

visually calm;

fast;

intelligent;

proactive;

understandable by non-technical users;

useful without requiring complex setup;

useful from the first session;

capable of becoming a SaaS later.

The interface must hide unnecessary accounting terminology.

Prefer:

“Gastos”

“Entradas”

“Contas”

“Planejamento”

“Quanto ainda posso gastar”

“Você está acima do seu normal”

Avoid when unnecessary:

“Débito”

“Crédito contábil”

“Livro razão”

“Plano de contas”

“Centro de custo”

The experience should resemble a modern consumer product, not enterprise software.

4. UX Principles

4.1 Zero-friction philosophy

Every important action should require as few decisions as possible.

Examples:

Bad:

Click “Lançamentos”

Click “Novo”

Select type

Select category

Select account

Select date

Enter description

Enter value

Save

Better:

Click +

Type 42,90 iFood

System infers:

expense

R$ 42,90

category: Alimentação

date: today

most recently used account

User confirms

The system should automate defaults and ask only when uncertain.

4.2 Progressive disclosure

Do not show all financial complexity immediately.

Basic users should see simple screens.

Advanced controls may exist under:

“Mais opções”

contextual menus

settings

expandable sections

4.3 Explain numbers in human language

Charts must never exist without interpretation.

Bad:

Pie chart: 37% alimentação.

Good:

“Alimentação foi sua maior categoria neste mês: R$ 1.180, 18% acima da sua média dos últimos 3 meses.”

4.4 Primary navigation

Keep the main navigation minimal.

Recommended:

Início

Movimentações

Planejamento

Metas

Conta / Perfil

Avoid creating 10+ top-level menu items.

Secondary features should live inside these sections.

5. Main User Journey

5.1 First access

The onboarding should take approximately 2 minutes.

Ask only:

First name

Monthly income estimate

Main financial objective

Whether the user wants:

personal control

household/family control

Main account name

Optional opening balance

Example objectives:

Organizar meus gastos

Economizar mais

Sair das dívidas

Criar reserva de emergência

Juntar dinheiro para uma meta

Do not force users to fully configure categories before seeing the dashboard.

5.2 First dashboard

Immediately show a useful empty-state dashboard.

Example:

Olá, João 👋
Vamos organizar sua vida financeira.

Cards:

Entradas este mês

Gastos este mês

Saldo disponível

Orçamento usado

CTA:

Adicionar primeiro gasto

Importar extrato

6. Dashboard

The dashboard must prioritize clarity.

Main cards

Available balance

Current calculated balance.

Income this month

Sum of income transactions.

Expenses this month

Sum of expense transactions.

Estimated month-end balance

Projection based on:

current balance

recurring expenses

installments

average spending pace

Daily safe-to-spend amount

Calculate:

available_budget / remaining_days

Present as:

“Você pode gastar aproximadamente R$ 74 por dia até o fim do mês sem ultrapassar seus limites atuais.”

7. Transactions

Entity: Transaction / Django model Lancamento

Fields should include:

id

user

financial_space

account

category

type

INCOME

EXPENSE

TRANSFER

description

amount

date

notes

source

MANUAL

CSV

OFX

RECEIPT

API

recurring flag

installment_group

created_at

updated_at

Use DecimalField, never float, for money.

All money calculations must use Decimal.

8. Quick Add

Create a globally available + action.

Allow natural shorthand:

42 iFood

mercado 153.20

salario 4500

uber 21 ontem

notebook 3000 10x

The first implementation may use deterministic parsing.

No paid AI dependency is required.

Examples:

notebook 3000 10x

Should propose:

Expense

R$ 3,000

Electronics / Shopping category

10 installments

R$ 300 each

The user must confirm before saving.

9. Categories

Academic entity: Categoria

Default categories:

Income

Salário

Freelance

Rendimentos

Reembolso

Outros

Expenses

Alimentação

Mercado

Moradia

Transporte

Saúde

Educação

Lazer

Compras

Assinaturas

Contas

Viagem

Dívidas

Outros

Users may:

rename custom categories;

create new categories;

disable unused categories.

Do not let users delete categories that contain transactions without migration/reassignment.

10. Accounts

Academic entity: Conta

Examples:

Conta corrente

Carteira

Poupança

Cartão

Conta digital

Fields:

id

financial_space

name

type

institution

opening_balance

active

created_at

updated_at

Balance should preferably be derived from transaction history rather than manually mutated whenever practical.

11. Budgets

Academic entity: Orcamento

Core requirement:
Budget by category and month.

Fields:

financial_space

category

month

year

limit_amount

alert_threshold

created_at

updated_at

Rules:

only one active budget per category/month/space;

calculate amount used;

calculate percentage used;

show remaining amount;

warn at:

75%

90%

100%

Messages:

“Você já usou 82% do orçamento de Alimentação.”

“Restam R$ 214 para Alimentação neste mês.”

12. Installments

Academic entity: Parcela

When creating an installment purchase:

create a logical installment group;

create all installments automatically;

calculate due dates;

preserve relation to original transaction.

Example:

Purchase:

Notebook

R$ 3,000

10 installments

first installment: 08/09/2026

Result:

10 installments

R$ 300 each

monthly dates

Handle rounding safely.

If total does not divide exactly:

distribute rounding difference into the last installment.

13. Recurring Expenses

Extra feature.

Allow:

monthly

weekly

yearly

Examples:

Netflix

rent

gym

internet

Do not blindly create infinite future transactions.

Recommended architecture:

recurrence rule

generator/service

materialize only a bounded future window

14. Goals

Extra product feature.

Example:

“Quero juntar R$ 15.000 até dezembro de 2027.”

Fields:

title

target_amount

current_amount

target_date

priority

active

Show:

% complete

required monthly contribution

projected completion date

Example insight:

“Mantendo R$ 750 por mês, você alcança sua meta em novembro de 2027.”

15. Statement Import

This is one of the strongest product differentiators.

Support eventually:

CSV

OFX

Architecture:

imports/

parsers

normalizers

deduplicators

classifiers

Workflow:

Upload file

Parse rows

Normalize dates and values

Detect possible duplicates

Guess categories

Show preview

User reviews exceptions

Confirm import

Save transactions

Never save imported transactions before confirmation.

16. Automatic Categorization

Initial approach must be deterministic and explainable.

Rules:

IFOOD -> Alimentação
UBER -> Transporte
99APP -> Transporte
NETFLIX -> Assinaturas
SPOTIFY -> Assinaturas
POSTO -> Transporte
SUPERMERCADO -> Mercado
DROGARIA -> Saúde

Create model:

MerchantCategoryRule

Fields:

financial_space or user

normalized_pattern

category

confidence

source

created_at

If user manually corrects a category:

optionally create/update a personalized rule.

17. Receipt Import

Optional later feature.

Goal:
User uploads a receipt image.

System attempts to extract:

merchant

date

total

items (if possible)

The product must always show a confirmation screen.

Never silently trust OCR.

18. Economic Data Integrations

Use free/public APIs only when they genuinely improve the product.

Possible integration:

Banco Central do Brasil

exchange rates

Selic

IPCA

Create integrations behind interfaces/services.

Example:

services/economic_data.py

Never call external APIs directly inside templates or models.

Use:

timeout

error handling

cache

graceful fallback

The application must remain usable when third-party APIs are down.

19. Financial Insights

Insights should be generated from deterministic calculations first.

Examples:

“Você gastou 18% mais com alimentação que no mês passado.”

“Seu gasto com delivery aumentou por 3 meses seguidos.”

“Assinaturas representam R$ 214/mês.”

“Mantendo este ritmo, seu orçamento de lazer acaba em 8 dias.”

“Você tem R$ 630 em parcelas previstas para o próximo mês.”

Create a service layer:

finance/services/insights.py

Views must not contain complex financial calculations.

20. Forecasting

Implement simple, explainable projections.

Do not use opaque AI models for core financial calculations.

Possible forecast:

projected_expense =
current_expense
+ average_daily_variable_expense * remaining_days
+ scheduled_fixed_expenses
+ pending_installments

Always communicate that it is an estimate.

21. Financial Spaces — P2

Support future multi-space architecture from the beginning.

Examples:

Pessoal

Casa

Casal

Família

Model:

FinancialSpace

Fields:

name

owner

currency

created_at

All core financial entities should belong to a space.

Even if P1 exposes only one personal space, design database relationships so P2 does not require rewriting the whole schema.

22. Roles — P2

Future roles:

OWNER

ADMIN

MEMBER

VIEWER

Examples:

Owner may delete space

Admin manages financial records

Member creates/edits records

Viewer only reads

Implement authorization centrally.

Never rely solely on hiding buttons.

Views must enforce permission checks server-side.

23. Django Architecture

Prefer a clean modular monolith.

Recommended structure:

project/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── finance/
│   ├── budgets/
│   ├── goals/
│   ├── imports/
│   ├── insights/
│   └── core/
│
├── templates/
│   ├── base.html
│   ├── components/
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── tests/
├── requirements/
├── .env.example
├── .gitignore
├── README.md
└── AGENTS.md

Do not create dozens of tiny Django apps without clear boundaries.

24. Django Responsibility Boundaries

Models

Contain:

data structure;

simple invariants;

relationships.

Avoid giant models with all business logic.

Views

Views should orchestrate requests.

Avoid:

large business calculations;

parsing logic;

complex financial algorithms.

Services

Use services for:

installment creation;

imports;

categorization;

projections;

insights;

external APIs;

budget calculations.

Forms

Use Django Forms / ModelForms for validation.

Templates

Presentation only.

Avoid financial business rules in templates.

25. Frontend Requirements

Use:

semantic HTML

modern CSS

lightweight vanilla JavaScript

Django Templates

Avoid unnecessary frontend dependencies.

The UI must work well on:

mobile

tablet

desktop

Mobile-first is preferred.

26. Visual Design

Style goals:

premium but simple;

calm;

modern fintech;

generous spacing;

minimal visual noise;

readable typography;

soft shadows;

rounded cards;

consistent spacing;

strong accessibility.

Avoid:

excessive gradients;

neon effects;

clutter;

too many charts;

excessive icons;

tiny text;

dense tables on the home page.

Use cards only when they improve scanning.

27. Dashboard Layout

Desktop:

-------------------------------------------------
Top navigation
-------------------------------------------------

Hello + month selector

[ Available ]
[ Income ]
[ Expenses ]
[ Safe/day ]

-----------------------------------
Main insight
-----------------------------------

Budget progress
-----------------------------------

Spending categories
-----------------------------------

Recent transactions
-----------------------------------

Mobile:
stack everything vertically.

28. Design System

Create CSS tokens.

Example:

:root {
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  --font-sm: 0.875rem;
  --font-base: 1rem;
  --font-lg: 1.25rem;
  --font-xl: 1.75rem;
}

Do not scatter arbitrary numbers everywhere.

29. Accessibility

Must include:

semantic HTML

labels for inputs

visible focus states

keyboard navigation

ARIA only when necessary

sufficient color contrast

form error summaries where appropriate

Never rely only on color to represent financial state.

30. Forms

Forms should:

have clear labels;

show errors close to fields;

preserve input after validation error;

use sensible defaults;

minimize required fields.

Example transaction form basic fields:

description

amount

category

account

date

Advanced:

notes

recurring

installment

tags

31. Security

Mandatory:

no secrets committed;

.env;

python-dotenv;

.env in .gitignore;

.env.example without real values;

CSRF protection;

Django authentication;

secure cookies in production;

DEBUG=False in production;

input validation;

permission checks;

ORM instead of raw SQL unless justified.

Never log:

passwords;

tokens;

sensitive financial content unnecessarily.

32. Authentication

Use Django authentication.

Initial:

signup

login

logout

password reset

Later:

email verification

optional OAuth

Do not build custom password storage.

33. PostgreSQL

Use PostgreSQL as the primary database.

Use migrations for every schema change.

Always:

python manage.py makemigrations
python manage.py migrate

Never manually edit database schema to bypass migrations.

34. Money Handling

Critical rule:

Never use float for money.

Use:

Decimal
models.DecimalField(...)

Always define:

max_digits

decimal_places

Example:

amount = models.DecimalField(
    max_digits=14,
    decimal_places=2
)

35. Dates and Timezones

Use Django timezone utilities.

Do not use naive datetime.now().

Prefer:

from django.utils import timezone

Financial date and transaction posting date may be separate concepts later.

36. Data Integrity

Use:

foreign key constraints

database constraints

unique constraints

transactions where required

Examples:

Prevent duplicate monthly budget:

financial_space + category + year + month

Installment creation should be atomic.

Imports should be atomic when confirmed.

37. Testing

Tests are mandatory.

Use Django TestCase / pytest if configured intentionally.

Test categories:

Model tests

validations

relationships

constraints

Service tests

installment generation

budget math

categorization

forecast

duplicate detection

View tests

authentication

permissions

form validation

redirects

Integration tests

CSV import

OFX import

external API adapters

38. Critical Test Cases

Installments:

2 installments

10 installments

rounding

month transitions

year transitions

Budgets:

zero transactions

exactly 100%

over 100%

missing category budget

Transactions:

negative values

zero values

large decimals

transfers

Imports:

duplicate row

malformed CSV

unknown encoding

invalid date

decimal comma

39. Performance

Use:

select_related

prefetch_related
where appropriate.

Avoid N+1 queries.

Do not prematurely optimize.

Use Django Debug Toolbar only in development if added.

40. API — P2

Use Django REST Framework.

Suggested endpoints:

/api/v1/accounts/
/api/v1/categories/
/api/v1/transactions/
/api/v1/budgets/
/api/v1/goals/
/api/v1/insights/

API requirements:

authentication

permissions

pagination

serializers

validation

versioning

Never expose another user's financial data.

41. Error Handling

User-facing messages must be friendly.

Bad:

IntegrityError

Good:

“Já existe um orçamento para Alimentação neste mês.”

Log technical detail server-side.

42. Empty States

Every empty screen must guide the user.

Example:

No transactions:

“Ainda não há movimentações neste mês.”

Buttons:

Adicionar gasto

Importar extrato

Do not show blank tables.

43. Loading and Feedback

Every action should produce feedback.

Examples:

toast after successful save

inline validation errors

disabled submit during request

progress indicator for imports

Avoid silent failures.

44. Product Copy

Tone:

direct

supportive

neutral

non-judgmental

Avoid:

“Você gastou demais!”

Prefer:

“Seus gastos com lazer ficaram 24% acima da sua média.”

Never shame the user.

45. Privacy

Financial data is sensitive.

Principles:

collect only necessary data;

isolate users;

do not expose transaction data in URLs;

do not print sensitive data in logs;

prepare architecture for data export/deletion later.

46. Developer Experience

Provide:

git clone ...
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

README must be enough for another student/developer to run the project.

47. Environment Variables

.env.example should contain:

DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_HOST=localhost
DATABASE_PORT=5432

Do not put actual credentials in .env.example.

48. Git Rules — STRICT

Codex must never create commits in this repository.

Codex must not execute or attempt:

git commit
git push
git merge
git rebase
git tag
git cherry-pick
git reset --hard

Codex may inspect Git state when useful, for example:

git status
git diff
git log

Codex may edit files in the working tree, but all commit, push, merge, branch-history, tag, and remote-publication decisions belong exclusively to the human developer.

At the end of a task, Codex may summarize:

which files changed;

what was implemented;

relevant tests executed;

any remaining issues.

It must not create a commit, even if the implementation is complete, even if another instruction says to commit, and even if committing appears to be a normal final step.

The working tree must be left for the human developer to review.

Never stage files automatically unless the user explicitly requests staging in that specific conversation.

Never push anything to any remote.

Never publish code or repository contents externally.

Do not add real secrets or sensitive local files to the repository, including:

.env

virtual environments

database dumps

credentials

tokens

IDE caches

generated secret files

48.1 Code Comment Policy — ZERO COMMENTS

Production code in this repository must be 100% free of explanatory comments.

Do not add:

Python # comments

JavaScript // comments

JavaScript/CSS /* comments */

HTML <!-- comments -->

SQL comments

TODO comments

FIXME comments

explanatory notes inside source files

comments describing what the next line does

section-divider comments

generated comments

comments explaining obvious framework behavior

comments narrating implementation decisions

Do not leave comments such as:

# Get all transactions
# Calculate total
# Validate user input
# Create installments
// Toggle menu
/* Dashboard styles */
<!-- Transaction form -->

Do not use comments as a substitute for clear naming.

Code must explain itself through:

precise names;

small functions;

coherent modules;

obvious control flow;

appropriate abstractions.

Avoid comments that make the repository look tutorial-like, generated, or mechanically explained.

Docstrings

Do not add explanatory docstrings to ordinary application code.

Avoid module, class, method, and function docstrings unless a framework, protocol, public API contract, or external tooling genuinely requires one.

Do not add docstrings merely to describe obvious behavior.

Tests should also remain free of explanatory comments and unnecessary docstrings.

Existing comments

Do not perform large unrelated rewrites solely to remove third-party, generated, migration, vendored, or framework-required comments.

For code authored or materially rewritten by Codex, leave no unnecessary comments.

If an existing first-party comment becomes obsolete while editing the surrounding code, remove it.

48.2 Natural Code Style — NO "AI-GENERATED" FEEL

The repository should read like code written and maintained by a competent human developer.

Avoid recognizable generated-code patterns such as:

excessive abstractions for simple problems;

needless helper classes;

verbose naming that repeats context already provided by the module;

giant files created in one pass;

boilerplate wrappers with no real purpose;

repetitive validation layers;

unnecessary defensive checks for impossible states;

generic names such as process_data, handle_item, or do_operation;

duplicated patterns that should naturally be reused;

functions that exist only to make the architecture look sophisticated;

excessive logging;

tutorial-style code organization;

placeholder architecture for hypothetical future needs;

unnecessary type complexity;

comments or prose that narrate obvious code.

Prefer:

idiomatic Django;

ordinary Python conventions;

concise implementations;

specific domain names;

local solutions before abstractions;

abstractions only after a real duplication or boundary exists;

framework defaults when they are sufficient;

readable code over clever code;

code that matches the style already present in the repository.

Do not add phrases, identifiers, strings, fixtures, documentation, or metadata referring to:

AI

ChatGPT

Codex

generated code

language models

an assistant

unless the product itself genuinely requires such terminology.

Do not add attribution such as "generated by", "created by AI", or similar text anywhere in the source tree.

49. Implementation Order

Codex should implement in this order unless an existing repo requires adaptation.

Phase 0 — Bootstrap

inspect repository

preserve existing code

create/verify Django project

configure PostgreSQL

configure environment variables

configure templates/static

create base layout

Phase 1 — Authentication

signup

login

logout

protected pages

Phase 2 — Core finance

FinancialSpace

Account

Category

Transaction

migrations

admin

forms

CRUD

Phase 3 — Budgets

monthly category budget

progress

warnings

Phase 4 — Installments

installment group

automatic generation

UI

Phase 5 — Dashboard

summary cards

recent transactions

category spending

safe-to-spend

month selector

Phase 6 — UX polish

quick add

empty states

responsive design

validation

accessibility

Phase 7 — Product extras

recurring expenses

goals

CSV/OFX import

automatic categorization

insights

Phase 8 — P2 architecture

multi-space roles

DRF API

advanced dashboard

50. Definition of Done

A feature is not complete until:

implementation works;

database migration exists if needed;

validation exists;

permissions are enforced;

error states are handled;

responsive UI is acceptable;

tests cover core behavior;

README is updated if setup changed;

no secrets are committed.

51. Codex Working Rules

When Codex works on this repository:

Inspect existing files before changing architecture.

Do not rewrite working code unnecessarily.

Prefer small, coherent changes.

Preserve Django conventions.

Keep business logic out of templates.

Keep complex logic out of views.

Use service functions/modules.

Use Django ORM.

Use PostgreSQL-compatible features.

Use migrations.

Use Decimal.

Write tests.

Do not introduce React or another frontend framework.

Do not introduce paid APIs.

Do not add dependencies without clear benefit.

Do not expose secrets.

Do not invent academic requirements.

Keep the mandatory academic entities and P1 scope intact.

Extra product features must remain optional layers over the required project.

Prefer maintainable code over clever code.

Never create a Git commit.

Never push to a remote.

Do not add explanatory comments to code.

Do not add unnecessary docstrings.

Keep authored code natural, concise, idiomatic, and consistent with the repository.

Do not add AI attribution, generated-code markers, or assistant-related wording.

52. Initial Codex Mission

After reading this file, Codex should:

inspect the current repository;

summarize the existing project structure;

identify what already exists;

propose the minimal implementation plan;

build the application incrementally;

keep the project runnable after each meaningful step;

avoid creating placeholders that are never wired into the product;

ensure the first usable milestone includes:

authentication;

accounts;

categories;

transactions;

monthly budgets;

automatic installments;

usable dashboard;

polished responsive interface.

53. Product Success Criteria

The product is successful when a new user can:

create an account;

enter their first financial account;

add income and expenses;

understand their current financial month;

create a category budget;

register a purchase in installments;

see future installments;

understand how much budget remains;

use the system comfortably on mobile;

obtain useful information without learning accounting terminology.

The long-term success criterion is:

The application should reduce the amount of manual financial organization the user needs to perform, while increasing their understanding of their own money.

