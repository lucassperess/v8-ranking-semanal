# Desenvolvimento e roteiro de leitura

Este guia permite localizar o cálculo, preparar um ambiente e verificar mudanças sem depender do histórico da conversa. A [documentação de uso](como-usar.md) atende quem explora a interface; este artigo atende quem mantém o código.

## Roteiro recomendado

1. [README principal](../README.md): objetivo, resultado de referência e comandos de reprodução.
2. [Decisões](decisoes.md) e [metodologia](metodologia.md): definições e limites que governam o cálculo.
3. [Arquitetura](sistema.md): caminho do envio ao resultado.
4. [weekly_ranking.py](../weekly_ranking.py): siga `run`, `choose_week`, `rank_pair` e a geração do relatório.
5. Módulos abaixo: acompanhe as entradas e saídas de cada etapa.
6. [Testes](../tests): exemplos dos contratos e comportamentos esperados.
7. [Resultado do case](../resultados/2026-09-22/README.md): exemplo histórico, com arquivos derivados versionados.

## Mapa técnico

| Arquivo ou pasta | Responsabilidade | Teste principal |
| --- | --- | --- |
| `etl.py` | Ler esquema, normalizar campos, preservar linhas, registrar qualidade e manifesto | `test_etl.py` |
| `b3_registry.py` | Interpretar cadastro B3 e calcular identificações de conteúdo | `test_b3_registry.py` |
| `resolve_period.py` | Obter e reaproveitar fontes datadas para as pontas | Casos de resolução em `test_classify_period.py` |
| `classify_period.py` | Reunir evidências oficiais e classificação por instrumento/data | `test_classify_period.py` |
| `ranking_universe.py` | Decidir incluir, excluir ou revisar para ON/PN | `test_ranking_universe.py` |
| `weekly_ranking.py` | Escolher janela, ordenar retornos e produzir média/relatórios | `test_weekly_ranking.py` |
| `verify_b3.py` | Conferência adicional de classificação com COTAHIST | `test_verify_b3.py` |
| `review_exceptions.py` | Revisão opcional de exceções, separada da rotina principal | `test_review_exceptions.py` |
| `webapp/server.py`, `store.py`, `worker.py` | API, persistência/fila, processamento e limpeza | `test_webapp.py` cobre API, fila e apresentação; não é teste integral da operação na VPS |
| `webapp/presentation.py` | Adaptar derivados e calcular contexto visual em Python | `test_webapp.py` |
| `webapp/documentation.py`, `docs/` | Renderizar artigos Markdown versionados e índice de busca | `test_webapp.py` |
| `webapp/static/` | Interface HTML/CSS/JavaScript | Conferência no navegador das páginas afetadas |
| `scripts/create_featured_daily.py` | Preparar séries visuais da demonstração a partir do bruto | Conferir saídas e lacunas ao atualizar a demonstração |
| `scripts/export_audit.py` | Exportar evidências derivadas de uma execução para a demonstração correspondente | Confere assinaturas e recusa versões conflitantes antes da cópia |
| `deploy/` | Docker, Traefik e operação da aplicação | Verificação de saúde e HTTPS após publicação autorizada |

Nem toda linha do projeto possui teste automático específico. Use a tabela para localizar verificações existentes, sem pressupor cobertura integral.

## Preparar o ambiente

O núcleo de tratamento/classificação/ranking usa Python 3.11+ e a biblioteca padrão. Para trabalhar na interface e executar todos os testes, instale as dependências de desenvolvimento, que incluem as da aplicação.

### Windows / PowerShell

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m unittest discover -s tests -v
```

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
```

`requirements-web.txt` instala o necessário para servir o site. `requirements-dev.txt` inclui também `httpx`, utilizado nos testes da API. Os comandos acima usam o executável da pasta virtual explicitamente, sem exigir ativação do ambiente.

## Executar a interface local

No Windows, a partir da raiz, em um terminal:

```powershell
.venv\Scripts\python -m uvicorn webapp.server:app --host 127.0.0.1 --port 8000
```

Em outro terminal:

```powershell
.venv\Scripts\python -m webapp.worker
```

Abra `http://127.0.0.1:8000`. No Linux/macOS, use `.venv/bin/python` nos mesmos comandos. A demonstração pode ser consultada sem worker; novos envios precisam dele.

