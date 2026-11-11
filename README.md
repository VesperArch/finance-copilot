# Finance Copilot

Controle financeiro por organização com Django Templates, Django REST Framework, PostgreSQL, HTML, CSS e JavaScript. A P2 preserva cadastro, login, recuperação de senha, contas, categorias, movimentações, orçamentos, compras parceladas e dashboard da P1; acrescenta membros, Administrador/Operador e API por sessão.

## Requisitos

- Python 3.12 ou superior.
- PostgreSQL 14 ou superior.
- Um banco e um usuário PostgreSQL com permissão de criar tabelas. Para executar os testes, o usuário também precisa de `CREATEDB`.

## Instalação

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

No Linux/macOS, a ativação é `source .venv/bin/activate` e a cópia é `cp .env.example .env`.

Preencha `DJANGO_SECRET_KEY` no `.env` com a chave obtida. Configure `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST` e `DATABASE_PORT` com os dados do seu PostgreSQL. Não sobrescreva um `.env` já configurado.

Uma opção para criar o banco, usando as ferramentas do PostgreSQL e um administrador local:

```powershell
createuser -U postgres --pwprompt --createdb finance
createdb -U postgres --owner=finance finance
```

Use o usuário `finance` e a senha que você escolheu no `.env`. A permissão `CREATEDB` é necessária somente para testes; o usuário de produção não deve recebê-la.

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/acesso/cadastro/` para criar a conta de uso pessoal. O superusuário dá acesso ao Admin em `/admin/`; o cadastro público cria o espaço pessoal e suas categorias automaticamente.

## Ambiente local da auditoria P2

Na auditoria de 10/11/2026, este checkout não possuía `.env`, Python utilizável no PATH ou o ambiente portátil citado na P1. Nenhum `.env` foi criado ou sobrescrito. Foi preparado um ambiente ignorado pelo Git: Python 3.13.9 em `.tools/python/python.exe` e PostgreSQL 17.6 em `.tools/postgresql-runtime/pgsql/`. O banco **descartável** `finance_p2_audit` usa exclusivamente `127.0.0.1:55433`, separado dos bancos de uso. A autenticação `trust` deste cluster de teste é somente local; não é configuração de produção.

O cluster de auditoria foi encerrado após os testes. Os arquivos permanecem preservados; use o comando de início abaixo antes de repetir as verificações locais.

Para iniciar o banco após reiniciar o computador:

```powershell
.\.tools\postgresql-runtime\pgsql\bin\pg_ctl.exe -D .tools/pgdata-p2 -l .tools/postgres-p2.log -o "-h 127.0.0.1 -p 55433" start
```

Se ele já estiver rodando, não é preciso iniciá-lo novamente. Para verificar:

```powershell
.\.tools\postgresql-runtime\pgsql\bin\pg_ctl.exe -D .tools/pgdata-p2 status
```

Para iniciar a aplicação sem instalar outro Python:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\.tools\audit-env.ps1
.\.tools\python\python.exe manage.py runserver
```

Para criar um administrador ou executar os testes nesse ambiente:

```powershell
.\.tools\python\python.exe manage.py createsuperuser
.\.tools\python\python.exe manage.py test --noinput
```

Para parar o banco local:

```powershell
.\.tools\postgresql-runtime\pgsql\bin\pg_ctl.exe -D .tools/pgdata-p2 stop
```

## Primeiro uso

1. Crie seu cadastro e adicione uma conta com o saldo inicial.
2. Adicione uma entrada, como salário, e um gasto. Os valores aceitam vírgula decimal.
3. Em Planejamento, defina um limite para uma categoria, mês e ano.
4. Para uma compra parcelada, adicione um gasto, informe o valor total, a primeira data e o número de parcelas.
5. Confira a agenda completa da compra e use o seletor de mês para navegar entre as movimentações futuras.

O botão global “Adicionar” abre o formulário de confirmação. Não há importações nem gravações automáticas sem confirmação.

