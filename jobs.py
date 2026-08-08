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

ERWARTUNGEN — vor dem ersten Lauf gemessen, damit niemand rätselt:

    Bosch        1258 Stellen in China, davon    24 in Peking
    Continental    31 Stellen in China, davon     0 in Peking

Deutsche Industriearbeitgeber sitzen in China im Jangtse-Delta, nicht in der
Hauptstadt: Bei Bosch verteilen sich die Stellen auf Shanghai (345), Suzhou
(333) und Wuxi (227). Auf Peking allein eingegrenzt bleibt fast nichts übrig,
und IT-nahe Stellen dort sind die Ausnahme. Wer mehr sehen will, erweitert
CITIES unten — das ist eine Zeile und der wirksamste Hebel in dieser Datei.

Nur Bosch und Continental fanden sich unter den geprüften deutschen Namen bei
SmartRecruiters; SAP, Siemens, BMW, Mercedes, BASF, Bayer, Henkel, Infineon
und Lufthansa nutzen andere Systeme (SuccessFactors, Workday, Phenom), die
jeweils einen eigenen Adapter bräuchten. COMPANIES aufzunehmen ist dagegen
gratis: ein falscher Name liefert `totalFound: 0` statt eines Fehlers.
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

# Städte, die zählen — kleingeschrieben verglichen. Peking allein ergibt fast
# nichts (siehe Kopf dieser Datei); "shanghai" und "suzhou" aufzunehmen ist der
# Unterschied zwischen einer leeren und einer gefüllten Rubrik.
CITIES = ["beijing"]

# Ländercode der API. "cn" ist Festlandchina.
COUNTRY = "cn"

# Wie viele Ausschreibungen je Firma höchstens geholt werden. Die API liefert
# 100 je Seite; Bosch allein hat über 1200 in China, ohne Deckel wären das 13
# Abrufe für eine Rubrik, die am Ende drei Einträge zeigt.
MAX_PER_COMPANY = 600
PAGE = 100

# Fachlicher Zuschnitt. Bewusst weit gefasst und nur eine Vorauswahl — über die
# Eignung entscheidet das Modell im SYSTEM_PROMPT, das den Lebenslauf des
# Lesers kennt. Chinesische Begriffe sind nötig, weil ein Teil der
# Ausschreibungen ausschließlich auf Chinesisch betitelt ist.
ROLE_RE = re.compile(
    r"software|engineer|developer|entwickl|informatik|\bIT\b|data|cloud|devops|"
    r"cyber|security|architect|programmier|analyst|digital|system|automation|"
    r"软件|开发|数据|算法|系统|工程师|架构|信息",
    re.I,
)

# Deutschkenntnisse sind der Vorteil des Lesers; eine Ausschreibung, die sie
# nennt, ist deshalb wertvoller als eine ohne. Nur ein Hinweis für das Modell,
# kein Filter.
GERMAN_RE = re.compile(r"german|deutsch|德语|德国", re.I)

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
    city = str((posting.get("location") or {}).get("city") or "").strip().lower()
    return any(city == wanted or wanted in city for wanted in CITIES)


def fetch(max_age_hours: int, max_items: int = 30) -> list:
    """Neu ausgeschriebene Stellen als Kandidaten im Format von main.fetch_items.

    Gleiche Schlüssel wie ein RSS-Kandidat (source, feed, title, link,
    published, summary), damit der Rest der Pipeline — Wiederholungssperre,
    URL-Prüfung, Herausgeberzuordnung — ohne Sonderfall damit umgehen kann.
    """
    if not COMPANIES or not CITIES:
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
            hint = " Die Ausschreibung nennt Deutschkenntnisse." if GERMAN_RE.search(
                json.dumps(posting, ensure_ascii=False)
            ) else ""

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