O diretório padrão de estado local é `runtime-data/`. A variável `RANKING_DATA_DIR` permite outro diretório. A operação da VPS e suas configurações ficam em [deploy/README.md](../deploy/README.md).

## Reproduzir o pipeline

Exemplo da referência, com o CSV original disponível fora do Git:

```powershell
.venv\Scripts\python weekly_ranking.py --input "CAMINHO\economatica.csv" --reference-date 2026-09-22 --output-dir "runs\reproducao-2026-09-22"
```

Para uma nova extração, substitua arquivo, referência e diretório. Fontes oficiais ausentes podem ser baixadas. `--reference-dir` escolhe a pasta de fontes; `--offline` impede novas buscas e só permite concluir se as evidências guardadas forem suficientes.

Não é possível reproduzir integralmente o case apenas com os derivados do Git: o CSV bruto e as fontes necessárias também são entradas. Veja [auditoria](auditoria.md) para o que está disponível publicamente.

Para complementar uma demonstração com evidências da **mesma execução**, use:

```powershell
.venv\Scripts\python -m scripts.export_audit --run-dir "runs\reproducao-2026-09-22" --destination "resultados\2026-09-22"
```

O destino deve existir e conter o mesmo `ranking_report.json`. O exportador confere as evidências e recusa arquivos existentes com conteúdo diferente antes de copiar. Ele não publica bruto nem altera retornos, README editorial ou séries diárias. Uma reprodução com outra versão de código pode gerar outro relatório: nesse caso, use outro destino para a nova demonstração, sem substituir o histórico.

## Testes e limites da verificação

A suíte padrão utiliza casos sintéticos e fontes locais artificiais. Não depende de Groq, credenciais ou rede. Testes que precisam da extração original são opcionais e podem aparecer como ignorados quando ela não estiver configurada.

Para habilitar a regressão do tratamento com o CSV original no PowerShell:

```powershell
$env:ECONOMATICA_CASE_CSV = "CAMINHO\economatica.csv"
.venv\Scripts\python -m unittest discover -s tests -v
```

No Linux/macOS:

```bash
ECONOMATICA_CASE_CSV="/caminho/economatica.csv" .venv/bin/python -m unittest discover -s tests -v
```

Essa regressão confere o tratamento e sua repetição; não equivale a testar downloads reais da B3 ou executar uma análise pública completa.

Para conferir a área web isoladamente:

```powershell
.venv\Scripts\python -m unittest discover -s tests -p "test_webapp.py" -v
```

Após editar, rode também `git diff --check`. Mudanças em dados ou regras precisam de testes com casos relevantes; mudanças de layout precisam de inspeção no navegador. Conferir a média histórica não prova, sozinho, que novas extrações funcionem.

## Manutenção da documentação

As oito páginas de uso são publicadas a partir de uma lista explícita em `webapp/documentation.py`. Este roteiro e o registro de decisões são documentação técnica no GitHub; não foram adicionados ao menu público nesta etapa.

Ao mudar uma regra, atualize a decisão, o artigo aplicável e o teste correspondente. Ao mudar uma saída, atualize seus consumidores e o dicionário de campos. Ao documentar limitações, diferencie funcionamento atual e melhorias planejadas.

## Organização da interface e verificações automáticas

O cabeçalho tem uma única fonte em `webapp/templates/header.html`. `webapp/pages.py` compõe as páginas no servidor e marca a navegação ativa. Preserve os identificadores usados pelo JavaScript ao editar esse template.

- `styles.css`: estilos compartilhados, ranking e formulário de nova análise.
- `mobile.css`: composição móvel carregada depois dos estilos de cada página; navegação, ranking compacto, controles por toque, índices persistentes e tabelas com rótulos por campo.
- `documentation.css`: navegação e artigos da documentação.
- `audit.css`: apresentação da auditoria de uma execução.

Edite a regra existente antes de acrescentar outra para o mesmo seletor e propriedade no mesmo contexto. HTML, CSS e JavaScript são formatados com Prettier; Node.js 22 é uma ferramenta de desenvolvimento, sem necessidade no servidor de produção.

```powershell
npm ci --ignore-scripts
npm run format
npm run format:check
npm run check:frontend
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m scripts.verify_artifacts
```