## Regras financeiras

| Entidade acadêmica | Modelo | Localização |
| --- | --- | --- |
| Conta | `Account` | `apps/finance/models.py` |
| Categoria | `Category` | `apps/finance/models.py` |
| Lançamento | `Transaction` | `apps/finance/models.py` |
| Orçamento | `Budget` | `apps/budgets/models.py` |
| Parcela | `Parcela` | `apps/finance/models.py` |

Os nomes acadêmicos estão preservados também nos nomes exibidos pelo Admin. `FinancialSpace` representa a organização e preserva seu proprietário original; `Membership` associa usuários e papéis ao espaço. `InstallmentGroup` representa a compra original; cada `Parcela` pertence a esse grupo e ao seu lançamento. Seu valor e vencimento estão no lançamento, sem duplicação desses dados.

- Valores monetários usam `Decimal` e `DecimalField(14, 2)`.
- O saldo disponível soma os saldos iniciais e as movimentações até hoje, inclusive de contas desativadas, preservando o histórico.
- Entradas, gastos e orçamentos consideram todo o mês selecionado, incluindo lançamentos e parcelas futuros. Transferências não entram nos totais de entrada, gasto ou orçamento.
- Uma transferência reduz a origem e aumenta o destino na mesma movimentação, sem alterar o saldo total.
- Existe apenas um orçamento por espaço, categoria, mês e ano, com restrição no banco. Categorias de entrada não recebem orçamento.
- Os alertas sinalizam 75%, 90% e 100% do limite; o usuário pode antecipar o primeiro alerta. O restante pode ficar negativo ao ultrapassar o limite.
- A estimativa diária divide o restante dos orçamentos pelos dias restantes, incluindo hoje. Só aparece no mês atual com orçamento definido. Não é uma previsão de saldo bancário nem cobre categorias sem limite.
- Parcelamentos aceitam de 2 a 120 parcelas. O valor regular é truncado para centavos; a última recebe a diferença exata. Nenhuma parcela pode ser zero ou negativa.
- O dia original é preservado sempre que existe. Uma compra em 31 de janeiro vence em 28/29 de fevereiro e 31 de março.
- A compra original é o grupo, sem um lançamento extra pelo total. Isso evita contabilizar a despesa duas vezes.
- Parcelas são criadas em uma transação atômica. Para corrigir uma compra, exclua o grupo inteiro com confirmação e cadastre novamente. Parcelas individuais não podem ser editadas ou excluídas separadamente.
- Contas e categorias em uso não podem ser excluídas. Podem ser desativadas; seguem visíveis no histórico e deixam de ser oferecidas para novos registros.
- Cada consulta, ID e seleção de relacionamento é limitado à organização atual no servidor. Contas/categorias inativas podem permanecer em registros históricos; novas associações são rejeitadas também nos serviços/modelos.
- Lançamentos preservam o autor original ao serem editados por outro membro ou após a saída desse autor. O ator da operação precisa continuar membro; o autor histórico não precisa.

## Arquitetura organizacional e permissões da P2

`FinancialSpace` é o equivalente de `Organizacao` da Aula 14. Criar outra organização acima dele duplicaria o escopo já presente em todos os registros; manter ambas só se justificaria com diferentes conjuntos contábeis dentro da mesma organização, requisito inexistente nesta entrega. A classe abstrata `SpaceRecord` já centraliza a FK e agora impede mover um registro entre espaços na validação.

```text
User ── Membership (ADMIN / OPERATOR) ── FinancialSpace (organização)
                                            ├── Account / Category / Budget
                                            ├── Transaction (user = autor histórico)
                                            └── InstallmentGroup ── Parcela ── Transaction
```

Um usuário pode participar de vários espaços; cada espaço pode ter vários usuários. O cadastro público mantém o comportamento P1: cria um espaço pessoal com categorias e associa seu proprietário como Administrador. O usuário padrão do Django e `AUTH_USER_MODEL` permanecem inalterados.

