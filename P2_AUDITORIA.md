# Auditoria técnica e implementação da P2 — Finance Copilot

Data: 10/11/2026. Revisão inicial: `8b94913f482768cfe6720bed784a758dd125020f`.

## A. Diagnóstico inicial

O checkout estava limpo, sem alterações preexistentes ou AGENTS.md aplicável. A evidência principal foi o código, incluindo migrations, formulários, views, serviços, templates e testes; o README foi confrontado com o ambiente real.

| Área | Estado anterior | Evidência |
| --- | --- | --- |
| Autenticação | Implementada | User padrão, SignupForm, auth URLs, CSRF, recuperação de senha |
| Domínio financeiro | Implementado | Account, Category, Transaction, Budget, InstallmentGroup, Parcela e constraints P1 |
| Serviços financeiros | Implementados | Parcelamento atômico, arredondamento, datas, account_balances, budget_progress |
| Isolamento | Parcial para P2 | Querysets e formulários filtravam FinancialSpace, mas personal_space só buscava proprietário |
| Organizações compartilhadas | Ausentes | Sem vínculo de colaboração ou mecanismo de associação por papel |
| Papéis e gestão de membros | Ausentes | Apenas restrição do Django Admin a superusuários |
| API REST | Ausente | Sem DRF nas dependências e sem rotas /api/ |
| Dashboard | Funcional na P1 | Sum, annotate e aggregate por espaço, considerando futuro nas métricas mensais |
| Testes | 46 testes presentes | Baseline executado e aprovado nesta auditoria em PostgreSQL 17.6 |
| Ambiente descrito no README | Desatualizado neste checkout | Sem .env, .tools e Python executável no PATH |

Os 46 testes originais foram executados sobre cópia da revisão inicial obtida com `git archive`. Nenhum arquivo da P1 ou migration inicial foi alterado para produzir esse baseline.

## B. Alterações realizadas

- FinancialSpace evoluído para organização, sem tabela organizacional duplicada ou reatribuição de registros.
- Membership com Administrador/Operador e restrição de unicidade; cadastro cria vínculo ADMIN.
- Contexto escolhido na sessão e revalidado por associação no servidor. Troca de contexto somente por POST.
- Gestão HTML de nome, membros e papéis; convites vinculados à conta convidada, com expiração e aceite explícito. Administração não depende apenas de botões ocultos.
- Serviços administrativos transacionais bloqueiam o espaço antes de alterar membros, aceitar/revogar convites ou renomear a organização.
- Querysets HTML/API e relacionamentos restritos ao contexto. Registros de outras organizações retornam 404 e relacionamentos externos falham antes da gravação.
- Autoria dos lançamentos preservada nas edições; histórico permanece após a saída de membros. Parcelas propagam a origem do lançamento inicial.
- Validação de novas relações inativas centralizada nos modelos; relações históricas inativas continuam editáveis sem troca forçada.
- PROTECT no proprietário evita apagar seu espaço por exclusão do usuário. Admin de membros/convites/histórico é somente leitura.
- API DRF por sessão/CSRF, paginação, campos explícitos, proteção de atribuição em massa e erros coerentes.
- Dashboard preservado e disponibilizado na API pelos mesmos serviços, acrescentando resultado mensal e contagem de movimentos.
- Templates em português e estilos existentes preservados, com controles organizacionais e recuperação de contexto revogado.

## C. Arquivos criados ou alterados

As listas abaixo incluem os arquivos de implementação e documentação; não incluem cache, ferramentas ou logs ignorados em `.tools/`.

