# Melhorias identificadas na auditoria da P1

As evidências referem-se à revisão inicial `8b94913f482768cfe6720bed784a758dd125020f`. São cinco mudanças reais, verificáveis no código P2.

| Melhoria | Evidência na P1 | Implementação P2 | Verificação |
| --- | --- | --- | --- |
| Compartilhar dados com autorização explícita | `core/access.py:personal_space` selecionava apenas `user.financial_spaces`; não havia papéis | `Membership`, contexto validado, Administrador/Operador e convites com aceite | Testes de dois membros, duas organizações, URLs diretas, revogação e papéis em HTML/API |
| Proteger dados contra exclusão do proprietário | `FinancialSpace.owner` usava CASCADE, podendo apagar o espaço ao excluir o usuário | PROTECT em `finance/0002`; criação/exclusão de organização indisponível no Admin | `test_owner_account_deletion_is_protected` e teste de migração |
| Preservar autoria e origem no histórico | `TransactionForm` atribuía sempre o usuário atual; o serviço de parcelas não copiava `source` | Formulário só atribui autor em criação, modelo rejeita troca de autor e parcelas herdam origem | Edição por outro membro em HTML/API; compra API mantém `source=API` em todas as parcelas |
| Aplicar regra de inatividade também no domínio | Formulários filtravam ativos, mas `Transaction.clean` e `Budget.clean` não rejeitavam novas relações inativas | Validação nos modelos preserva relações históricas e rejeita novas associações inativas | Testes via serviço/API e regressões de histórico P1 |
| Disponibilizar integração sem duplicar cálculos | Não havia DRF nem endpoints; operações financeiras existiam apenas no HTML/serviços | API por sessão/CSRF, campos explícitos, relações filtradas e reutilização dos serviços | CRUD, mass assignment, IDs externos, precisão, parcelas, dashboard e consultas sem N+1 |

Nenhuma migration inicial foi reescrita. Os 46 testes da P1 permaneceram inalterados.
