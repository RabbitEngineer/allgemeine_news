"""Neu ausgeschriebene Stellen in China, aus offenen Bewerbermanagement-APIs.

Die einzige Quelle in dieser Anwendung, die kein RSS ist. Für Stellenanzeigen
gibt es schlicht keine Feeds mehr: LinkedIn hat sein RSS abgeschaltet (404),
Indeed sperrt automatisierte Abrufe (403), StackOverflow Jobs ist eingestellt,
51job und theBeijinger bieten keinen Feed an, StepStone rendert vollständig im
Browser. Google News beantwortet solche Suchen mit Presseartikeln über den
Arbeitsmarkt, nicht mit Ausschreibungen.

Was es stattdessen gibt, sind die **offenen APIs der Bewerbermanagementsysteme**
selbst. Beide hier genutzten sind dokumentiert, verlangen keinen Schlüssel und
liefern JSON:

    SmartRecruiters  api.smartrecruiters.com/v1/companies/<firma>/postings
    Greenhouse       boards-api.greenhouse.io/v1/boards/<board>/jobs

Die Ergebnisse gehen als Kandidaten in dieselbe Pipeline wie die RSS-Beiträge:
Das Modell wählt aus, fasst zusammen und ordnet ein, die Wiederholungssperre
sorgt dafür, dass eine Ausschreibung genau einmal erscheint.

DAS ZEITFENSTER IST BEWUSST SEHR BREIT
--------------------------------------
Stellenanzeigen sind keine Nachrichten. Eine Ausschreibung von vor vier Monaten
ist, solange sie offen steht, genauso gültig wie die von gestern — Riot Games
etwa führt China-Stellen, die seit über einem Jahr ausgeschrieben sind. Ein
30-Tage-Fenster warf davon 13 von 14 fachlich passenden Treffern weg.

Deshalb blickt diese Rubrik ein Jahr zurück und überlässt die Entdopplung
allein der Wiederholungssperre: Beim ersten Lauf erscheint der gesamte offene
Bestand, danach nur noch, was neu hinzugekommen ist.

WARUM ZWEI QUELLEN, UND WARUM DIESE
-----------------------------------
Anfangs standen hier nur deutsche Arbeitgeber über SmartRecruiters. Das war zu
eng gedacht — gesucht ist Arbeit in China, nicht Arbeit bei einer deutschen
Firma. Vor allem aber war es das schlechtere Feld: Von 30 fachlich passenden
Bosch-Ausschreibungen der letzten 30 Tage waren **zwei** international
ausgeschrieben, der Rest richtete sich rein chinesisch an den lokalen
Arbeitsmarkt, 16 davon als Hochschulrekrutierung für Absolventen.

Greenhouse deckt internationale Technologieunternehmen ab, deren Arbeitssprache
Englisch ist — das passt zu einem Bewerber mit rudimentärem Chinesisch weit
besser. Gemessen beim Bau:

    Riot Games   50 Stellen in China (u.a. Cloud Infrastructure and
                 Security Engineer, Shanghai)
    Airbnb       10 Stellen in China, teils Peking
    Epic Games    4 Stellen, Shanghai
    MongoDB       3 Stellen (Vertrieb)
    Databricks    1 Stelle (Vertrieb)

Lever und Ashby wurden ebenfalls geprüft — mit 43 getesteten Kennungen, darunter
die großen Krypto- und Handelsfirmen, ergaben sie keinen einzigen China-Treffer
und sind deshalb nicht eingebaut. Bei SmartRecruiters brachten 131 geprüfte
Kennungen nur Bosch, Continental und Grab.

Eine Kennung aufzunehmen ist gratis: Ein unbekannter Name liefert eine leere
Liste oder einen 404, den `_safe` abfängt, und niemals einen Abbruch.
"""

import json
import re
import socket
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Arbeitgeber
# ---------------------------------------------------------------------------

# SmartRecruiters-Firmenkennungen. Groß-/Kleinschreibung zählt.
SMARTRECRUITERS = [
    "BoschGroup",
    "Continental",
    "Grab",
]