| Arquivos | Finalidade |
| --- | --- |
| `apps/accounts/models.py` | Membership, Role e MembershipInvitation |
| `apps/accounts/migrations/__init__.py` | Pacote de migrations do app existente |
| `apps/accounts/migrations/0001_initial.py` | Schema aditivo de membros/convites e constraints |
| `apps/accounts/migrations/0002_legacy_memberships.py` | Proprietários legados viram administradores usando models históricos |
| `apps/accounts/services.py` | Administração organizacional, convites, aceite e revogação |
| `apps/accounts/organization_forms.py` | Campos administrativos explícitos |
| `apps/accounts/organization_views.py` | Gestão HTML e troca de contexto |
| `apps/accounts/admin.py` | Consulta de vínculos/convites exclusiva para superusuários |
| `apps/core/access.py` | Contexto e autorização reutilizáveis |
| `apps/core/context_processors.py` | Seletor organizacional e papel atual na interface |
| `apps/finance/models.py` | Espaço imutável na validação, autoria/histórico, inatividade e PROTECT |
| `apps/finance/migrations/0002_alter_financialspace_owner.py` | Política de exclusão segura do proprietário |
| `apps/finance/forms.py` | Preservação do autor em edição colaborativa |
| `apps/finance/views.py` | Contexto por associação e gravações pelos serviços |
| `apps/finance/admin.py` | Proteção de criação/exclusão do espaço e proprietário somente leitura |
| `apps/finance/services/spaces.py` | Cadastro com associação ADMIN |
| `apps/finance/services/installments.py` | Ator autorizado, proteção de parcelas persistidas e propagação de source |
| `apps/finance/services/records.py` | Gravação/exclusão financeira com associação validada e transação |
| `apps/finance/services/summary.py` | Reuso do resumo, resultado mensal e Count |
| `apps/budgets/models.py` | Rejeição de novas associações com categoria inativa |
| `apps/api/__init__.py` | Pacote da API |
| `apps/api/serializers.py` | Campos explícitos, relações filtradas, validação de domínio e proteção de campos |
| `apps/api/permissions.py` | Associação e administração verificadas no backend |
| `apps/api/views.py` | Recursos REST, perfil, contexto, dashboard e aceite |
| `apps/api/urls.py` | Router e rotas auxiliares sob /api/ |
| `apps/api/exceptions.py` | Conversão de erros de domínio e conflitos HTTP |
| `config/settings/base.py` | DRF, sessão, paginação, renderers e context processor |
| `config/urls.py` | Inclusão de API e telas organizacionais |
| `requirements/base.txt` | Dependência DRF 3.16, sem biblioteca adicional de autenticação |
| `templates/base.html` | Contexto, troca autorizada e link de gestão |
| `templates/403.html` | Tratamento controlado de ausência de associação/permissão |
| `templates/accounts/organization.html` | Configuração, membros e criação de convite |
| `templates/accounts/member.html` | Papel e confirmação explícita de remoção |
| `templates/accounts/invitation.html` | Aceite explícito do convite |
| `static/css/app.css` | Ajustes mínimos para controles organizacionais e links longos |
| `tests/test_p2_organizations.py` | Compartilhamento, HTML, papéis, contexto, convites, serviços e Admin |
| `tests/test_p2_api.py` | CRUD, autorização, isolamento, CSRF, regras financeiras e N+1 |
| `tests/test_p2_migrations.py` | Migração de registros históricos com IDs, valores, datas e vínculos preservados |
| `README.md` | Uso, instalação, arquitetura, matriz de papéis, rotas, migração e testes |
| `MELHORIAS_P1.md` | Cinco melhorias reais fundamentadas na auditoria |
| `P2_BACKLOG.md` | Matriz inicial, decisões, plano e issues propostas localmente |
| `P2_AUDITORIA.md` | Relatório técnico e evidências finais |

## D. Arquitetura final

FinancialSpace é o tenant/organização. Todos os registros de negócio continuam associados ao mesmo espaço da P1. SpaceRecord centraliza essa FK para contas, categorias, lançamentos, compras e orçamentos; Parcela deriva o escopo do grupo e do lançamento, sem duplicar valores ou vencimentos.

User continua sendo o usuário padrão do Django. Membership permite vários usuários por organização e várias organizações por usuário, mantendo os espaços legados separados. O proprietário original permanece Administrador e não pode ser removido/rebaixado pelos fluxos da aplicação. Não existe transferência de propriedade nesta entrega.

Os dois papéis podem executar operações financeiras existentes; apenas Administrador gerencia nome, membros e convites. A sessão indica qual associação usar; o backend verifica o vínculo a cada requisição, inclusive após revogação. Não existe bypass de tenant por is_staff/is_superuser. O Django Admin continua sendo ferramenta global confiável para superusuários.

A migração é aditiva e não altera AUTH_USER_MODEL nem IDs financeiros. O teste histórico cobre dois espaços do mesmo proprietário, uma segunda organização, contas/categorias inativas, orçamento e parcelas com vencimento em fevereiro bissexto. Nenhum registro financeiro é reatribuído.

## E. API REST

As rotas exatas, campos e exemplos estão no README. Resumo:

| Recurso sob `/api/` | Métodos |
| --- | --- |
| accounts, categories, transactions, budgets | GET/POST na coleção; GET/PUT/PATCH/DELETE no detalhe |
| purchases | GET/POST na coleção; GET/DELETE no detalhe |
| purchases/ID/installments, installments, installments/ID | GET |
| organizations | GET da organização atual; PUT/PATCH do nome no detalhe por Administrador |
| members | GET; PUT/PATCH/DELETE no detalhe por Administrador |
| invitations | GET/POST; GET/DELETE no detalhe por Administrador |
| invitations/UUID/accept | POST da conta convidada |
| me, dashboard | GET |
| context | POST com ID de organização associada |

Autenticação somente por sessão Django com CSRF para métodos de gravação. Os serializers validam modelos e filtram contas/categorias por espaço/atividade. Campos protegidos e desconhecidos são rejeitados nas gravações de recursos. O aceite usa exclusivamente a identidade autenticada e o papel persistido no convite, ignorando qualquer tentativa de substituí-los no corpo da requisição.

