# 📡 Agente de Monitoreo de Noticias — Banco Mundial

Monitoreo automático de noticias sobre el **Grupo Banco Mundial**, **IFC**, **Banco Mundial**, **Ajay Banga**, **Sanaa Abouzaid** y **Elizabeth Martinez Marcano**.

Se ejecuta **3 veces al día** y envía un email con un resumen profesional.

---

## ⚡ Inicio Rápido (15 minutos)

### Paso 1: Crear repositorio en GitHub

1. Ve a [github.com/new](https://github.com/new)
2. Nombre: `news-monitor` (puede ser privado)
3. Crea el repositorio

### Paso 2: Subir los archivos

Sube estos archivos al repositorio manteniendo la estructura:

```
news-monitor/
├── news_monitor.py
├── .github/
│   └── workflows/
│       └── news_monitor.yml
└── README.md
```

Puedes hacerlo arrastrando los archivos en la web de GitHub o con git:

```bash
git clone https://github.com/TU_USUARIO/news-monitor.git
cd news-monitor
# (copia aquí los archivos)
git add .
git commit -m "Setup news monitor"
git push
```

### Paso 3: Configurar credenciales de Gmail

#### 3a. Crear una contraseña de aplicación en Gmail

1. Ve a [myaccount.google.com/security](https://myaccount.google.com/security)
2. Activa la **verificación en 2 pasos** si no la tienes
3. Busca **"Contraseñas de aplicaciones"** (App passwords)
4. Crea una nueva contraseña para "Otra (nombre personalizado)" → `News Monitor`
5. **Copia la contraseña de 16 caracteres** que te genera

#### 3b. Agregar secretos en GitHub

1. Ve a tu repositorio → **Settings** → **Secrets and variables** → **Actions**
2. Crea estos secretos haciendo clic en **New repository secret**:

| Nombre del secreto | Valor |
|---|---|
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `tu_email@gmail.com` |
| `SMTP_PASSWORD` | La contraseña de 16 caracteres del paso 3a |
| `EMAIL_TO` | `destinatario@email.com` (pueden ser varios separados por coma) |

### Paso 4 (Opcional): Agregar NewsAPI

NewsAPI agrega más fuentes de noticias. Es gratis hasta 100 búsquedas/día.

1. Regístrate en [newsapi.org](https://newsapi.org/register)
2. Copia tu API key
3. Agrégala como secreto en GitHub: `NEWSAPI_KEY` → tu key

### Paso 5: Probar

1. Ve a tu repositorio → **Actions** → **📡 News Monitor - Banco Mundial**
2. Clic en **Run workflow** → **Run workflow**
3. Espera ~1 minuto y revisa tu email

---

## 🕐 Horarios de Ejecución

| Ejecución | UTC | México (CST) | Colombia (COT) | España (CET) |
|---|---|---|---|---|
| Mañana | 08:00 | 02:00 | 03:00 | 09:00 |
| Mediodía | 14:00 | 08:00 | 09:00 | 15:00 |
| Noche | 20:00 | 14:00 | 15:00 | 21:00 |

Para cambiar los horarios, edita los valores `cron` en `.github/workflows/news_monitor.yml`.

---

## 🔧 Personalización

### Agregar o quitar términos de búsqueda

Edita el diccionario `SEARCH_TERMS` en `news_monitor.py`:

```python
SEARCH_TERMS = {
    "instituciones": [
        "World Bank Group",
        "Nuevo término aquí",
    ],
    "personas": [
        "Ajay Banga",
        "Nueva persona aquí",
    ],
}
```

### Agregar más idiomas

Modifica la lista `LANGUAGES`:

```python
LANGUAGES = ["en", "es", "fr"]  # Agregar francés
```

### Cambiar frecuencia

Edita el cron en el archivo workflow. Ejemplos:
- Cada hora: `'0 * * * *'`
- Solo días laborales: `'0 8,14,20 * * 1-5'`
- Una vez al día: `'0 14 * * *'`

---

## 💰 Costo

**$0** — GitHub Actions ofrece **2,000 minutos gratis al mes** para repositorios privados. Este agente usa ~1 minuto por ejecución = ~90 minutos/mes.

---

## 🐛 Solución de Problemas

| Problema | Solución |
|---|---|
| No llega el email | Revisa que los secretos estén bien configurados en GitHub |
| Error de autenticación Gmail | Asegúrate de usar una contraseña de aplicación, NO tu contraseña normal |
| Pocos resultados | Agrega `NEWSAPI_KEY` para más fuentes |
| GitHub Actions no se ejecuta | Ve a Actions → verifica que el workflow esté habilitado |

---

## 📄 Licencia

Uso personal/interno. Siéntete libre de modificar y adaptar.
