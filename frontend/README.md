# Bizio Frontend

Frontend приложение для Bizio CRM, построенное на React + TypeScript + Vite.

## Установка

```bash
cd frontend
npm install
```

## Запуск

```bash
npm run dev
```

Приложение будет доступно по адресу `http://localhost:3000`

## Сборка для продакшена

```bash
npm run build
```

## Структура проекта

```
frontend/
├── src/
│   ├── api/           # API клиент для работы с backend
│   ├── components/    # React компоненты
│   ├── pages/         # Страницы приложения
│   ├── types.ts       # TypeScript типы
│   ├── App.tsx        # Главный компонент
│   └── main.tsx       # Точка входа
├── package.json
└── vite.config.ts     # Конфигурация Vite
```

## API

Frontend использует proxy для запросов к backend API. Все запросы к `/api/*` проксируются на `http://localhost:8000` (настраивается в `vite.config.ts`).

## Особенности

- **Deals Page**: Страница со списком сделок
- **Create Deal Modal**: Модальное окно для создания новой сделки
- Автоматическое создание клиента при создании сделки (если не выбран существующий)
- Поддержка выбора существующих организаций и контактов
- Полная интеграция с backend API

## Требования

- Node.js 18+
- Backend должен быть запущен на `http://localhost:8000`


