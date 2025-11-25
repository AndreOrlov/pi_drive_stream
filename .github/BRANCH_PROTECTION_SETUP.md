# Настройка Branch Protection Rules

Эта инструкция для настройки защиты веток `master` и `dev` в GitHub.

## Шаг 1: Перейти в настройки репозитория

1. Откройте репозиторий на GitHub
2. Перейдите в **Settings** (вкладка вверху)
3. В левом меню выберите **Branches**

## Шаг 2: Настроить защиту для `master`

1. Нажмите **Add branch protection rule**
2. В поле **Branch name pattern** введите: `master`

### Включите следующие опции:

#### ✅ Require a pull request before merging
- [x] Require approvals: **1**
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require review from Code Owners (опционально)

#### ✅ Require status checks to pass before merging
- [x] Require branches to be up to date before merging
- **Status checks that are required:**
  - `test` (из GitHub Actions)
  - `build-check` (из GitHub Actions)

#### ✅ Require conversation resolution before merging
- [x] Включить

#### ✅ Require linear history (опционально)
- [x] Включить (запрещает merge commits, только rebase/squash)

#### ✅ Do not allow bypassing the above settings
- [ ] **НЕ включать** (чтобы вы могли коммитить напрямую)

#### ✅ Restrict who can push to matching branches
- [x] Включить
- Добавьте свой username в список разрешённых

#### ✅ Allow force pushes
- [ ] **НЕ включать**

#### ✅ Allow deletions
- [ ] **НЕ включать**

3. Нажмите **Create** или **Save changes**

## Шаг 3: Настроить защиту для `dev`

1. Нажмите **Add branch protection rule** снова
2. В поле **Branch name pattern** введите: `dev`

### Включите следующие опции:

#### ✅ Require a pull request before merging
- [x] Require approvals: **0** (для dev можно без review)

#### ✅ Require status checks to pass before merging
- [x] Require branches to be up to date before merging
- **Status checks that are required:**
  - `test`
  - `build-check`

#### ✅ Restrict who can push to matching branches
- [x] Включить
- Добавьте свой username в список разрешённых

3. Нажмите **Create**

## Шаг 4: Проверка

После настройки:

1. Создайте тестовую ветку:
   ```bash
   git checkout -b test/branch-protection
   echo "test" > test.txt
   git add test.txt
   git commit -m "test: проверка branch protection"
   git push origin test/branch-protection
   ```

2. Создайте PR в `dev` на GitHub

3. Убедитесь, что:
   - GitHub Actions запустились автоматически
   - Кнопка **Merge** заблокирована до прохождения проверок
   - После прохождения проверок кнопка становится активной

## Результат

✅ **Для всех пользователей (кроме вас):**
- Невозможен прямой push в `master` и `dev`
- Обязателен PR с прохождением всех проверок
- Для `master` требуется review

✅ **Для вас (maintainer):**
- Можете коммитить напрямую в `master` и `dev`
- Можете мерджить PR даже если проверки не прошли (не рекомендуется)

## Дополнительно: Настройка Codecov (опционально)

Если хотите отслеживать покрытие кода:

1. Зарегистрируйтесь на https://codecov.io
2. Подключите репозиторий
3. Скопируйте токен
4. Добавьте секрет в GitHub:
   - Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `CODECOV_TOKEN`
   - Value: ваш токен

Workflow уже настроен на отправку coverage в Codecov.
