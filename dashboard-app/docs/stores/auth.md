# Store: auth

**Archivo:** `src/stores/auth.js`

Gestiona la autenticación de usuarios y la lista de usuarios del sistema (mock, sin backend real).

## Estado

| Campo | Tipo | Descripción |
|---|---|---|
| `user` | `object \| null` | Usuario actualmente autenticado (sin campo `password`) |
| `token` | `string \| null` | Token de sesión simulado |
| `allUsers` | `array` | Lista completa de usuarios (cargada desde localStorage) |

## Getters

| Getter | Retorna | Descripción |
|---|---|---|
| `isAuthenticated` | `boolean` | `true` si hay usuario autenticado |
| `isDesigner` | `boolean` | `true` si el rol es `'designer'` |
| `isViewer` | `boolean` | `true` si el rol es `'viewer'` |
| `currentUser` | `object \| null` | Alias de `state.user` |
| `viewers` | `array` | Lista de usuarios con rol `'viewer'` |

## Acciones

### `login(email, password)`

Valida credenciales contra `allUsers`. Si son correctas, guarda el usuario (sin contraseña) y un token simulado en el estado y en `localStorage`.

```javascript
await authStore.login('admin@demo.com', 'admin123')
// Lanza Error('Credenciales incorrectas') si falla
```

### `logout()`

Limpia el estado y elimina `localStorage['auth']`. El router guard redirigirá al login en la próxima navegación.

### `initFromStorage()`

Restaura la sesión desde `localStorage['auth']`. Se llama en `main.js` al iniciar la app.

### `getUserById(id)`

Devuelve el usuario con el ID dado de `allUsers`.

### `updateUserAssignedDashboards(userId, dashboardIds)`

Actualiza los dashboards asignados a un usuario viewer. Persiste en `localStorage['mockUsers']`.

## Usuarios de demo

| ID | Nombre | Email | Rol |
|---|---|---|---|
| 1 | Ana García | admin@demo.com | designer |
| 2 | Carlos López | viewer@demo.com | viewer |
| 3 | María Torres | maria@demo.com | viewer |

## Persistencia

- `localStorage['auth']` → `{ user, token }` — sesión activa
- `localStorage['mockUsers']` → array de usuarios con `assignedDashboards`

## Modelo de usuario

```javascript
{
  id: string,
  name: string,
  email: string,
  role: 'designer' | 'viewer',
  avatar: string,              // iniciales para avatar
  assignedDashboards: string[] // IDs de dashboards asignados
}
```
