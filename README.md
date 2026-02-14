
<h1>Real-Time Translator</h1> 

## Descrição

Programa de desktop em Python que captura áudio do microfone, converte voz em texto em tempo real (STT), traduz de inglês para português e exibe a tradução dinamicamente na tela. Ideal para quem precisa de tradução simultânea em reuniões, aulas ou conversas.

---

## Funcionalidades

* Captura contínua de áudio do microfone
* Reconhecimento de voz em tempo real (STT)
* Tradução automática de inglês para português
* Exibição dinâmica do texto traduzido em uma interface gráfica
* Modular e escalável (módulos separados para áudio, STT, tradução e UI)
* Configurações fáceis de alterar (idioma, APIs, latência)

---

## Estrutura do Projeto

```
real_time_translator/
╭─ main.py                  # Ponto de entrada, coordena todos os módulos
│
├─ audio/ 📁
│   ├─ capture.py            # Classe: AudioCapture → captura de áudio do microfone
│   └─ utils.py              # Funções auxiliares de manipulação de áudio
│
├─ stt/ 📁
│   ├─ whisper_stream.py     # Classe: WhisperSTT → transforma áudio em texto em tempo real
│   └─ provider.py           # Integração com diferentes STT providers (Whisper, Google, Azure)
│
├─ translation/ 📁
│   ├─ translator.py         # Classe: Translator → recebe texto do STT e traduz
│   └─ provider.py           # Integração com APIs de tradução (GPT, DeepL, Google Translate)
│
├─ ui/ 📁
│   ├─ window.py             # Classe: MainWindow → interface gráfica principal
│   └─ widgets.py            # Widgets da interface (Labels, TextBoxes, Botões)
│
├─ config.py                 # Configurações gerais (chaves API, idiomas, latência)
└─ requirements.txt          # Dependências Python
```

---

## Instalação

1. Clone o repositório:

```bash
git clone <repo_url>
cd real_time_translator
```

2. Crie um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Uso

1. Configure suas chaves API em `config.py`
2. Execute o programa:

```bash
python main.py
```

3. A interface abrirá e começará a capturar áudio automaticamente
4. O texto reconhecido e traduzido aparecerá em tempo real na tela

---

## Observações

* Latência mínima é obtida com **streaming e blocos curtos de áudio**
* STT e tradução funcionam melhor com conexões de internet estáveis
* Pode ser expandido para múltiplos idiomas, TTS ou gravação de histórico
* Modularidade facilita troca de serviços STT ou APIs de tradução sem alterar UI

---

## Execução Rápida (Mac/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Se o microfone padrão não for o correto, ajuste em:
`real_time_translator/audio/capture.py` no `device_index`.

## Modo Visual (Web, recomendado)

Rodar interface com botões no navegador:

```bash
python main_web.py
```

Abrir:

`http://127.0.0.1:7860`

Botões disponíveis:
- `Permitir Microfone` (dispara pedido de permissão no macOS)
- `Iniciar`
- `Parar`
- `Limpar`
- `Atualizar`
- `Aplicar Sensibilidade` (auto/manual)
- `Recalibrar Ambiente` (isolar melhor ruído de TV/fundo)

Listar microfones:

```bash
python main_web.py --list-mics
```

Escolher microfone:

```bash
python main_web.py --mic-index 1
```

### Dica para ruído de fundo (TV)
1. Deixe em `manual`.
2. Comece com `Threshold manual` entre `800` e `1300`.
3. Clique `Recalibrar Ambiente` com você em silêncio por 1-2s.
4. Clique `Iniciar` e teste.

## Modo Produto (Desktop)

Executar interface desktop guiada (sem navegador):

```bash
python main_desktop.py
```

Ou com um clique:

```bash
./run_desktop.command
```

Fluxo recomendado para usuário final:
1. `Permitir Microfone`
2. `Auto Detectar` (microfone)
3. `Testar Microfone` (nível)
4. `Iniciar`

## Build instalável macOS (.app)

```bash
./scripts/build_macos_app.sh
```

Saída:
- `dist/RealTranslator.app`

No primeiro uso, o macOS vai pedir permissão de microfone.

<img width="800" height="533" alt="image" src="https://github.com/user-attachments/assets/6912bda6-3506-4fc6-bf04-83e73faa49fc" />
