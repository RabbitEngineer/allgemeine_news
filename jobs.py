"""Neu ausgeschriebene Stellen bei deutschen Arbeitgebern in China.

Die einzige Quelle in dieser Anwendung, die kein RSS ist. Für Stellenanzeigen
gibt es schlicht keine Feeds mehr: LinkedIn hat sein RSS abgeschaltet (404),
Indeed sperrt automatisierte Abrufe (403), StackOverflow Jobs ist eingestellt,
51job und eChinacities bieten keinen Feed an. Google News beantwortet solche
Suchen mit Presseartikeln über den Arbeitsmarkt, nicht mit Ausschreibungen.

Was es stattdessen gibt, ist die **öffentliche API von SmartRecruiters** — dem
Bewerbermanagementsystem, über das ein Teil der deutschen Industrie ihre
Stellen ausschreibt. Sie ist dokumentiert, verlangt keinen Schlüssel und
liefert JSON:

    https://api.smartrecruiters.com/v1/companies/<firma>/postings?country=cn

Die Ergebnisse gehen als Kandidaten in dieselbe Pipeline wie die RSS-Beiträge:
Das Modell wählt aus, fasst zusammen und ordnet ein, die Wiederholungssperre
sorgt dafür, dass eine Ausschreibung genau einmal erscheint. Die Rubrik zeigt
also **neu ausgeschriebene** Stellen, keinen dauerhaften Stellenmarkt.

ERWARTUNGEN — gemessen, damit niemand rätselt, und ernüchternd:

    1289 Ausschreibungen in China insgesamt
     199 davon in den letzten 30 Tagen
      15 davon DevOps- oder Backend-nah
       0 davon mit lateinischem Titel
       0 davon in Peking

Zwei Befunde stecken darin. Erstens sitzt die deutsche Industrie in China im
Jangtse-Delta und nicht in der Hauptstadt — die 15 Treffer lagen in Suzhou (6),
Shanghai (3), Wuxi (3), Hangzhou und Jinan. Deshalb steht CITIES unten leer,
also ohne Ortsfilter; eine Eingrenzung auf Peking räumt die Rubrik leer.

Zweitens, und das wiegt schwerer: Alle 15 waren ausschließlich auf Chinesisch
ausgeschrieben. Solche Stellen richten sich an den lokalen Arbeitsmarkt und
setzen in aller Regel fließendes Mandarin voraus. Für einen Bewerber mit nur
rudimentären Chinesischkenntnissen ist diese Quelle deshalb strukturell dünn —
sie bleibt drin, weil eine international ausgeschriebene Stelle jederzeit
auftauchen kann und dann sofort sichtbar ist, aber sie ersetzt keine eigene
Suche. Was stattdessen trägt, steht in der README unter "Was diese Rubrik
nicht leisten kann".

Nur Bosch und Continental fanden sich unter 52 geprüften deutschen Namen bei
SmartRecruiters; SAP, Siemens, BMW, Mercedes, BASF, Bayer, Henkel, Infineon,
ZF, Schaeffler und Lufthansa nutzen andere Systeme (SuccessFactors, Workday,
Phenom), die jeweils einen eigenen Adapter bräuchten. COMPANIES zu erweitern
ist dagegen gratis: ein unbekannter Name liefert `totalFound: 0` statt eines
Fehlers.
"""

import json
import re
import socket
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

API = "https://api.smartrecruiters.com/v1/companies/{company}/postings"

# SmartRecruiters-Firmenkennungen. Groß-/Kleinschreibung zählt. Ein unbekannter
# Name ist ungefährlich: die API antwortet mit 200 und totalFound 0.
COMPANIES = [
    "BoschGroup",
    "Continental",
]

# Städte, die zählen — kleingeschrieben verglichen, Teiltreffer erlaubt.
# LEERE LISTE heißt: ganz China, kein Ortsfilter. So ist es eingestellt, weil
# eine Eingrenzung auf Peking die Rubrik leerräumt: Von den 15 DevOps- und
# Backend-Treffern der letzten 30 Tage lag KEINER in Peking, sondern in Suzhou
# (6), Shanghai (3), Wuxi (3), Hangzhou und Jinan. Deutsche Industrie sitzt in
# China im Jangtse-Delta, nicht in der Hauptstadt.
CITIES = []

# Ländercode der API. "cn" ist Festlandchina.
COUNTRY = "cn"

# Wie viele Ausschreibungen je Firma höchstens geholt werden. Die API liefert
# 100 je Seite; Bosch allein hat über 1200 in China, ohne Deckel wären das 13
# Abrufe für eine Rubrik, die am Ende drei Einträge zeigt.
MAX_PER_COMPANY = 1500
PAGE = 100

# Fachlicher Zuschnitt: DevOps zuerst, Backend daneben. Bewusst weit gefasst
# und nur eine Vorauswahl — über die Eignung entscheidet das Modell im
# SYSTEM_PROMPT, das das Profil des Lesers kennt. Die chinesischen Begriffe
# sind nötig, weil der größte Teil der Ausschreibungen ausschließlich auf
# Chinesisch betitelt ist (运维 Betrieb/DevOps, 后端 Backend, 云 Cloud).
ROLE_RE = re.compile(
    r"devops|sre|site reliability|platform engineer|kubernetes|k8s|docker|"
    r"ci/cd|cicd|jenkins|terraform|ansible|cloud|infrastructure|infrastruktur|"
    r"backend|back-end|microservice|\bapi\b|linux|automation|automatisier|"
    r"software|developer|entwickl|java|python|golang|informatik|\bIT\b|"
    r"运维|云|后端|平台|架构|自动化|软件|开发",
    re.I,
)

