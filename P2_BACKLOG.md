# P2 — plano, auditoria e backlog local

Revisão inicial: `8b94913f482768cfe6720bed784a758dd125020f`, árvore limpa.
Não há AGENTS.md aplicável nem ferramenta de plano nesta sessão; este arquivo mantém o plano executável.

## Matriz inicial

| Pilar | Estado inicial | Evidência | Ação |
| --- | --- | --- | --- |
| A: organizações | Parcial | SpaceRecord, personal_space e filtros HTML; acesso apenas pelo proprietário | Evoluir FinancialSpace, migrar proprietários para membros e resolver contexto autorizado |
| B: papéis | Ausente | User padrão, Admin exclusivo de superusuário | Membros Administrador/Operador, convites e controles centralizados |
| C: API | Ausente | Sem DRF nas dependências e sem /api/ | API por sessão, reutilizando serviços financeiros |
| D: dashboard | Parcial | summary.py e budget_progress usam Sum e filtros por espaço | Compartilhar por membros e testar isolamento, agregações e regressões |
| Testes | P1 presente, execução ainda não verificada | 46 testes históricos no README | Executar baseline e suíte expandida em PostgreSQL |
| Documentação | P1 | README | Atualizar arquitetura, rotas, migrações, evidências e melhorias |

## Decisão de arquitetura

- Evoluir FinancialSpace como organização é a alternativa mais simples: todos os registros já têm esse vínculo (Parcela por grupo/lançamento).
- Uma entidade Organizacao acima do espaço duplicaria o escopo sem requisito de domínio. Separar ambas só seria justificável com vários espaços contábeis por organização, fora desta P2.
- Membership permite vários usuários por espaço e preserva inclusive múltiplos espaços legados do mesmo proprietário. A sessão escolhe apenas entre associações válidas, verificadas a cada requisição.
- Não alterar AUTH_USER_MODEL, IDs, relações nem migrations da P1. Migração aditiva cria associações de administradores para proprietários existentes.
- Operadores e administradores executam o CRUD financeiro existente. Só administradores gerenciam organização, membros e convites. O proprietário permanece administrador; não há transferência de propriedade nesta versão.
- Riscos principais: relações entre espaços, histórico autoral de lançamentos, alterações indevidas de parcelas, vínculos legados e concorrência na administração. Validar no modelo/serviço e em PostgreSQL descartável.

## Plano de execução

- [x] Reconhecimento sem edições, Git, models, migrations, forms, views, serviços, templates, settings e testes.
- [x] A — membership, resolução/switch de contexto, migração legada e integridade.
- [x] B — papéis, gestão de membros/convites, cadastro e Admin seguros.
- [x] C — DRF, serializers, CRUD adequado, sessão/CSRF e documentação das rotas.
- [x] D — preservar dashboard e validar métricas por organização.
- [x] Testes — baseline, regressões P1, isolamento HTML/API, papéis, migração e PostgreSQL.
- [x] Documentação — README, MELHORIAS_P1.md, matriz final e limitações observadas.
- [x] Revisão final — check, migrations, testes, diff, Git e relatório.

## Issues locais rastreáveis aos pilares

| ID | Pilar | Tarefa | Estado e evidência |
| --- | --- | --- | --- |
| P2-A01 | A | Evoluir FinancialSpace sem organização duplicada | Concluída: Membership e core/access.py |
| P2-A02 | A | Migrar proprietários sem mover dados | Concluída: accounts/0002 e test_p2_migrations.py |
| P2-A03 | A | Proteger relações, URLs e contexto | Concluída: models/forms, serializers e testes HTML/API |
| P2-B01 | B | Papéis e gestão com autorização no backend | Concluída: services, organization_views e permissions |
| P2-B02 | B | Convites com consentimento e revogação | Concluída: convite por conta, expiração, aceite único e locks |
| P2-B03 | B | Proteger autoria, proprietário e acesso ao Admin | Concluída: validações, PROTECT, Admin somente leitura e testes |
| P2-C01 | C | API CRUD por sessão/CSRF | Concluída: apps/api e requirements/base.txt |
| P2-C02 | C | Reusar domínio e proteger parcelas | Concluída: mesmos serviços e testes de precisão, datas, atomismo e métodos proibidos |
| P2-D01 | D | Manter métricas por organização | Concluída: summary/budget_progress e testes de saldo, período, orçamento e categorias |
| P2-Q01 | A–D | Regressões e migração em PostgreSQL | Concluída: baseline 46/46; suíte final 96/96; check e migrations consistentes |
| P2-Q02 | B/D | Validar fluxos e responsividade reais | Concluída: Chrome, 24 verificações de layout e cinco fluxos, zero exceções JS |
| P2-DEP01 | A | Aplicar atualização em cópia/banco de uso com backup | Pendente de ambiente de uso configurado; validação descartável concluída |
| P2-DEP02 | B/C | Validar infraestrutura HTTPS/SMTP e decidir HSTS por domínio | Pendente de infraestrutura de produção; check --deploy observou W005/W021 |

Nenhuma issue remota foi criada. P2-DEP01/P2-DEP02 são atividades de implantação, não funcionalidades apresentadas como concluídas. Limites deliberados: sem transferência de propriedade/exclusão de organização e sem e-mail automático de convites.

## Fechamento observado

- 10/11/2026: PostgreSQL 17.6 real, sem SQLite; 96 testes passaram em 29,278 s, incluindo os 46 originais sem alteração.
- Migrations aplicadas no ambiente descartável e testadas com registros da P1. Nenhuma migration inicial foi reescrita.
- Chrome, servidor temporário e PostgreSQL descartável encerrados após os testes; arquivos e relatórios locais preservados em .tools.
- HEAD preservado em `8b94913f482768cfe6720bed784a758dd125020f`, staging vazio, sem commit/push ou operações de branch.