No Linux/macOS, use `.venv/bin/python`. O verificador da interface confere sintaxe JavaScript, interpretação do CSS e declarações sobrescritas no mesmo contexto. Ruff verifica erros essenciais de Python. A conferência dos derivados verifica assinaturas, retornos a partir das pontas, ordenação, top 20 e médias das duas janelas; ela não substitui uma reprodução a partir do CSV bruto.

O workflow `.github/workflows/checks.yml` executa essas verificações em cada envio de código e pull request. Os testes Python rodam em Linux (3.11 e 3.12) e Windows (3.11); a formatação e a sintaxe da interface rodam em Linux com Node 22. A regressão com o bruto original permanece opcional e é ignorada no CI quando a entrada não está disponível.

Uma execução aprovada no CI não verifica downloads reais da B3, o comportamento visual no navegador nem a operação da VPS. Essas conferências continuam necessárias quando a mudança afeta essas áreas. O workflow não publica automaticamente o site.

## Revisão e teste de novas extrações

`webapp/review.py` reaproveita `etl.transform` em lotes e `weekly_ranking.select_week` para conferir datas e cobertura antes da fila. `POST /api/analyses` responde 409 com `short_week_review` quando é necessária revisão, sem manter upload ou criar job. O cliente apresenta datas e exige checkbox; no segundo envio, `allow_nonfriday_end`, `reviewed_sha256` e `reviewed_reference_date` vinculam a aceitação à entrada. A API reconfere o arquivo.

A fila migra bancos existentes acrescentando opções com padrão vazio. O worker passa `--allow-nonfriday-end` somente quando autorizado e grava `analysis_request.json`. Ele executa novamente todos os controles. `submission_details` confere a compatibilidade do registro com o relatório. Mensagens de falha recebem orientação por categoria; a mensagem original permanece visível.

`tests/test_replication.py` executa o worker em subprocesso real com extrações e fontes B3 **artificiais e locais**, sem rede. Os fixtures não devem ser publicados como evidência oficial. A API também é conferida com duas entradas distintas, migração de banco antigo, confirmação invalidada e bloqueios. Uma extração real diferente deve ser conferida em desenvolvimento para verificar aquisição das fontes e apresentação por HTTPS.

### Conferência visual mobile

Confira 320, 390 e 430 px e o desktop antes de publicar alterações de layout. Verifique navegação completa, ausência de sobreposição na introdução, retorno visível no ranking, seleção e volta do gráfico, abertura/fechamento de informações, matriz com datas e ticker fixos, menus e tabelas da documentação, seletor da auditoria e referência brasileira no formulário. Conferência de viewport no navegador não substitui teste em Android e iOS físicos, especialmente para seleção de arquivos e teclado.


## Arquivar a documentação aplicável

Novas análises da interface recebem `documentation_snapshot.json` na conclusão, antes da preparação do resultado. `webapp/doc_revision.py` guarda README e arquivos Markdown de `docs/`, identifica a revisão pelo conteúdo e vincula a cópia à entrada e à assinatura do código do relatório. A API verifica essa correspondência e a integridade dos textos ao ler os guias.

Uma execução pelo comando, ou anterior a esse registro, exige conferência das regras antes da associação:

```powershell
.venv/Scripts/python -m scripts.archive_documentation --run-dir "runs/reproducao-2026-09-22" --reviewed
```

O parâmetro declara que a compatibilidade foi revisada; não faz essa revisão automaticamente. O registro usa `reviewed_after_execution`, informa quando a associação ocorreu e não sobrescreve cópias existentes. A demonstração histórica usa esse modo. Não mude o relatório ou os CSVs para acrescentar documentação.

A auditoria abre `/documentacao/referencia/{assunto}` para os guias associados à referência e `/analise/{id}/documentacao/{assunto}` para uma análise. A busca permanece nos artigos atuais; cópias arquivadas usam o menu de assuntos. `documentation_snapshot.json` é um derivado público permitido, sem dados brutos, endereços IP ou credenciais. O prazo da cópia acompanha o resultado de teste.

Imagens dos guias ficam em `docs/assets/`, com nomes que identificam a versão. Preserve arquivos já referenciados por cópias arquivadas; adicione uma imagem com outro nome quando atualizar exemplos. O site serve as capturas em `/documentation-assets/`. A referência técnica concentra comandos avançados e o dicionário antes presentes no README principal.