CRUD financeiro reaproveita os serviços; não há implementação paralela de parcelamento ou métricas. Edição/exclusão individual de parcelas é bloqueada, e registros em uso retornam 409. Listagens são paginadas em 25 itens.

## F. Testes e verificações

Ambiente efetivamente usado: Python 3.13.9, Django 5.2.19, DRF 3.16.1, psycopg 3.3.8 e PostgreSQL 17.6 no Windows. Não foi usado SQLite.

Baseline P1: **46 executados, 46 aprovados**. Suíte final P1/P2: **96 executados, 96 aprovados, zero falhas/erros**, em **29,278 s**. Os 46 testes originais permaneceram inalterados; foram acrescentados 50 testes. A única falha intermediária era um teste novo que reutilizava um objeto alterado em memória; o estado foi restaurado antes da segunda asserção, sem enfraquecer a validação de domínio.

Comandos executados com variáveis direcionadas exclusivamente ao banco descartável:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\.tools\audit-env.ps1
.\.tools\python\python.exe .tools/run_p1.py test --noinput --verbosity 1
.\.tools\python\python.exe manage.py check
.\.tools\python\python.exe manage.py makemigrations --check --dry-run
.\.tools\python\python.exe manage.py migrate --noinput
.\.tools\python\python.exe manage.py test --noinput --verbosity 1
.\.tools\python\python.exe manage.py check --deploy --settings=config.settings.production
.\.tools\python\python.exe -m compileall -q apps config tests
.\.tools\python\python.exe .tools/browser_audit.py
git diff --check
```

`check`: sem problemas. `makemigrations --check --dry-run`: sem mudanças pendentes. Migrações aplicadas com sucesso no banco descartável e exercitadas com dados P1 pelo MigrationExecutor. Compilação de imports concluída; URLs e serializers exercitados pelos testes HTTP.

Chrome headless real: **24 verificações de layout**, cobrindo dashboard, organização, membro, contas, criação de movimentação e orçamento em **320, 390, 768 e 1440 px**, sem transbordamento horizontal. Cinco fluxos adicionais passaram: renomear organização, criar convite, aceite pela conta convidada, recusa de administração para Operador e alteração de papel. Nenhuma exceção JavaScript observada. A página com o link longo do convite também foi conferida em 320 px.

Evidências locais ignoradas pelo Git: `.tools/p2-tests-final.log`, `.tools/browser-results.json`, `.tools/browser_audit.py` e logs do servidor/navegador. As ferramentas auxiliares permanecem locais e não são dependências de produção. Os processos temporários de servidor e Chrome foram encerrados após a verificação.

O PostgreSQL descartável também foi encerrado no fechamento, sem remover seus arquivos. O README contém o comando para reiniciá-lo e repetir os testes locais.

## G. Conformidade acadêmica

| Pilar | Estado | Evidência concreta |
| --- | --- | --- |
| A — Multi-organização | Atendido | FinancialSpace + Membership; migração histórica; filtros HTML/API; testes de IDs/relacionamentos externos, dados compartilhados e contexto revogado |
| B — Perfis e permissões | Atendido | Role ADMIN/OPERATOR, core/access.py, serviços administrativos, permissões DRF, gestão HTML e testes de URLs diretas/superusuários |
| C — API REST | Atendido | apps/api, sessão/CSRF, CRUD conforme domínio, campos explícitos, paginação, conflitos e testes de endpoints |
| D — Dashboard/relatórios | Atendido | Mesmo dashboard e serviços de Sum/Count, aggregate/annotate, métricas mensais, categorias, orçamento e testes de precisão/isolamento/futuro |

O material completo da Aula 15 não estava no repositório. A matriz de papéis é uma decisão documentada do projeto, sem atribuição de políticas não verificadas ao professor. Nenhum indicador artificial ou biblioteca de autenticação adicional foi introduzido.

## H. Pendências e limites reais

- Aplicação das migrations em um banco de uso fica pendente: nenhum .env ou banco real foi fornecido/configurado neste checkout. A entrega valida schema e dados legados em PostgreSQL descartável; não simula um deploy concluído.
- Produção: HTTPS/SMTP reais não foram exercitados. `check --deploy` aponta os dois avisos existentes de HSTS (`security.W005` e `security.W021`), dependentes da política do domínio.
- Convites exigem usuário já cadastrado; links são compartilhados manualmente, sem envio automático. Transferência de propriedade e exclusão de organização não fazem parte do domínio exposto.
- Isolamento é garantido pelos fluxos da aplicação, não por RLS. Scripts SQL/ORM privilegiados devem respeitar full_clean/serviços. As versões executadas foram as listadas na seção F, sem afirmar execução em outras versões.

## I. Git

Todas as alterações permanecem locais. Não foram executados commit, push, git add, troca/criação/exclusão de branch, reset, clean, descarte de alterações ou modificação de histórico. HEAD permaneceu na revisão inicial e o staging permaneceu vazio nas verificações. Nenhuma issue remota foi criada.