# Greenhouse-Board-Kennungen, in aller Regel der Firmenname kleingeschrieben.
# Geprüft und gültig. hashicorp, confluent, unity, atlassian und canva standen
# hier ebenfalls und antworten mit 404 — sie liegen nicht (mehr) auf Greenhouse.
# Die verbleibenden ohne heutige China-Stelle bleiben absichtlich drin: Der
# Abruf kostet einen Request, und wer erst nächsten Monat in Shanghai
# ausschreibt, wird dann von selbst sichtbar.
GREENHOUSE = [
    "riotgames",
    "airbnb",
    "epicgames",
    "mongodb",
    "databricks",
    "elastic",
    "cloudflare",
    "datadog",
    "gitlab",
    "roblox",
    "scopely",
    "clickhouse",
]

# ---------------------------------------------------------------------------
# Zuschnitt
# ---------------------------------------------------------------------------

# Was als "in China" gilt. SmartRecruiters kann serverseitig nach Land filtern,
# Greenhouse nicht — dort steht der Ort als freier Text ("Shanghai, China",
# "Beijing; Shanghai; Shenzhen", schlicht "China"). Deshalb dieser Ausdruck.
CHINA_RE = re.compile(
    r"china|beijing|peking|shanghai|shenzhen|guangzhou|hangzhou|suzhou|wuxi|"
    r"chengdu|nanjing|wuhan|xi'?an|dalian|tianjin|qingdao|chongqing|changsha|"
    r"jinan|ningbo|xiamen|zhuhai|taicang",
    re.I,
)

# Eingrenzung auf einzelne Städte, kleingeschrieben, Teiltreffer. Eine leere
# Liste hieße: ganz China.
#
# Peking ist ein schmales Feld, das ist gemessen: Über beide Quellen und 230
# geprüfte Arbeitgeberkennungen bleiben derzeit VIER offene Stellen — drei bei
# Grab, eine bei Airbnb. Dafür sind alle vier international ausgeschrieben und
# damit ohne fließendes Mandarin erreichbar; die Trefferquote ist also 100 %,
# während sie über ganz China bei 13 von 20 lag.
#
# Der Grund: Deutsche Industrie sitzt in China im Jangtse-Delta (Bosch verteilt
# sich auf Shanghai, Suzhou und Wuxi), und die internationalen Technologiefirmen
# mit Greenhouse-Board haben ihre China-Standorte fast alle in Shanghai. Wer den
# Radius öffnen will, leert diese Liste — das ist der wirksamste Hebel hier.
CITIES = ["beijing", "peking"]

# Fachlicher Zuschnitt: DevOps zuerst, Backend daneben. Bewusst weit gefasst und
# nur eine Vorauswahl — über die Eignung entscheidet das Modell im
# SYSTEM_PROMPT, das das Profil kennt. Die chinesischen Begriffe sind nötig,
# weil ein großer Teil der Ausschreibungen ausschließlich chinesisch betitelt
# ist (运维 Betrieb/DevOps, 后端 Backend, 云 Cloud, 平台 Plattform).
ROLE_RE = re.compile(
    r"devops|sre|site reliability|platform engineer|kubernetes|k8s|docker|"
    r"ci/cd|cicd|jenkins|terraform|ansible|cloud|infrastructure|infrastruktur|"
    r"backend|back-end|microservice|\bapi\b|linux|automation|automatisier|"
    r"software|developer|entwickl|java|python|golang|informatik|\bIT\b|"
    r"运维|云|后端|平台|架构|自动化|软件|开发",
    re.I,
)

# ---------------------------------------------------------------------------
# Hinweise, die dem Modell die Einordnung ermöglichen
# ---------------------------------------------------------------------------
# Keiner davon filtert. Sie landen im Kandidatentext, und der SYSTEM_PROMPT
# sortiert danach — Sprache vor Fachlichkeit, weil rudimentäres Chinesisch die
# harte Grenze ist und nicht die Rolle.

GERMAN_RE = re.compile(r"german|deutsch|德语|德国", re.I)
ENGLISH_RE = re.compile(r"english|englisch|英语", re.I)

# Rein chinesisch betitelte Stellen richten sich an den lokalen Arbeitsmarkt und
# setzen fast immer fließendes Mandarin voraus.
CJK_RE = re.compile(r"[一-鿿]")

