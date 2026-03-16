"""
Agente de Monitoreo de Noticias - Grupo Banco Mundial & Personas Clave
======================================================================
Ejecuta búsquedas en Google News RSS y NewsAPI, genera un resumen
y lo envía por email (compatible con Gmail SMTP).

Ejecución: 3 veces al día vía GitHub Actions (8:00, 14:00, 20:00 UTC)
"""

import os
import re
import json
import smtplib
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen, Request
from urllib.parse import quote_plus
from xml.etree import ElementTree
from html import unescape

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────

SEARCH_TERMS = {
    "instituciones": [
        "World Bank Group",
        "Grupo Banco Mundial",
        "IFC International Finance Corporation",
        "World Bank",
        "Banco Mundial",
    ],
    "personas": [
        "Sanaa Abouzaid",
        "Elizabeth Martinez Marcano",
        "Ajay Banga",
    ],
}

LANGUAGES = ["en", "es"]

# Variables de entorno (configurar en GitHub Secrets)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")  # App password de Gmail
EMAIL_TO = os.environ.get("EMAIL_TO", "")  # Destinatario(s), separados por coma
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")  # Opcional, mejora resultados

# ─── LOGGING ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("news_monitor")

# ─── FUNCIONES DE BÚSQUEDA ───────────────────────────────────────────────────


def fetch_url(url: str, timeout: int = 15) -> str:
    """Descarga contenido de una URL con user-agent realista."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def search_google_news_rss(query: str, lang: str = "en") -> list[dict]:
    """Busca noticias en Google News RSS feed."""
    results = []
    encoded = quote_plus(query)
    hl = "es-419" if lang == "es" else "en-US"
    gl = "MX" if lang == "es" else "US"
    url = (
        f"https://news.google.com/rss/search?"
        f"q={encoded}+when:2d&hl={hl}&gl={gl}&ceid={gl}:{lang}"
    )

    try:
        xml_text = fetch_url(url)
        root = ElementTree.fromstring(xml_text)

        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            source = item.findtext("source", "")

            # Limpiar HTML del título
            title = unescape(re.sub(r"<[^>]+>", "", title)).strip()

            results.append({
                "title": title,
                "link": link,
                "published": pub_date,
                "source": source,
                "query": query,
                "lang": lang,
                "provider": "Google News",
            })
    except Exception as e:
        log.warning(f"Error buscando '{query}' en Google News ({lang}): {e}")

    return results


def search_newsapi(query: str, lang: str = "en") -> list[dict]:
    """Busca noticias en NewsAPI.org (requiere API key gratuita)."""
    if not NEWSAPI_KEY:
        return []

    results = []
    from_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    encoded = quote_plus(query)
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={encoded}&from={from_date}&language={lang}"
        f"&sortBy=publishedAt&pageSize=10&apiKey={NEWSAPI_KEY}"
    )

    try:
        data = json.loads(fetch_url(url))
        for article in data.get("articles", []):
            results.append({
                "title": article.get("title", ""),
                "link": article.get("url", ""),
                "published": article.get("publishedAt", ""),
                "source": article.get("source", {}).get("name", ""),
                "query": query,
                "lang": lang,
                "provider": "NewsAPI",
                "description": article.get("description", ""),
            })
    except Exception as e:
        log.warning(f"Error buscando '{query}' en NewsAPI ({lang}): {e}")

    return results


# ─── DEDUPLICACIÓN ───────────────────────────────────────────────────────────


def deduplicate(articles: list[dict]) -> list[dict]:
    """Elimina artículos duplicados basándose en similitud de título."""
    seen_hashes = set()
    unique = []

    for article in articles:
        # Normalizar título para detectar duplicados
        normalized = re.sub(r"[^a-z0-9\s]", "", article["title"].lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Hash de las primeras 8 palabras (atrapa duplicados con distinta fuente)
        key_words = " ".join(normalized.split()[:8])
        h = hashlib.md5(key_words.encode()).hexdigest()

        if h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(article)

    return unique


# ─── GENERACIÓN DE EMAIL HTML ────────────────────────────────────────────────


def build_email_html(
    articles_by_category: dict[str, list[dict]],
    run_time: datetime,
) -> str:
    """Genera un email HTML con diseño profesional."""

    period_label = "Mañana ☀️"
    hour = run_time.hour
    if 12 <= hour < 17:
        period_label = "Mediodía 🌤️"
    elif hour >= 17:
        period_label = "Noche 🌙"

    total = sum(len(v) for v in articles_by_category.values())

    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
<div style="max-width:680px;margin:20px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1a3a5c 0%,#2d6ca2 100%);padding:28px 32px;color:#fff;">
    <h1 style="margin:0;font-size:22px;font-weight:700;letter-spacing:-0.3px;">
      📡 Monitor de Noticias — Banco Mundial
    </h1>
    <p style="margin:8px 0 0;font-size:14px;opacity:0.85;">
      Reporte {period_label} · {run_time.strftime('%d %b %Y — %H:%M UTC')}
      · <strong>{total} artículo{'s' if total != 1 else ''}</strong> encontrado{'s' if total != 1 else ''}
    </p>
  </div>

  <div style="padding:24px 32px;">
"""

    if total == 0:
        html += """
    <div style="text-align:center;padding:40px 0;">
      <p style="font-size:48px;margin:0;">🔍</p>
      <p style="color:#6b7280;font-size:16px;margin:12px 0 0;">
        No se encontraron noticias nuevas en este periodo.
      </p>
    </div>
"""
    else:
        category_icons = {
            "instituciones": "🏛️",
            "personas": "👤",
        }
        category_labels = {
            "instituciones": "Instituciones",
            "personas": "Personas Clave",
        }

        for category, articles in articles_by_category.items():
            if not articles:
                continue

            icon = category_icons.get(category, "📰")
            label = category_labels.get(category, category.title())

            html += f"""
    <div style="margin-bottom:24px;">
      <h2 style="font-size:16px;color:#1a3a5c;border-bottom:2px solid #e5e7eb;padding-bottom:8px;margin:0 0 16px;">
        {icon} {label}
        <span style="font-weight:400;color:#9ca3af;font-size:13px;margin-left:8px;">
          ({len(articles)} resultado{'s' if len(articles) != 1 else ''})
        </span>
      </h2>
"""
            for art in articles[:15]:  # Máximo 15 por categoría
                lang_badge = (
                    '<span style="background:#dbeafe;color:#1d4ed8;font-size:10px;'
                    'padding:2px 6px;border-radius:4px;margin-left:6px;">EN</span>'
                    if art["lang"] == "en"
                    else '<span style="background:#fef3c7;color:#92400e;font-size:10px;'
                    'padding:2px 6px;border-radius:4px;margin-left:6px;">ES</span>'
                )

                source_text = f" — {art['source']}" if art.get("source") else ""
                desc = art.get("description", "")
                desc_html = (
                    f'<p style="margin:4px 0 0;font-size:13px;color:#6b7280;line-height:1.4;">'
                    f"{desc[:200]}{'…' if len(desc) > 200 else ''}</p>"
                    if desc
                    else ""
                )

                html += f"""
      <div style="margin-bottom:14px;padding:12px 16px;background:#f9fafb;border-radius:8px;border-left:3px solid #2d6ca2;">
        <a href="{art['link']}" style="color:#1a3a5c;text-decoration:none;font-size:14px;font-weight:600;line-height:1.4;">
          {art['title']}
        </a>
        {desc_html}
        <p style="margin:6px 0 0;font-size:11px;color:#9ca3af;">
          🔎 <em>{art['query']}</em>{source_text}
          · {art.get('published', '')[:16]} {lang_badge}
        </p>
      </div>
"""
            html += "    </div>\n"

    html += f"""
    <div style="text-align:center;padding:16px 0 8px;border-top:1px solid #e5e7eb;">
      <p style="font-size:11px;color:#9ca3af;margin:0;">
        Generado automáticamente · Próximo reporte en ~8 horas<br>
        Términos monitoreados: {', '.join(SEARCH_TERMS['instituciones'] + SEARCH_TERMS['personas'])}
      </p>
    </div>
  </div>
</div>
</body>
</html>"""

    return html


