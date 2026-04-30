Descrição
Briefings são resumos de notícias ou informações relevantes sobre um determinado assunto.

Briefings são úteis para manter as pessoas informadas sobre tópicos de interesse sem que precisem buscar ativamente por informações. Tais recursos são amplamente utilizados em contextos corporativos, jornalísticos e pessoais para fornecer atualizações rápidas e concisas sobre eventos, tendências ou áreas específicas.

A ideia do Projeto Prático #01 é construir um sistema que gera briefings personalizados de notícias e os distribui automaticamente por e-mail e Discord usando agentes de IA.

O fluxo de configuração do sistema é inteiramente via Discord: o usuário configura suas preferências (tópicos de interesse, palavras-chave prioritárias, etc.) respondendo perguntas do agente em um chat do Discord.

Em períodos determinados (e.g., 1 vez por dia às 7h da manhã), o agente busca notícias recentes, gera um briefing consolidado e envia-o tanto no Discord quanto por e-mail.

IMPORTANTE: O sistema deve ser implementado em Python com o framework Agno, conforme material disponibilizado na disciplina.

Requisitos Funcionais Mínimos
1. O agente deve iniciar conversa no Discord para coletar preferências:
   - Tópicos de interesse
   - Palavras-chave prioritárias para cada tópico
   - Número máximo de notícias por tópico
   - E-mail de destino para envio do briefing
   - ID do canal do Discord para envio do briefing
2. O agente deve buscar notícias recentes sobre cada tópico.
3. O agente deve gerar o briefing com estrutura definida pela equipe de desenvolvimento.
4. O agente deve enviar o briefing no horário adequado para o canal Discord configurado.
5. O agente deve enviar um e-mail com o conteúdo do briefing para o endereço configurado.

Práticas Obrigatórias de Engenharia de Software
Organização
Repositório com estrutura de arquivos e diretórios clara e organizada
Arquivo README.md com descrição do projeto, instruções de instalação/execução e estrutura de diretórios
.gitignore adequado para Python
Gerenciamento de dependências baseado em pyproject.toml
.env para variáveis de ambiente
Clean Code
Código homogêneo em estilo, idioma e formatação (PEP8 para Python, em inglês)
Funções curtas (preferivelmente com no máximo 20 linhas)
Nomes descritivos (variáveis, funções, classes)
Type hints e docstrings em todas as assinaturas
Princípios de Desenvolvimento
Single Responsibility Principle (SRP): Cada classe/função com uma única responsabilidade
Open/Closed Principle (OCP): Aberto para extensão, fechado para modificação; evite blocos condicionais extensos e use polimorfismo
Interface Segregation Principle (ISP): Prefira interfaces/classes abstratas específicas
Dependency Inversion Principle (DIP): Dependa de abstrações, não de implementações concretas; use injeção de dependências