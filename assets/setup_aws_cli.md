# Log de Configuração: Ambiente de Nuvem Local
**Data:** 2026-02-01  
**Referência:** https://docs.aws.amazon.com/pt_br/cli/latest/userguide/getting-started-install.html

---

## 1. Instalação da AWS CLI
- **Método:** Instalador MSI oficial para Windows v2.
- **Guia de Instalação:** [AWS CLI Installation Guide](https://docs.aws.amazon.com/pt_br/cli/latest/userguide/getting-started-install.html)
- **Verificação:** O executável deve ser validado no terminal após a instalação.

## 2. Configuração de Credenciais
Foi configurada a AWS CLI para permitir a comunicação com o ambiente de testes local.
- **Access Key:** `test`
- **Secret Key:** `test`
- **Region:** `us-east-1`
- **Output:** `json`

## 3. Automação do Terminal (Aliases)
Foram adicionados atalhos para simplificar os comandos e resolver conflitos de caminho:
- `aws`: Aponta para o caminho directo do executável no sistema.
- `awslocal`: Atalho que inclui o endpoint local `http://localhost:4566` e desabilita a conversão de caminhos.

## 4. Validação do Armazenamento
- **Estado Final:** Conexão estabelecida e listagem de objectos validada no serviço de armazenamento de objectos.