# ─── ENVÍO DE EMAIL ──────────────────────────────────────────────────────────


def send_email(subject: str, html_body: str) -> None:
    """Envía el reporte por email vía SMTP."""
    if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_TO]):
        log.error("Faltan credenciales de email. Configurar SMTP_USER, SMTP_PASSWORD, EMAIL_TO.")
        # En modo desarrollo, guardar HTML localmente
        out_path = "/tmp/news_report.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        log.info(f"Reporte guardado localmente en {out_path}")
        return

    recipients = [e.strip() for e in EMAIL_TO.split(",")]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"📡 News Monitor <{SMTP_USER}>"
    msg["To"] = ", ".join(recipients)

    # Versión texto plano
    text_part = MIMEText("Abre este email en un cliente que soporte HTML.", "plain", "utf-8")
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(text_part)
    msg.attach(html_part)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipients, msg.as_string())
        log.info(f"Email enviado exitosamente a {', '.join(recipients)}")
    except Exception as e:
        log.error(f"Error enviando email: {e}")
        raise


# ─── EJECUCIÓN PRINCIPAL ─────────────────────────────────────────────────────


def run_monitor():
    """Ejecuta el ciclo completo de monitoreo."""
    run_time = datetime.now(timezone.utc)
    log.info(f"═══ Iniciando monitoreo: {run_time.isoformat()} ═══")

    articles_by_category: dict[str, list[dict]] = {}

    for category, terms in SEARCH_TERMS.items():
        all_articles = []
        for term in terms:
            for lang in LANGUAGES:
                log.info(f"Buscando: '{term}' [{lang}]")

                # Google News RSS (siempre disponible)
                results = search_google_news_rss(term, lang)
                all_articles.extend(results)
                log.info(f"  → Google News: {len(results)} resultados")

                # NewsAPI (si hay API key)
                results = search_newsapi(term, lang)
                all_articles.extend(results)
                if results:
                    log.info(f"  → NewsAPI: {len(results)} resultados")

        # Deduplicar por categoría
        unique = deduplicate(all_articles)
        articles_by_category[category] = unique
        log.info(f"Categoría '{category}': {len(unique)} artículos únicos")

    total = sum(len(v) for v in articles_by_category.values())
    log.info(f"Total artículos únicos: {total}")

    # Generar y enviar email
    subject = (
        f"📡 Monitoreo Banco Mundial — "
        f"{run_time.strftime('%d/%m/%Y %H:%M')} UTC "
        f"({total} artículo{'s' if total != 1 else ''})"
    )

    html = build_email_html(articles_by_category, run_time)
    send_email(subject, html)

    log.info("═══ Monitoreo completado ═══")
    return total


if __name__ == "__main__":
    run_monitor()