# Hochschulrekrutierung. 校招 ist der feste Ausdruck für den Jahrgangsantritt
# ("届校招" mit vorangestelltem Abschlussjahr), 实习 ein Praktikum. Beides
# richtet sich an Studierende und ist für einen Berufserfahrenen gegenstandslos
# — es machte beim Test aber die Mehrheit der Bosch-Treffer aus.
CAMPUS_RE = re.compile(r"校招|实习|campus|graduate program|intern\b|trainee", re.I)

# Greenhouse führt bei manchen Arbeitgebern Metadaten zu Visum und Umzug. Für
# jemanden, der aus Deutschland zuzieht, ist das die wertvollste Einzelangabe
# in der ganzen Ausschreibung.
VISA_FIELDS = re.compile(r"visa|sponsor|relocation|umzug", re.I)

# Höchstzahl je Arbeitgeber, dasselbe Prinzip wie "per_feed" bei den RSS-Feeds:
# Bosch schrieb im Test an einem einzigen Tag 16 Absolventenstellen aus und
# verdrängte damit sämtliche international ausgeschriebenen Treffer aus dem
# Kandidatenbudget. Ohne diesen Deckel bestimmt der lauteste Arbeitgeber die
# ganze Rubrik.
MAX_PER_EMPLOYER = 6

# Hochschulrekrutierung ganz aussortieren statt nur zu kennzeichnen. Sie
# richtet sich an Studierende und ist für einen Bewerber mit mehrjähriger
# Berufserfahrung gegenstandslos, machte im Test aber die Mehrheit aller
# Treffer aus. Auf False setzen, um sie nur zu markieren.
SKIP_CAMPUS = True

TIMEOUT = 20
WORKERS = 8
PAGE = 100
MAX_PER_COMPANY = 1500
USER_AGENT = (
    "allgemeine-news/1.0 (+https://github.com/topics/rss; "
    "taeglicher persoenlicher Ueberblick)"
)


def _get(url: str):
    request = urllib.request.Request(url)
    request.add_header("User-Agent", USER_AGENT)
    request.add_header("Accept", "application/json")
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read())


def _safe(label: str, call, *args):
    """Einen Abruf ausführen und jeden Fehler in eine leere Liste verwandeln.

    Eine unerreichbare oder umgebaute API darf den Tageslauf so wenig
    abbrechen wie ein toter RSS-Feed. Die Rubrik bleibt dann eben leer, und das
    Protokoll sagt, warum.
    """
    try:
        return call(*args)
    except (urllib.error.URLError, socket.timeout, json.JSONDecodeError,
            OSError, ValueError, KeyError, TypeError) as exc:
        print(f"WARNUNG: Stellen von {label} nicht abrufbar: {exc}", file=sys.stderr)
        return []


def _parse_date(raw: str):
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Adapter: SmartRecruiters
# ---------------------------------------------------------------------------


def _smartrecruiters(company: str) -> list:
    base = f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
    collected, offset = [], 0
    while offset < MAX_PER_COMPANY:
        payload = _get(f"{base}?country=cn&limit={PAGE}&offset={offset}")
        page = payload.get("content") or []
        collected.extend(page)
        offset += PAGE
        if not page or offset >= (payload.get("totalFound") or 0):
            break

    items = []
    for posting in collected:
        location = posting.get("location") or {}
        items.append({
            "employer": (posting.get("company") or {}).get("name") or company,
            "title": str(posting.get("name") or "").strip(),
            "where": location.get("fullLocation") or location.get("city") or "China",
            "city": str(location.get("city") or ""),
            # Geprüft: liefert 200 und ist ohne Konto lesbar, anders als der
            # API-Pfad, der in "ref" steht.
            "url": f"https://jobs.smartrecruiters.com/{company}/{posting.get('id')}",
            "published": _parse_date(posting.get("releasedDate")),
            "level": (posting.get("experienceLevel") or {}).get("label") or "",
            "team": (posting.get("department") or {}).get("label") or "",
            "blob": json.dumps(posting, ensure_ascii=False),
            "visa": "",
        })
    return items


# ---------------------------------------------------------------------------
# Adapter: Greenhouse
# ---------------------------------------------------------------------------