# Deutschkenntnisse sind der Vorteil des Lesers; eine Ausschreibung, die sie
# nennt, ist deshalb wertvoller als eine ohne. Nur ein Hinweis für das Modell,
# kein Filter.
GERMAN_RE = re.compile(r"german|deutsch|德语|德国", re.I)

# Der Leser spricht Deutsch und Englisch, Chinesisch nur rudimentär. Das dreht
# die übliche Bewertung um: Eine Ausschreibung mit lateinischem Titel ist in
# aller Regel international ausgeschrieben und damit überhaupt erreichbar, eine
# rein chinesische richtet sich an den lokalen Arbeitsmarkt und setzt fast
# immer fließendes Mandarin voraus. Auch das ist nur ein Hinweis; entscheiden
# soll das Modell, nicht ein Filter hier.
CJK_RE = re.compile(r"[一-鿿]")

# Hochschulrekrutierung. 校招 ist der feste Ausdruck für den Jahrgangsantritt
# ("届校招" mit vorangestelltem Abschlussjahr), 实习 ist ein Praktikum. Beides
# richtet sich an Studierende und ist für einen Bewerber mit mehrjähriger
# Berufserfahrung gegenstandslos — es machte beim Test aber die Mehrheit der
# Treffer aus, taucht also als Hinweis in der Zusammenfassung auf.
CAMPUS_RE = re.compile(r"校招|实习|campus|graduate program|intern\b|trainee", re.I)

TIMEOUT = 20
WORKERS = 4
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


def _postings(company: str) -> list:
    """Alle Ausschreibungen einer Firma im Zielland, seitenweise.

    Wirft nie. Eine unerreichbare oder umgebaute API darf den Tageslauf so
    wenig abbrechen wie ein toter RSS-Feed — die Rubrik bleibt dann leer und
    der Lauf sagt, warum.
    """
    collected, offset = [], 0
    while offset < MAX_PER_COMPANY:
        url = f"{API.format(company=company)}?country={COUNTRY}&limit={PAGE}&offset={offset}"
        try:
            payload = _get(url)
        except (urllib.error.URLError, socket.timeout, json.JSONDecodeError, OSError) as exc:
            print(f"WARNUNG: Stellen von {company} nicht abrufbar: {exc}", file=sys.stderr)
            return collected
        page = payload.get("content") or []
        collected.extend(page)
        offset += PAGE
        if not page or offset >= (payload.get("totalFound") or 0):
            break
    return collected


def _released(posting: dict):
    raw = str(posting.get("releasedDate") or "")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _in_scope(posting: dict) -> bool:
    """Ortsfilter. Leeres CITIES heißt: ganz China, alles zählt."""
    if not CITIES:
        return True
    city = str((posting.get("location") or {}).get("city") or "").strip().lower()
    return any(city == wanted or wanted in city for wanted in CITIES)


def fetch(max_age_hours: int, max_items: int = 30) -> list:
    """Neu ausgeschriebene Stellen als Kandidaten im Format von main.fetch_items.

    Gleiche Schlüssel wie ein RSS-Kandidat (source, feed, title, link,
    published, summary), damit der Rest der Pipeline — Wiederholungssperre,
    URL-Prüfung, Herausgeberzuordnung — ohne Sonderfall damit umgehen kann.
    """
    if not COMPANIES:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    items = []

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(_postings, COMPANIES))

    for company, postings in zip(COMPANIES, results):
        for posting in postings:
            if not _in_scope(posting):
                continue
            released = _released(posting)
            if released is None or released < cutoff:
                continue
            title = str(posting.get("name") or "").strip()
            if not title or not ROLE_RE.search(title):
                continue
            posting_id = str(posting.get("id") or "").strip()
            if not posting_id:
                continue

            location = posting.get("location") or {}
            department = (posting.get("department") or {}).get("label") or ""
            experience = (posting.get("experienceLevel") or {}).get("label") or ""
            hints = []
            if GERMAN_RE.search(json.dumps(posting, ensure_ascii=False)):
                hints.append("Die Ausschreibung nennt Deutschkenntnisse.")
            hints.append(
                "Nur auf Chinesisch ausgeschrieben, richtet sich also"
                " voraussichtlich an den lokalen Arbeitsmarkt."
                if CJK_RE.search(title) else
                "International ausgeschrieben (lateinischer Titel)."
            )
            if CAMPUS_RE.search(title):
                hints.append(
                    "Hochschulrekrutierung fuer Absolventen, nicht fuer "
                    "Berufserfahrene."
                )
            hint = " " + " ".join(hints)

            items.append({
                "source": posting.get("company", {}).get("name") or company,
                "feed": "SmartRecruiters",
                "title": title,
                # Die öffentliche Anzeigenseite. Geprüft: liefert 200 und ist
                # ohne Konto lesbar, anders als der API-Pfad in "ref".
                "link": f"https://jobs.smartrecruiters.com/{company}/{posting_id}",
                "published": released,
                "summary": (
                    f"Ausgeschrieben in {location.get('fullLocation') or location.get('city')}."
                    f"{f' Bereich: {department}.' if department else ''}"
                    f"{f' Erfahrungsstufe: {experience}.' if experience else ''}"
                    f"{hint}"
                ).strip(),
            })

    items.sort(key=lambda item: item["published"], reverse=True)
    return items[:max_items]
