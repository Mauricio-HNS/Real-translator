# Real Translator

Tradutor de voz em tempo real (EN -> PT) com duas frentes:
- App Web (uso final)
- API SaaS (integração para empresas, cobrança mensal)

## 1) Rodar o App Web

### Instalação rápida (macOS/Linux)

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Mauricio-HNS/Real-translator/main/scripts/install_and_run.sh)"
```

Abre em:
- `http://127.0.0.1:7892`

### Instalação manual

```bash
cd "/Users/mauriciohenrique/Documents/New project/Real-translator"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main_web.py --host 127.0.0.1 --port 7892
```

## 2) API SaaS (mensal)

Backend para empresas enviarem texto e receberem tradução com controle de uso mensal.

### Subir API local

```bash
cd "/Users/mauriciohenrique/Documents/New project/Real-translator"
source .venv/bin/activate
pip install -r requirements.txt
uvicorn saas_api.app:app --host 0.0.0.0 --port 8080 --reload
```

Swagger:
- `http://127.0.0.1:8080/docs`

### Variáveis de ambiente

```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
export RT_API_DB_URL="sqlite:///./saas_api.db"
```

### Endpoints principais

- `POST /v1/admin/companies`
  - cria empresa, assinatura e API key
- `POST /v1/translate`
  - traduz texto com autenticação por `X-API-Key`
- `GET /v1/usage`
  - retorna consumo mensal
- `POST /v1/billing/stripe/webhook`
  - sincroniza status da assinatura com Stripe

### Exemplo de criação de empresa

```bash
curl -X POST "http://127.0.0.1:8080/v1/admin/companies" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "email": "billing@acme.com",
    "plan_code": "business"
  }'
```

### Exemplo de tradução

```bash
curl -X POST "http://127.0.0.1:8080/v1/translate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rt_..." \
  -d '{
    "text": "Good morning, how are you?",
    "source": "en",
    "target": "pt",
    "estimated_minutes": 1
  }'
```

## 3) Android e iOS

Para Android/iOS, o app mobile não precisa rodar STT localmente no início.
Fluxo recomendado:
- Captura áudio no celular
- Converte para texto (STT local ou API externa)
- Envia texto para `POST /v1/translate`
- Exibe tradução ao usuário

Ou seja: o backend já está pronto para integração mobile via HTTP.

## 4) Virar programa instalável

### macOS (.app)

```bash
./scripts/build_macos_app.sh
```

Saída:
- `dist/RealTranslator.app`

## 5) Aprendizado com usuários

O app web salva correções locais em:
- `learning_memory.db`

Assim ele melhora frases recorrentes no próprio ambiente do usuário.

## 6) Estrutura

```text
main_web.py
main_desktop.py
saas_api/
  app.py
  config.py
  db.py
  models.py
  schemas.py
  service.py
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
