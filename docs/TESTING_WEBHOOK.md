# 🧪 Guide de Test des Webhooks

Ce guide explique comment tester les webhooks Bitbucket localement avec signature HMAC.

## Prérequis

```bash
# Démarrer l'app en mode DEBUG pour accéder aux endpoints de test
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload
```

L'app démarre sur `http://localhost:8000`

Accédez à Swagger : **http://localhost:8000/docs**

## 📋 Vue d'ensemble

L'app dispose de **3 endpoints** pour les webhooks :

| Endpoint | Méthode | Objectif |
|----------|---------|----------|
| `/api/webhook` | `POST` | ✅ Webhook Bitbucket principal (production) |
| `/api/test/webhook/generate-payload` | `POST` | 🧪 Génère un payload de test avec signature |
| `/api/test/webhook/send` | `POST` | 🧪 Envoie un webhook de test directement |

---

## Option 1️⃣ : Via Swagger UI (le plus facile!)

### Étape 1 : Accéder à Swagger

Ouvrez : **http://localhost:8000/docs**

### Étape 2 : Générer un payload de test

1. Scroll vers le bas → **Testing** section
2. Ouvre **POST `/api/test/webhook/generate-payload`**
3. Clique sur "Try it out"
4. Remplace le payload par défaut (optionnel) :

```json
{
  "eventKey": "pr:merged",
  "project_key": "PROJ",
  "repo_slug": "my-repo",
  "pr_id": 123,
  "merge_commit": "abc123def456abc123def456abc123def456"
}
```

5. Clique sur "Execute"
6. Récupère la réponse :
   - `payload`: Le JSON complet
   - `signature`: Signature HMAC valide
   - `curl_command`: Prêt à copier/coller

### Étape 3 : Tester le webhook

#### Via Swagger (le plus simple)

1. Ouvre **POST `/api/test/webhook/send`**
2. Clique "Try it out"
3. Configure le test :

```json
{
  "payload": {
    "eventKey": "pr:merged",
    "project_key": "PROJ",
    "repo_slug": "my-repo",
    "pr_id": 123,
    "merge_commit": "abc123def456abc123def456abc123def456"
  },
  "use_signature": true,
  "invalid_signature": false
}
```

4. Clique "Execute"
5. Regarde la réponse et les logs

#### Test avec signature invalide (pour valider la sécurité)

Utilise le même endpoint avec `"invalid_signature": true` pour vérifier que la validation fonctionne !

---

## Option 2️⃣ : Via Terminal (curl)

### Méthode A : Avec signature valide (sécurisé)

```bash
# 1. Générer la signature
SECRET="mon_secret_teste"
PAYLOAD='{"eventKey":"pr:merged","pullRequest":{"id":123,"toRef":{"repository":{"project":{"key":"PROJ"},"slug":"my-repo"}},"properties":{"mergeCommit":{"id":"abc123def456"}}}}'

SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -hex | cut -d' ' -f2)

# 2. Envoyer le webhook
curl -X POST http://localhost:8000/api/webhook \
  -H "Content-Type: application/json" \
  -H "x-hub-signature: sha256=$SIGNATURE" \
  -d "$PAYLOAD"
```

### Méthode B : Sans signature (mode développement)

```bash
# Si BITBUCKET_WEBHOOK_SECRET n'est pas défini en .env

PAYLOAD='{"eventKey":"pr:merged","pullRequest":{"id":123,"toRef":{"repository":{"project":{"key":"PROJ"},"slug":"my-repo"}},"properties":{"mergeCommit":{"id":"abc123def456"}}}}'

curl -X POST http://localhost:8000/api/webhook \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
```

### Méthode C : Test de sécurité (signature invalide)

```bash
# Doit retourner 401 Unauthorized

PAYLOAD='{"eventKey":"pr:merged","pullRequest":{"id":123,"toRef":{"repository":{"project":{"key":"PROJ"},"slug":"my-repo"}},"properties":{"mergeCommit":{"id":"abc123def456"}}}}'

curl -X POST http://localhost:8000/api/webhook \
  -H "Content-Type: application/json" \
  -H "x-hub-signature: sha256=invalid0000000000000000000000000000000000000000000000000000" \
  -d "$PAYLOAD"
```

**Résultat attendu** :
```json
{
  "detail": "Unauthorized: Invalid webhook signature"
}
```

