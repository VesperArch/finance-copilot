# Finance Copilot

Controle financeiro pessoal com Django Templates, PostgreSQL, HTML, CSS e JavaScript. O primeiro milestone inclui cadastro, login, recuperação de senha, contas, categorias, movimentações, orçamento mensal por categoria, compras parceladas e dashboard responsivo.

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

## Ambiente local preparado nesta pasta

Há um Python e um PostgreSQL portáteis em `.tools/`, ignorados pelo Git. O `.env` local já está configurado com credenciais aleatórias, banco `finance` e PostgreSQL em `127.0.0.1:55432`. As migrations já foram aplicadas. Esses arquivos locais não fazem parte da distribuição do projeto.

Para iniciar o banco após reiniciar o computador:

```powershell
.\.tools\postgresql\pgsql\bin\pg_ctl.exe -D .tools/pgdata -l .tools/postgres.log -o "-h 127.0.0.1 -p 55432" start
```

Se ele já estiver rodando, não é preciso iniciá-lo novamente. Para verificar:

```powershell
.\.tools\postgresql\pgsql\bin\pg_ctl.exe -D .tools/pgdata status
```

Para iniciar a aplicação sem instalar outro Python:

```powershell
.\.tools\python\tools\python.exe manage.py runserver
```

Para criar um administrador ou executar os testes nesse ambiente:

```powershell
.\.tools\python\tools\python.exe manage.py createsuperuser
.\.tools\python\tools\python.exe manage.py test
```

Para parar o banco local:

```powershell
.\.tools\postgresql\pgsql\bin\pg_ctl.exe -D .tools/pgdata stop
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

Os nomes acadêmicos estão preservados também nos nomes exibidos pelo Admin. `FinancialSpace` pertence a um usuário e organiza todos os registros. `InstallmentGroup` representa a compra original; cada `Parcela` pertence a esse grupo e ao seu lançamento. Seu valor e vencimento estão no lançamento, sem duplicação desses dados.

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
- Cada acesso e seleção de relacionamento é limitado ao espaço do usuário no servidor. A interface P1 expõe o primeiro espaço pessoal; colaboração e papéis ficam para P2.

## Estrutura

```text
manage.py
config/
  settings/{base,development,production}.py
  urls.py
  wsgi.py
apps/
  accounts/{forms,views}.py
  core/
    access.py
    forms.py
    templatetags/money.py
  finance/
    models.py
    forms.py
    views.py
    admin.py
    migrations/0001_initial.py
    services/{spaces,installments,summary}.py
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
requirements/base.txt
requirements.txt
.env.example
.gitignore
```

Não foram criados módulos vazios para funcionalidades futuras. Metas, importação, recorrências, integrações, parsing de texto livre e API não fazem parte deste milestone.

## Verificação

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Os testes usam um banco PostgreSQL separado, criado e removido automaticamente pelo Django. A suíte cobre autenticação, CSRF, CRUD, isolamento entre usuários, transferências, valores inválidos, precisão decimal, parcelas, arredondamento, meses curtos, anos bissextos, unicidade e cálculos de orçamento.

Validação deste milestone: 46 testes Django aprovados em PostgreSQL 17.6, `check` sem problemas e nenhuma migration pendente. Uma verificação adicional no Chrome percorreu cadastro, conta, lançamentos, parcelamento e orçamento, além de conferir as páginas nas larguras de 320, 390, 768 e 1440 pixels, sem transbordamento horizontal ou erros JavaScript. A ferramenta de navegador foi usada somente no ambiente local de verificação.

Migrations iniciais:

- `finance/0001_initial`: espaço, conta, categoria, compra parcelada, lançamento, parcela, índices e restrições.
- `budgets/0001_initial`: orçamento mensal, unicidade e restrições de valores e período.

Ao modificar modelos:

```powershell
python manage.py makemigrations --no-header
python manage.py migrate
```

## E-mail e produção

Em desenvolvimento, os e-mails de recuperação são gravados em `.tools/emails/`, não enviados. Abra o arquivo local para usar o link. Esses arquivos contêm links de recuperação e ficam fora do Git.

Em produção, selecione `config.settings.production` e configure SMTP pelas variáveis de `.env.example`, os hosts permitidos e uma chave secreta própria. Sirva a aplicação por um servidor WSGI atrás de HTTPS e execute `python manage.py collectstatic --noinput --settings=config.settings.production` para preparar os estáticos. Configure o servidor web para servi-los.

O ambiente de produção força `DEBUG=False`, cookies seguros e redirecionamento HTTPS. Revise a infraestrutura e execute `python manage.py check --deploy --settings=config.settings.production` antes de publicar.

Essa checagem aponta dois avisos de publicação: `SECURE_HSTS_INCLUDE_SUBDOMAINS` e `SECURE_HSTS_PRELOAD` não estão habilitados. Defina essas opções quando houver um domínio de produção e garantia de HTTPS em todos os subdomínios. O envio de e-mail real também depende da configuração de SMTP.

O Admin financeiro é restrito a superusuários. Lançamentos e parcelas são somente leitura no Admin para preservar as regras do serviço; use a aplicação para gravá-los. A área pessoal exige um cadastro com espaço financeiro.