def _greenhouse(board: str) -> list:
    payload = _get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
    items = []
    for job in payload.get("jobs") or []:
        where = str((job.get("location") or {}).get("name") or "")
        if not CHINA_RE.search(where):
            continue
        # Visum und Umzugspaket stehen bei manchen Arbeitgebern in den
        # Metadaten. Für einen Zuzug aus Deutschland ist das die wertvollste
        # Einzelangabe überhaupt, deshalb wird sie eigens herausgezogen.
        visa = []
        for field in job.get("metadata") or []:
            name, value = str(field.get("name") or ""), field.get("value")
            if value in (None, "", []) or not VISA_FIELDS.search(name):
                continue
            visa.append(f"{name}: {value if not isinstance(value, list) else ', '.join(map(str, value))}")
        items.append({
            "employer": job.get("company_name") or board,
            "title": str(job.get("title") or "").strip(),
            "where": where,
            "city": where,
            "url": job.get("absolute_url") or "",
            "published": _parse_date(job.get("first_published") or job.get("updated_at")),
            "level": "",
            "team": "",
            "blob": json.dumps(job, ensure_ascii=False),
            "visa": "; ".join(visa),
        })
    return items


# ---------------------------------------------------------------------------
# Zusammenführen
# ---------------------------------------------------------------------------


def _in_scope(item: dict) -> bool:
    """Ortsfilter. Leeres CITIES heißt: ganz China, alles zählt."""
    if not CITIES:
        return True
    city = item["city"].strip().lower()
    return any(wanted in city for wanted in CITIES)


def _describe(item: dict) -> str:
    """Der Kandidatentext, aus dem das Modell die Einordnung zieht."""
    parts = [f"Ausgeschrieben in {item['where']}."]
    if item["team"]:
        parts.append(f"Bereich: {item['team']}.")
    if item["level"]:
        parts.append(f"Erfahrungsstufe: {item['level']}.")

    title = item["title"]
    if CJK_RE.search(title):
        parts.append("Nur auf Chinesisch ausgeschrieben, richtet sich also "
                     "voraussichtlich an den lokalen Arbeitsmarkt.")
    else:
        parts.append("International ausgeschrieben (lateinischer Titel).")

    blob = item["blob"]
    if GERMAN_RE.search(blob):
        parts.append("Die Ausschreibung erwähnt Deutsch.")
    if ENGLISH_RE.search(blob):
        parts.append("Die Ausschreibung erwähnt Englisch.")
    if CAMPUS_RE.search(title):
        parts.append("Hochschulrekrutierung für Absolventen, nicht für Berufserfahrene.")
    if item["visa"]:
        parts.append(f"Angaben zu Visum/Umzug — {item['visa']}.")
    return " ".join(parts)


def fetch(max_age_hours: int, max_items: int = 30) -> list:
    """Neu ausgeschriebene Stellen im Format von main.fetch_items.

    Gleiche Schlüssel wie ein RSS-Kandidat (source, feed, title, link,
    published, summary), damit der Rest der Pipeline — Wiederholungssperre,
    URL-Prüfung, Herausgeberzuordnung — ohne Sonderfall damit umgehen kann.
    """
    tasks = ([("SmartRecruiters", _smartrecruiters, c) for c in SMARTRECRUITERS]
             + [("Greenhouse", _greenhouse, b) for b in GREENHOUSE])
    if not tasks:
        return []

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(
            lambda t: (t[0], _safe(f"{t[0]}/{t[2]}", t[1], t[2])), tasks
        ))

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    items, seen, per_employer = [], set(), {}
    # Neueste zuerst, dann je Arbeitgeber deckeln — so behält jeder Arbeitgeber
    # seine aktuellsten Ausschreibungen statt zufälliger.
    flat = sorted(
        ((s, r) for s, batch in results for r in batch
         if r["title"] and r["url"] and r["published"]),
        key=lambda pair: pair[1]["published"], reverse=True,
    )
    for source, raw in flat:
        title, url, published = raw["title"], raw["url"], raw["published"]
        if published < cutoff or not _in_scope(raw) or not ROLE_RE.search(title):
            continue
        if SKIP_CAMPUS and CAMPUS_RE.search(title):
            continue
        if url in seen:
            continue
        employer = raw["employer"]
        if per_employer.get(employer, 0) >= MAX_PER_EMPLOYER:
            continue
        per_employer[employer] = per_employer.get(employer, 0) + 1
        seen.add(url)
        items.append({
            "source": employer,
            "feed": source,
            "title": title,
            "link": url,
            "published": published,
            "summary": _describe(raw),
        })
    return items[:max_items]
