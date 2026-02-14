# Tradutor em Tempo Real (EN -> PT)

Aplicação para transcrever inglês e traduzir para português em tempo real, com interface Web e memória de correções.

## Instalação em 1 comando (GitHub)

No macOS/Linux, rode:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Mauricio-HNS/Real-translator/main/scripts/install_and_run.sh)"
```

O comando:
- clona/atualiza o projeto,
- cria `.venv`,
- instala dependências,
- inicia o servidor Web.

Depois, abra no navegador:
- `http://127.0.0.1:7892`

## Instalação manual

```bash
cd "/Users/mauriciohenrique/Documents/New project/Real-translator"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main_web.py --host 127.0.0.1 --port 7892
```

## Como usar

1. Clique `LIGAR`.
2. Clique `CALIBRAR` e fique em silêncio por ~2s.
3. Fale em inglês.
4. Veja a frase completa em `Inglês` e a tradução em `Português`.

Parar:
- `Ctrl + C` no terminal.

## Como o programa aprende com usuários

A interface tem:
- `Aprender Inglês (opcional)`
- `Tradução PT preferida (opcional)`
- botão `Aprender correção`

Quando você salva correções, elas ficam no banco local:
- `learning_memory.db`

Nas próximas falas, o sistema reaproveita essas correções automaticamente.

## “Aprender com a internet”

O projeto não faz aprendizado automático irrestrito da internet (isso é inseguro e pode degradar qualidade).

Forma recomendada:
- atualizar o app periodicamente com:

```bash
git pull
```

- manter melhorias/correções no repositório (histórico versionado e auditável).

## STT (fala -> texto)

Estratégia híbrida:
- `faster-whisper` local (principal)
- Google Speech Recognition (fallback)

O backend ativo aparece no log ao iniciar.

## Comandos úteis

Listar microfones:

```bash
python main_web.py --list-mics
```

Selecionar microfone:

```bash
python main_web.py --mic-index 0 --host 127.0.0.1 --port 7892
```

Porta diferente:

```bash
python main_web.py --host 127.0.0.1 --port 7893
```

## Build app macOS (.app)

```bash
./scripts/build_macos_app.sh
```

Saída:
- `dist/RealTranslator.app`

## Estrutura principal

```text
main_web.py
main_desktop.py
scripts/
  install_and_run.sh
  build_macos_app.sh
real_time_translator/
  app_controller.py
  config.py
  audio/capture.py
  stt/provider.py
  translation/provider.py
  ui/web_app.py
  learning/memory.py
```

## Troubleshooting rápido

- Não reconhece fala:
  - `CALIBRAR` em silêncio por 2s.
  - confirme permissões de microfone do Terminal/Python no macOS.
- Porta ocupada:
  - troque para `--port 7893`.
- Ambiente virtual:
  - rode `source .venv/bin/activate`.