| Operação | Administrador | Operador |
| --- | --- | --- |
| Consultar dashboard e dados financeiros | Sim | Sim |
| CRUD de contas, categorias, lançamentos e orçamentos | Sim, respeitando regras financeiras | Sim, mesmas regras |
| Criar/excluir compra parcelada completa | Sim | Sim |
| Editar/excluir parcela individual | Não | Não |
| Convidar/remover membros e alterar papéis | Sim, apenas nesta organização | Não |
| Renomear organização | Sim | Não |
| Remover/rebaixar proprietário ou transferir propriedade | Não disponível | Não disponível |
| Django Admin | Somente superusuário Django | Somente superusuário Django |

Esta matriz é uma decisão do projeto; não atribui regras não fornecidas à Aula 15. `is_staff` e `is_superuser` não concedem acesso automático aos dados via HTML/API. Superusuários sem associação recebem 403 controlado na aplicação e mantêm o acesso a `/admin/`.

O contexto usa `financial_space_id` na sessão. `apps/core/access.py` revalida a associação e o papel a cada requisição. O primeiro vínculo é o padrão quando nenhum espaço foi escolhido. A troca exige POST e uma associação existente: HTML `/organizacao/selecionar/<id>/` ou API `/api/context/`. Um contexto revogado retorna 403 e permite selecionar outro espaço autorizado. Nenhum campo de gravação financeira aceita organização/proprietário arbitrário.

Em `/organizacao/`, administradores renomeiam o espaço, gerenciam membros e geram convites para um **username já cadastrado**. O link exige login pela conta convidada e aceite explícito por POST. Expira em 7 dias, tem uso único e só vale se o emissor ainda for Administrador no aceite. Não há envio automático de e-mail. A API também permite revogar convites. Alterações administrativas e aceites usam transações e bloqueio da organização para serializar operações concorrentes.

O Django Admin financeiro continua restrito a superusuários. Membros, convites e histórico financeiro são somente leitura ali, evitando contornar os serviços. Criação/exclusão de organização e alteração de proprietário não são oferecidas pelo Admin. Contas, categorias e orçamento continuam validando modelos e relações. Excluir o usuário proprietário agora usa `PROTECT`, impedindo apagar seu espaço financeiro em cascata.

O isolamento é aplicado na aplicação, não por PostgreSQL RLS. Código interno que usa `save()`, `update()` ou SQL diretamente deve respeitar os serviços e `full_clean()`; Django não chama `clean()` automaticamente em toda gravação ORM. Os pontos HTTP usam serviços e querysets restritos. Superusuários e operadores do banco são acessos técnicos confiáveis, não tenants comuns.

## API REST por sessão

Instale `requirements.txt`, aplique `migrate` e faça login em `/acesso/login/`. A API está em `/api/`; a interface navegável do DRF usa a mesma sessão. Não usa JWT, OAuth nem autenticação Basic. Em requisições POST/PUT/PATCH/DELETE, envie também o cookie CSRF e o cabeçalho `X-CSRFToken` (obtenha o cookie abrindo uma página HTML com formulário após o login). Login e logout existentes continuam protegidos por CSRF; logout é POST em `/acesso/logout/`.