---

## 🔒 Scénarios de Test de Sécurité

### Scénario 1 : Webhook sans signature (mode dev)

**Condition** : `BITBUCKET_WEBHOOK_SECRET` vide ou absent en `.env`

```bash
# ✅ Doit accepter
curl -X POST http://localhost:8000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"eventKey":"pr:merged",...}'
```

**Résultat** : 
```json
{"status": "accepted", "details": {...}}
```

### Scénario 2 : Webhook avec signature valide

**Condition** : `BITBUCKET_WEBHOOK_SECRET="mon_secret"` en `.env`

```bash
# ✅ Doit accepter
curl -X POST http://localhost:8000/api/webhook \
  -H "x-hub-signature: sha256=<VALID_SIGNATURE>" \
  -d '{"eventKey":"pr:merged",...}'
```

### Scénario 3 : Webhook avec signature invalide

```bash
# ❌ Doit rejeter avec 401
curl -X POST http://localhost:8000/api/webhook \
  -H "x-hub-signature: sha256=invalid000000000000" \
  -d '{"eventKey":"pr:merged",...}'
```

**Résultat** :
```json
{"detail": "Unauthorized: Invalid webhook signature"}
```

### Scénario 4 : Webhook sans header signature (secret configuré)

```bash
# ❌ Doit rejeter avec 401
curl -X POST http://localhost:8000/api/webhook \
  -d '{"eventKey":"pr:merged",...}'
```

**Résultat** :
```json
{"detail": "Unauthorized: Missing webhook signature"}
```

---

## 📊 Vérification des Logs

Quand tu testes, regarde la console pour :

```
✅ Webhook signature verified successfully
   → Signature HMAC valide

🚨 Webhook signature mismatch - possible tampering detected
   → Signature invalide ou payload modifié

🚨 Missing x-hub-signature header - possible attack attempt
   → En production, c'est important !

⚠️  BITBUCKET_WEBHOOK_SECRET not configured - webhook signature verification DISABLED
   → Mode développement, pas de sécurité
```

---

## 🔑 Configuration en Production

### Sur Bitbucket

1. Repo Settings → Webhooks
2. Créer/modifier webhook
3. Dans la section "Secret", entrer un secret fort :
   - Minimum 32 caractères
   - Caractères aléatoires
   - Peut contenir lettres, chiffres, symboles

### Sur le serveur

1. Copier le secret de Bitbucket
2. Ajouter à `.env` :
   ```env
   BITBUCKET_WEBHOOK_SECRET=your_secret_from_bitbucket
   ```
3. **Jamais** commiter `.env` !
4. Redémarrer l'app

---

## 🐛 Troubleshooting

### "Missing webhook signature" (mais j'ai défini le header!)

**Cause** : Format incorrect du header

**Format correct** : `sha256=abcd1234...`

```bash
# ❌ Mauvais
-H "x-hub-signature: abcd1234"

# ✅ Correct
-H "x-hub-signature: sha256=abcd1234"
```

### "Webhook signature mismatch"

**Cause 1** : Secret différent entre Bitbucket et `.env`

**Cause 2** : Payload modifié après génération de la signature

**Vérification** :
```bash
# Faire correspondre exactement
echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -hex
```

### Endpoint `/api/test/webhook/*` non disponible

**Cause** : `LOG_LEVEL` n'est pas `DEBUG`

**Solution** :
```bash
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload
```

---

## 📝 Checklist de Test Complet

- [ ] Test sans signature (mode dev) → Accept
- [ ] Test avec signature valide → Accept
- [ ] Test avec signature invalide → Reject (401)
- [ ] Test sans header signature (secret configuré) → Reject (401)
- [ ] Vérifier les logs pour chaque test
- [ ] Tester via Swagger
- [ ] Tester via curl
- [ ] Tester en production avec vrai secret

---

## 💡 Tips

1. **Copie les payloads depuis Swagger** - Plus facile que de les écrire manuellement
2. **Utilise le `curl_command` généré** - Prêt à l'emploi
3. **Teste la sécurité d'abord** - Vérifie que les signatures invalides sont rejetées
4. **Regarde toujours les logs** - Les détails y sont
5. **En production**, toujours définir `BITBUCKET_WEBHOOK_SECRET`
