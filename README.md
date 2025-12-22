
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

<img width="800" height="533" alt="image" src="https://github.com/user-attachments/assets/6912bda6-3506-4fc6-bf04-83e73faa49fc" />