Referências técnicas: [SessionAuthentication e CSRF](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication) e [permissões de views e objetos](https://www.django-rest-framework.org/api-guide/permissions/). As verificações de associação e papel específicas deste projeto estão em `apps/core/access.py` e `apps/api/permissions.py`.

Todas as rotas abaixo exigem autenticação. Recursos financeiros exigem associação à organização atual. Listagens paginam em 25 itens com `count`, `next`, `previous`, `results` e parâmetro `?page=2`. O contexto/profile não são listagens paginadas.

| Endpoint após `/api/` | Métodos | Restrição |
| --- | --- | --- |
| `accounts/`, `categories/`, `transactions/`, `budgets/` | GET, POST | Lista/criação na organização atual |
| Recursos acima + `<id>/` | GET, PUT, PATCH, DELETE | IDs externos retornam 404; registros em uso não são excluídos |
| `purchases/` | GET, POST | Criação usa os mesmos campos de transaction e `installments` de 2 a 120 |
| `purchases/<id>/` | GET, DELETE | Sem atualização: excluir grupo completo e recadastrar |
| `purchases/<id>/installments/` | GET | Agenda paginada da compra |
| `installments/`, `installments/<id>/` | GET | Parcelas somente leitura |
| `organizations/`, `organizations/<id>/` | GET | Somente a organização atual; demais vínculos aparecem em `me/` |
| `organizations/<id>/` | PUT, PATCH | Administrador: somente `name` é editável |
| `members/`, `members/<id>/` | GET | Administrador: membros da organização atual |
| `members/<id>/` | PUT, PATCH, DELETE | Administrador: editar `role` ou remover vínculo; proprietário protegido |
| `invitations/` | GET, POST | Administrador; criação com `username` e `role` |
| `invitations/<uuid>/` | GET, DELETE | Administrador: consultar ou revogar |
| `invitations/<uuid>/accept/` | POST | Conta convidada, mesmo sem associação anterior; aceite de uso único |
| `me/` | GET | Identidade, papel atual e vínculos do próprio usuário |
| `context/` | POST | `{ "financial_space": 1 }`, apenas entre vínculos autorizados |
| `dashboard/?month=2026-11` | GET | Resumo da organização; mês opcional, formato AAAA-MM |

Campos graváveis principais:

- Conta: `name`, `type`, `institution`, `opening_balance`, `active`.
- Categoria: `name`, `type` (`INCOME`/`EXPENSE`), `active`.
- Lançamento: `description`, `type` (`INCOME`/`EXPENSE`/`TRANSFER`), `amount`, `account`, `category`, `date`, `destination_account`, `notes`, `installments` (padrão 1).
- Orçamento: `category`, `month`, `year`, `limit_amount`, `alert_threshold`.

Exemplo de corpo JSON para uma despesa (substitua IDs por registros ativos da organização):

```json
{
  "description": "Mercado",
  "type": "EXPENSE",
  "amount": "100.00",
  "account": 1,
  "category": 6,
  "date": "2026-11-10"
}
```

Use valores monetários como strings com ponto decimal. Para parcelar, adicione `"installments": 3` ao POST de `transactions/` ou `purchases/`: são criados exatamente três lançamentos, e a última parcela recebe os centavos restantes. `transactions/` retorna o primeiro lançamento e `installment_group`; `purchases/` retorna o grupo. Para transferência use `type=TRANSFER`, `category=null`, `destination_account` diferente da origem e sem parcelamento.

Serializers têm campos explícitos, filtram relacionamentos ativos por organização e rejeitam chaves desconhecidas ou somente leitura nas gravações. Organização, autor, origem, IDs e grupo derivado não podem ser atribuídos pelo cliente. HTML e API compartilham `save_transaction`, `save_record`, `delete_record`, `budget_progress` e `dashboard_summary`.

Respostas: 200 leitura/atualização, 201 criação/aceite, 204 exclusão, 400 validação, 403 autenticação por sessão ausente/permissão/CSRF, 404 objeto fora do escopo, 405 método não suportado e 409 conflito de integridade ou registro em uso. Alterar/excluir um lançamento que representa parcela retorna 403; alterar a própria parcela ou atualizar a compra retorna 405. Essas restrições preservam as regras financeiras da P1.

O dashboard existente foi preservado. `Sum`, `aggregate` e `annotate` calculam saldos, entradas, gastos, orçamento e distribuição por categoria. `Count` acrescenta a quantidade de movimentos e o resultado mensal é entradas menos gastos. A API retorna valores monetários como strings, sem conversão para float. `Avg`, `Max` e `Min` não foram adicionados por não haver indicador de domínio que os exigisse. Meses futuros entram nas métricas mensais, mas não reduzem o saldo disponível hoje; transferências não alteram receitas, despesas ou orçamento.

## Estrutura

```text
manage.py
config/
  settings/{base,development,production}.py
  urls.py
  wsgi.py
apps/
  accounts/{forms,views}.py
  accounts/{models,services,organization_forms,organization_views,admin}.py
  accounts/migrations/{0001_initial,0002_legacy_memberships}.py
  api/{serializers,views,permissions,exceptions,urls}.py
  core/
    access.py
    forms.py
    templatetags/money.py
  finance/
    models.py
    forms.py
    views.py
    admin.py
    migrations/{0001_initial,0002_alter_financialspace_owner}.py
    services/{spaces,installments,summary,records}.py
  budgets/
    models.py
    forms.py
    services.py
    admin.py
    migrations/0001_initial.py
templates/
  base.html
  components/
  finance/
  registration/
static/
  css/app.css
  js/app.js
tests/
  test_accounts.py
  test_finance.py
  test_journey.py
  test_p2_{organizations,api,migrations}.py
requirements/base.txt
requirements.txt
.env.example
.gitignore
```

Metas, importação, recorrências, integrações e parsing de texto livre continuam fora do escopo. A auditoria detalhada está em `P2_AUDITORIA.md`, o plano/backlog em `P2_BACKLOG.md` e as melhorias identificadas em `MELHORIAS_P1.md`.

## Verificação

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Os testes usam um banco PostgreSQL separado, criado e removido automaticamente pelo Django. A suíte cobre autenticação, CSRF, CRUD, isolamento entre usuários, transferências, valores inválidos, precisão decimal, parcelas, arredondamento, meses curtos, anos bissextos, unicidade e cálculos de orçamento.

Resultados observados em 10/11/2026:

- Baseline: **46 testes da revisão original P1 aprovados**, executados sobre cópia obtida com `git archive`.
- Suíte final: **96 executados, 96 aprovados, zero falhas/erros**, em 29,278 s. Inclui os 46 originais inalterados e 50 novos testes P2.
- Ambiente: Python 3.13.9, Django 5.2.19, DRF 3.16.1, psycopg 3.3.8 e PostgreSQL 17.6. Nenhum teste usou SQLite.
- `check`: sem problemas; `makemigrations --check --dry-run`: nenhuma alteração pendente; migrations aplicadas do zero e verificadas com dados históricos em banco descartável.
- Chrome headless: 24 verificações em seis páginas, nas larguras 320, 390, 768 e 1440 px, sem transbordamento horizontal. Passaram os fluxos de renomear organização, criar convite, aceitar pela conta convidada, bloquear administração de Operador e alterar papel. Nenhuma exceção JavaScript observada.
- `check --deploy` com settings de produção: somente os dois avisos de HSTS descritos na seção de produção. HTTPS/SMTP reais e aplicação em banco de uso não foram executados.

Para repetir somente os testes P2: `python manage.py test tests.test_p2_organizations tests.test_p2_api tests.test_p2_migrations`. O teste de migração altera apenas o schema do banco de testes gerenciado pelo Django; não deve ser adaptado para rodar em um banco de uso.

Migrations iniciais:

- `finance/0001_initial`: espaço, conta, categoria, compra parcelada, lançamento, parcela, índices e restrições.
- `budgets/0001_initial`: orçamento mensal, unicidade e restrições de valores e período.

Ao modificar modelos:

```powershell
python manage.py makemigrations --no-header
python manage.py migrate
```

### Migração segura da P1

1. Faça backup do banco de uso e teste a atualização em uma cópia; interrompa temporariamente gravações durante o deploy.
2. Instale as dependências atualizadas. Execute `python manage.py migrate --plan` e `python manage.py migrate` com o `.env` correto, sem alterar migrations existentes.
3. `finance/0002_alter_financialspace_owner` troca a política de exclusão do proprietário para PROTECT.
4. `accounts/0001_initial` acrescenta membros e convites com unicidade `(financial_space, user)` e restrições de papel.
5. `accounts/0002_legacy_memberships` usa `RunPython` com models históricos e o alias de banco da migração. Cria um Administrador por proprietário/espaço, inclusive se um proprietário tiver vários espaços. Não reatribui nem modifica registros financeiros.
6. Confirme login, dashboard, vínculos e isolamento. Usuários legados sem espaço continuam sem acesso financeiro até receberem convite; não são associados arbitrariamente a uma organização.

Não foram aplicadas migrations a um banco de uso nesta auditoria. Migrações novas foram verificadas tanto do zero quanto com dados históricos em PostgreSQL descartável. A etapa de dados é idempotente e sua reversão não remove vínculos; reverter o schema de `accounts` removeria as novas tabelas. Para rollback operacional, prefira restaurar o backup validado; não reverta migrations com dados colaborativos sem planejamento.

### Roteiro de isolamento com duas organizações

1. Cadastre Ana e Bia separadamente: cada cadastro tem seu próprio espaço e categorias. Crie contas com nomes distinguíveis e uma despesa em cada um.
2. Autenticada como Ana, confira contas, movimentações, orçamento, dashboard e `/api/` somente com dados de Ana. Troque IDs das URLs HTML/API pelos de Bia: GET/edição/exclusão devem retornar 404; relacionamentos externos devem falhar na validação.
3. Cadastre uma terceira conta para o colaborador. Como Ana, convide esse username como Operador em `/organizacao/`. Abra o link autenticado pelo convidado e confirme o aceite.
4. O colaborador consulta/cria/edita os dados de Ana; tentativas diretas de gerir membros ou renomear organização retornam 403. Edição preserva o autor anterior.
5. Como Ana, altere o colaborador para Administrador e confira o acesso à gestão. Remova seu vínculo e confira que a próxima requisição ao espaço revogado retorna 403, preservando o histórico dos lançamentos.
6. Com vários vínculos, use o seletor da interface ou POST `/api/context/`; IDs de organizações sem associação devem ser recusados. Bia continua isolada, salvo convite aceito explicitamente.

Os cenários equivalentes são automatizados em `tests/test_p2_organizations.py` e `tests/test_p2_api.py`; `tests/test_p2_migrations.py` comprova a preservação do legado.

## E-mail e produção

Em desenvolvimento, os e-mails de recuperação são gravados em `.tools/emails/`, não enviados. Abra o arquivo local para usar o link. Esses arquivos contêm links de recuperação e ficam fora do Git.

Em produção, selecione `config.settings.production` e configure SMTP pelas variáveis de `.env.example`, os hosts permitidos e uma chave secreta própria. Sirva a aplicação por um servidor WSGI atrás de HTTPS e execute `python manage.py collectstatic --noinput --settings=config.settings.production` para preparar os estáticos. Configure o servidor web para servi-los.

O ambiente de produção força `DEBUG=False`, cookies seguros e redirecionamento HTTPS. Revise a infraestrutura e execute `python manage.py check --deploy --settings=config.settings.production` antes de publicar.

Essa checagem aponta dois avisos de publicação: `SECURE_HSTS_INCLUDE_SUBDOMAINS` e `SECURE_HSTS_PRELOAD` não estão habilitados. Defina essas opções quando houver um domínio de produção e garantia de HTTPS em todos os subdomínios. O envio de e-mail real também depende da configuração de SMTP.

O Admin financeiro é restrito a superusuários. Lançamentos e parcelas são somente leitura no Admin para preservar as regras do serviço; use a aplicação para gravá-los. A área pessoal exige um cadastro com espaço financeiro.
