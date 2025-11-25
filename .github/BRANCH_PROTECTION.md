# Branch Protection Rules Setup

Настройка защиты веток для репозитория pi_drive_stream.

## Как настроить

1. Перейдите в **Settings** → **Branches** → **Add branch protection rule**

## Правила для `master`

### Pattern: `master`

**Protect matching branches:**
- ✅ **Require a pull request before merging**
  - Require approvals: **1**
  - Dismiss stale pull request approvals when new commits are pushed
  - Require review from Code Owners (optional)

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Status checks that are required:
    - `test`
    - `lint-check`

- ✅ **Require conversation resolution before merging**

- ✅ **Require signed commits** (optional, но рекомендуется)

- ✅ **Require linear history** (optional, для чистой истории)

- ✅ **Do not allow bypassing the above settings**
  - Исключение: только владелец репозитория

- ✅ **Restrict who can push to matching branches**
  - Add people or teams: `ваш_github_username`
  - Только вы сможете коммитить напрямую в master

- ✅ **Allow force pushes**
  - Specify who can force push: `ваш_github_username`
  - Только для экстренных случаев

## Правила для `dev`

### Pattern: `dev`

**Protect matching branches:**
- ✅ **Require a pull request before merging**
  - Require approvals: **0** (можно мержить свои PR)
  - Dismiss stale pull request approvals when new commits are pushed

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Status checks that are required:
    - `test`
    - `lint-check`

- ✅ **Restrict who can push to matching branches**
  - Add people or teams: `ваш_github_username`
  - Только вы сможете коммитить напрямую в dev

- ✅ **Allow force pushes**
  - Specify who can force push: `ваш_github_username`

## Workflow

### Для вас (владелец):
```bash
# Можете коммитить напрямую
git checkout dev
git add .
git commit -m "feat: add feature"
git push origin dev

# Или через PR (рекомендуется для больших изменений)
git checkout -b feature/new-feature
git push origin feature/new-feature
# Создать PR в GitHub
```

### Для других разработчиков:
```bash
# Только через PR
git checkout -b feature/my-feature
git push origin feature/my-feature
# Создать PR в GitHub → dev или master
# Дождаться прохождения CI (test + lint-check)
# Дождаться review (для master)
# Merge
```

## Проверка статуса

После настройки:
1. Создайте тестовый PR
2. Убедитесь, что CI запустился
3. Проверьте, что кнопка Merge заблокирована до прохождения тестов
4. Попробуйте запушить напрямую в dev/master (должно работать только для вас)

## Troubleshooting

### CI не запускается
- Проверьте, что файл `.github/workflows/ci.yml` в репозитории
- Проверьте вкладку **Actions** в GitHub

### Не могу мержить PR
- Проверьте статус CI (должен быть зелёным)
- Проверьте, что все conversations resolved (для master)
- Проверьте, что ветка обновлена (rebase/merge с target веткой)

### Хочу обойти защиту
- Временно отключите branch protection rule
- Или добавьте себя в исключения ("Allow specified actors to bypass")
