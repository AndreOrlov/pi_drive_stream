# Быстрая настройка CI/CD

## Что уже сделано ✅

1. ✅ GitHub Actions workflow (`.github/workflows/ci.yml`)
2. ✅ Pre-commit hooks (`.pre-commit-config.yaml`)
3. ✅ Ruff конфигурация (`ruff.toml`)
4. ✅ Все тесты проходят (22/22)
5. ✅ Код соответствует стандартам (ruff check passed)

## Что нужно сделать

### 1. Запушить изменения в GitHub

```bash
git add .
git commit -m "ci: add GitHub Actions workflow and pre-commit hooks"
git push origin dev
```

### 2. Настроить Branch Protection Rules

Перейдите в **Settings** → **Branches** → **Add branch protection rule**

#### Для ветки `master`:

**Branch name pattern:** `master`

Включите:
- ✅ Require a pull request before merging
  - Required approvals: **1**
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date
  - Status checks: `test`, `lint-check`
- ✅ Require conversation resolution before merging
- ✅ Restrict who can push to matching branches
  - Add: `ваш_github_username`

#### Для ветки `dev`:

**Branch name pattern:** `dev`

Включите:
- ✅ Require a pull request before merging
  - Required approvals: **0**
- ✅ Require status checks to pass before merging
  - Status checks: `test`, `lint-check`
- ✅ Restrict who can push to matching branches
  - Add: `ваш_github_username`

### 3. (Опционально) Установить pre-commit hooks локально

```bash
pip install pre-commit
pre-commit install

# Проверить работу
pre-commit run --all-files
```

## Проверка

После настройки:

1. Создайте тестовую ветку:
```bash
git checkout -b test/ci-check
echo "# Test" >> test.md
git add test.md
git commit -m "test: check CI"
git push origin test/ci-check
```

2. Создайте Pull Request в GitHub (dev или master)

3. Убедитесь, что:
   - ✅ CI автоматически запустился
   - ✅ Проверки `test` и `lint-check` прошли
   - ✅ Кнопка Merge доступна только после прохождения проверок

4. Попробуйте запушить напрямую в `dev`:
```bash
git checkout dev
git merge test/ci-check
git push origin dev
```
Должно работать (вы — владелец).

5. Попросите коллегу попробовать запушить напрямую — должно быть запрещено.

## Что проверяет CI

### Job: `test`
1. Устанавливает зависимости
2. Запускает `ruff check` (линтер)
3. Запускает `mypy` (type checker, warnings only)
4. Запускает `pytest` с coverage

### Job: `lint-check`
1. Проверяет форматирование кода (`ruff format --check`)

## Локальная проверка перед push

```bash
# Линтер
ruff check app/ tests/

# Автоисправление
ruff check app/ tests/ --fix

# Форматирование
ruff format app/ tests/

# Тесты
pytest tests/ -v

# Всё вместе (как в CI)
ruff check app/ tests/ && pytest tests/ -v
```

## Troubleshooting

### CI не запускается
- Проверьте, что файл `.github/workflows/ci.yml` в репозитории
- Проверьте вкладку **Actions** в GitHub (может быть отключена)

### Тесты падают в CI, но локально проходят
- Проверьте версию Python (CI использует 3.11)
- Проверьте зависимости в `requirements.txt`

### Не могу мержить PR
- Убедитесь, что все проверки зелёные
- Убедитесь, что ветка обновлена (rebase/merge с target)
- Для master: убедитесь, что есть approval

### Хочу обойти защиту
- Временно отключите branch protection rule
- Или добавьте себя в "Allow specified actors to bypass"
- **Не рекомендуется** для production
