# 🔐 OAuth Setup Guide

## Проблема
При попытке входа через Google или Discord появлялись ошибки:
- **Google**: `Ошибка 400: invalid_request, flowName=GeneralOAuthFlow`
- **Discord**: `Значение «» не является snowflake`

## Решение

### 1. Проверка конфигурации OAuth

**Backend** теперь проверяет наличие клиентских ID перед началом OAuth flow:

```python
@router.get("/google/login")
async def google_login(request: Request, response: Response):
    # Check if Google OAuth is configured
    if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "your_google_client_id":
        frontend_url = f"{settings.FRONTEND_URL}/auth/callback?provider=google&error=not_configured&message=Google OAuth is not configured"
        return RedirectResponse(url=frontend_url)
```

### 2. Новый endpoint для проверки конфигурации

```
GET /api/v1/oauth/config

Response:
{
    "google_configured": false,
    "discord_configured": false
}
```

### 3. Frontend проверки

**AuthModal** автоматически проверяет конфигурацию при открытии:
- Если OAuth не настроен → кнопки скрыты
- Показывается предупреждение: "⚠️ OAuth is not configured..."

**OAuthCallback** обрабатывает ошибки конфигурации:
- Показывает понятное сообщение об ошибке
- Предлагает использовать username/password login

## Как настроить OAuth

### Google OAuth

1. **Создайте проект в Google Cloud Console:**
   - Перейдите на https://console.cloud.google.com/
   - Создайте новый проект или выберите существующий

2. **Включите Google+ API:**
   - API & Services → Library
   - Найдите "Google+ API" и включите

3. **Создайте OAuth 2.0 Client ID:**
   - API & Services → Credentials
   - Create Credentials → OAuth 2.0 Client ID
   - Application type: Web application

4. **Настройте Authorized redirect URIs:**
   ```
   http://localhost:8000/api/v1/oauth/google/callback
   ```

5. **Скопируйте Client ID и Client Secret:**
   - Client ID: `xxxxxxxx.apps.googleusercontent.com`
   - Client Secret: `xxxxxxxxxxxxxxx`

6. **Добавьте в .env:**
   ```env
   GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxxxxxxxxxxxxx
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback
   ```

### Discord OAuth

1. **Создайте приложение в Discord Developer Portal:**
   - Перейдите на https://discord.com/developers/applications
   - New Application → Введите название

2. **Перейдите в раздел OAuth2:**
   - Скопируйте Client ID
   - Создайте Client Secret (Copy)

3. **Настройте Redirect URI:**
   ```
   http://localhost:8000/api/v1/oauth/discord/callback
   ```

4. **Добавьте в .env:**
   ```env
   DISCORD_CLIENT_ID=123456789012345678
   DISCORD_CLIENT_SECRET=xxxxxxxxxxxxxxx
   DISCORD_REDIRECT_URI=http://localhost:8000/api/v1/oauth/discord/callback
   ```

## Проверка настройки

### 1. Проверьте .env файл

```env
# Должно быть заполнено
GOOGLE_CLIENT_ID=123456789-xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback

DISCORD_CLIENT_ID=123456789012345678
DISCORD_CLIENT_SECRET=xxxxxxxx
DISCORD_REDIRECT_URI=http://localhost:8000/api/v1/oauth/discord/callback
```

### 2. Проверьте через API

```bash
curl http://localhost:8000/api/v1/oauth/config
```

**Ожидаемый ответ (если настроено):**
```json
{
    "google_configured": true,
    "discord_configured": true
}
```

**Если не настроено:**
```json
{
    "google_configured": false,
    "discord_configured": false
}
```

### 3. Проверьте в браузере

1. Откройте http://localhost:8000
2. Нажмите "Sign In" или "Get Started"
3. Если OAuth настроен → видите кнопки Google и Discord
4. Если не настроен → видите предупреждение и только Guest кнопку

## Измененные файлы

### Backend
- `backend/src/api/routers/oauth.py`
  - Добавлен endpoint `/config`
  - Проверка конфигурации в `/google/login`
  - Проверка конфигурации в `/discord/login`

### Frontend
- `frontend/src/components/AuthModal.tsx`
  - Проверка конфигурации при монтировании
  - Условный рендеринг OAuth кнопок
  - Показ предупреждения

- `frontend/src/components/AuthModal.css`
  - Стили для `.oauth-notice`

- `frontend/src/components/OAuthCallback.tsx`
  - Обработка ошибок конфигурации

## Поведение

### Если OAuth настроен:
```
┌─────────────────────────────────────┐
│  or continue with                   │
├─────────────────────────────────────┤
│  [🔵 Continue with Google]          │
│  [🟣 Continue with Discord]         │
│  [🎭 Continue as Guest]             │
└─────────────────────────────────────┘
```

### Если OAuth не настроен:
```
┌─────────────────────────────────────┐
│  or continue with                   │
├─────────────────────────────────────┤
│  ⚠️ OAuth is not configured.        │
│     Please use username/password    │
│     or guest login.                 │
│  [🎭 Continue as Guest]             │
└─────────────────────────────────────┘
```

## Коммиты

✅ `fix:OAuth-config-check-and-graceful-handling`

## Результат

✅ OAuth кнопки скрыты если не настроены  
✅ Показывается понятное предупреждение  
✅ Backend возвращает ошибку с редиректом  
✅ Frontend обрабатывает ошибки gracefully  
✅ Username/password и Guest login работают всегда  

**Теперь OAuth не сломается если не настроен! 🎉**
