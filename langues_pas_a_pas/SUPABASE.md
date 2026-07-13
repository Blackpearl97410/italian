# Configuration Supabase

Projet cible:

```text
https://supabase.com/dashboard/project/eyydmtlknpvvezfyyexb
```

## 1. Creer les tables

Dans Supabase Dashboard, ouvrir `SQL Editor`, puis executer le contenu de:

```text
../supabase/migrations/20260713090000_langues_pas_a_pas_auth_state.sql
```

Le script cree:

- `profiles`: profil public minimal rattache a `auth.users`;
- `user_state`: progression, reponses, revisions et imports sous forme JSON;
- Row Level Security pour que chaque utilisateur ne voie que ses propres donnees.

## 2. Activer email/password

Dans `Authentication > Providers`, verifier que `Email` est active.

Pour un premier test plus fluide, tu peux desactiver temporairement la confirmation email dans
`Authentication > Sign In / Providers > Email`, puis la reactiver plus tard.

Toujours dans `Authentication > Sign In / Providers > Email`, verifier aussi que les
inscriptions email sont autorisees. Dans la config Supabase, cela correspond a:

```toml
[auth.email]
enable_signup = true
```

Si ce reglage est desactive, l'app affiche `Email signups are disabled` et aucun
nouveau compte ne peut etre cree depuis le formulaire.

## 3. Renseigner la cle anon

Dans `Project Settings > API`, copier la cle `anon public`, puis modifier:

```text
web_preview/supabase-config.js
```

Exemple:

```js
window.LPP_SUPABASE = {
  url: "https://eyydmtlknpvvezfyyexb.supabase.co",
  anonKey: "eyJ...",
};
```

Ne jamais mettre la cle `service_role` dans l'application web.

## 4. Lancer

```bash
python3 -m http.server 8765
```

Puis ouvrir:

```text
http://localhost:8765/web_preview/
```

Si la cle anon n'est pas renseignee, l'app reste en mode local.
