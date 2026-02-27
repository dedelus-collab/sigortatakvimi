#!/usr/bin/env python3
"""
Akadoktor TR — Flask Web Uygulaması
Semantic Scholar + OpenAlex API'den gerçek veri çeker.

Kurulum:
    pip install flask flask-cors requests

Çalıştırma:
    python app.py

Sonra tarayıcıda aç:
    http://localhost:5000
"""

from flask import Flask, jsonify, request, send_from_directory
import os
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

TR_KEYWORDS = [
    'turkey','türkiye','ankara','istanbul','izmir','bursa','adana','konya',
    'hacettepe','marmara','gazi','ege','cerrahpasa','cerrahpaşa','bogazici','boğaziçi',
    'bilkent','koc','koç','sabanci','sabancı','ondokuz mayis','karadeniz','uludag','uludağ',
    'selcuk','selçuk','firat','fırat','inonu','inönü','cumhuriyet','baskent','başkent',
    'yeditepe','ataturk','atatürk','dokuz eylul','akdeniz','erciyes','cukurova','çukurova',
    'dicle','gaziantep','mersin','pamukkale','suleyman demirel','trakya','duzce','düzce',
    'afyon','balikesir','balıkesir','celal bayar','sakarya','kocaeli','gebze'
]

def is_turkish(affiliations):
    text = ' '.join((a.get('name','') for a in affiliations)).lower()
    return any(k in text for k in TR_KEYWORDS)

def calc_score(h, c, p, i10):
    return round(h*10 + c*0.01 + p*0.5 + i10*2, 1)


# ── Semantic Scholar ──────────────────────────────────────
def fetch_s2(specialty, univ=''):
    q = f"{specialty} {univ} Turkey".strip()
    url = "https://api.semanticscholar.org/graph/v1/author/search"
    params = {
        "query": q,
        "fields": "name,hIndex,citationCount,paperCount,affiliations,externalIds",
        "limit": 100
    }
    headers = {"User-Agent": "AkadoktorTR/1.0 (academic research tool)"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json().get("data", [])

    results = []
    for a in data:
        affils = a.get("affiliations", [])
        if not is_turkish(affils):
            continue
        h = a.get("hIndex") or 0
        c = a.get("citationCount") or 0
        p = a.get("paperCount") or 0
        if h == 0 and c == 0:
            continue
        affil_str = " · ".join(x["name"] for x in affils if x.get("name"))[:80] or "—"
        orcid = (a.get("externalIds") or {}).get("ORCID")
        results.append({
            "id": "s2_" + str(a.get("authorId","")),
            "name": a.get("name","—"),
            "hIndex": h,
            "citationCount": c,
            "paperCount": p,
            "i10": 0,
            "score": calc_score(h, c, p, 0),
            "affiliation": affil_str,
            "city": "",
            "country": "TR",
            "instType": "",
            "lat": None,
            "lon": None,
            "mapsUrl": f"https://www.google.com/maps/search/{requests.utils.quote(affil_str)}" if affil_str != "—" else "",
            "source": "Semantic Scholar",
            "profileUrl": f"https://www.semanticscholar.org/author/{a.get('authorId','')}",
            "orcid": orcid,
        })
    return results


# ── OpenAlex ─────────────────────────────────────────────
def fetch_oa(specialty, univ=''):
    """
    OpenAlex yaklaşımı:
    1. /works de konu + TR ülke filtresi → yazar+kurum bilgisini works'ten topla
    2. Yazar ID listesiyle /authors'tan h-index, atıf, i10 çek
    3. Kurum bilgisini works authorships'ten al (geo içermiyor ama display_name var)
    4. Kurumun şehri için /institutions endpoint'ini kullan
    """
    import urllib.parse

    # Adım 1: works'te konu ara, authorships+institutions bilgisini getir
    works_filter = f"authorships.institutions.country_code:TR,title.search:{specialty}"
    if univ:
        works_filter += f",authorships.institutions.display_name.search:{univ}"

    works_params = urllib.parse.urlencode({
        "filter": works_filter,
        "per_page": 200,
        "select": "id,authorships",
        "mailto": "akadoktor@example.com"
    })
    r1 = requests.get(f"https://api.openalex.org/works?{works_params}", timeout=20)
    r1.raise_for_status()
    works = r1.json().get("results", [])

    # Adım 2: Yazar → kurum eşlemesi kur (works authorships'ten)
    author_inst_map = {}  # author_id -> {inst_name, inst_id, inst_type, country}
    for work in works:
        for authorship in work.get("authorships", []):
            insts = authorship.get("institutions", [])
            tr_insts = [i for i in insts if (i.get("country_code") or "").upper() == "TR"]
            if not tr_insts:
                continue
            aid = (authorship.get("author") or {}).get("id", "")
            if not aid:
                continue
            aid_short = aid.replace("https://openalex.org/", "")
            if aid_short not in author_inst_map:
                best = tr_insts[0]
                author_inst_map[aid_short] = {
                    "inst_name": best.get("display_name", "—"),
                    "inst_id":   best.get("id", "").replace("https://openalex.org/", ""),
                    "inst_type": best.get("type", ""),
                    "country":   best.get("country_code", "TR"),
                }

    if not author_inst_map:
        return []

    # Adım 3: Kurum ID'lerinden şehir bilgisi çek
    inst_ids = list({v["inst_id"] for v in author_inst_map.values() if v["inst_id"]})[:50]
    inst_city_map = {}  # inst_id -> {city, lat, lon}
    if inst_ids:
        inst_filter = "openalex:" + "|".join(inst_ids)
        inst_params = urllib.parse.urlencode({
            "filter": inst_filter,
            "per_page": 50,
            "select": "id,display_name,geo,type",
            "mailto": "akadoktor@example.com"
        })
        try:
            ri = requests.get(f"https://api.openalex.org/institutions?{inst_params}", timeout=15)
            if ri.ok:
                for inst in ri.json().get("results", []):
                    iid = inst.get("id","").replace("https://openalex.org/","")
                    geo = inst.get("geo") or {}
                    inst_city_map[iid] = {
                        "city": geo.get("city", ""),
                        "lat":  geo.get("latitude"),
                        "lon":  geo.get("longitude"),
                        "type": inst.get("type",""),
                    }
        except Exception:
            pass

    # Adım 4: /authors endpoint'inden h-index, atıf, i10 çek
    results = []
    id_list = list(author_inst_map.keys())[:100]

    for i in range(0, len(id_list), 50):
        batch = id_list[i:i+50]
        # Doğru syntax: openalex: prefix ile pipe-separated
        ids_filter = "openalex:" + "|".join(batch)
        auth_params = urllib.parse.urlencode({
            "filter": ids_filter,
            "per_page": 50,
            "select": "id,display_name,cited_by_count,works_count,summary_stats,orcid",
            "mailto": "akadoktor@example.com"
        })
        r2 = requests.get(f"https://api.openalex.org/authors?{auth_params}", timeout=20)
        if not r2.ok:
            continue

        for a in r2.json().get("results", []):
            oa_id = a.get("id", "").replace("https://openalex.org/", "")
            c     = a.get("cited_by_count") or 0
            p     = a.get("works_count") or 0
            stats = a.get("summary_stats") or {}
            h     = stats.get("h_index") or 0
            i10   = stats.get("i10_index") or 0

            # Kurum bilgisini works'ten aldığımız map'ten al
            inst_info  = author_inst_map.get(oa_id, {})
            affil      = inst_info.get("inst_name", "—")
            inst_id    = inst_info.get("inst_id", "")
            inst_type  = inst_info.get("inst_type", "")
            country    = inst_info.get("country", "TR")

            # Şehri institutions map'ten al
            geo_info   = inst_city_map.get(inst_id, {})
            city       = geo_info.get("city", "")
            lat        = geo_info.get("lat")
            lon        = geo_info.get("lon")
            # type'ı institutions'dan güncelle (daha güvenilir)
            if geo_info.get("type"):
                inst_type = geo_info["type"]

            maps_query = (affil + (" " + city if city else "")).strip()
            maps_url   = f"https://www.google.com/maps/search/{requests.utils.quote(maps_query)}" if affil != "—" else ""

            results.append({
                "id":          "oa_" + oa_id,
                "name":        a.get("display_name", "—"),
                "hIndex":      h,
                "citationCount": c,
                "paperCount":  p,
                "i10":         i10,
                "score":       calc_score(h, c, p, i10),
                "affiliation": affil,
                "city":        city,
                "country":     country,
                "instType":    inst_type,
                "lat":         lat,
                "lon":         lon,
                "mapsUrl":     maps_url,
                "source":      "OpenAlex",
                "profileUrl":  a.get("id", ""),
                "orcid":       a.get("orcid"),
            })

    return results


# ── Merge ─────────────────────────────────────────────────
def normalize(name):
    name = name.lower()
    for a, b in [('ş','s'),('ı','i'),('ğ','g'),('ü','u'),('ö','o'),('ç','c')]:
        name = name.replace(a, b)
    return re.sub(r'\s+', ' ', name).strip()

def merge(s2, oa):
    out = list(s2)
    for doc in oa:
        norm = normalize(doc["name"])
        hit = next((d for d in out if normalize(d["name"]) == norm), None)
        if hit:
            hit["hIndex"]       = max(hit["hIndex"], doc["hIndex"])
            hit["citationCount"]= max(hit["citationCount"], doc["citationCount"])
            hit["paperCount"]   = max(hit["paperCount"], doc["paperCount"])
            hit["i10"]          = max(hit.get("i10",0), doc["i10"])
            hit["score"]        = calc_score(hit["hIndex"], hit["citationCount"], hit["paperCount"], hit["i10"])
            hit["source"]       = "S2 + OpenAlex"
            if not hit.get("orcid") and doc.get("orcid"):
                hit["orcid"] = doc["orcid"]
            hit["profileUrl2"]  = doc["profileUrl"]
        else:
            out.append(dict(doc))
    return out


# ── API Endpoint ──────────────────────────────────────────
@app.route("/api/search")
def api_search():
    specialty = request.args.get("specialty","").strip()
    univ      = request.args.get("univ","").strip()
    if not specialty:
        return jsonify({"error": "specialty parametresi gerekli"}), 400

    results, errors = [], []

    try:
        s2 = fetch_s2(specialty, univ)
        results.extend(s2)
    except Exception as e:
        errors.append(f"Semantic Scholar: {e}")

    try:
        oa = fetch_oa(specialty, univ)
        # merge with existing S2 results
        s2_only = [r for r in results if r["source"]=="Semantic Scholar"]
        oa_only  = [r for r in results if r["source"]!="Semantic Scholar"]
        merged = merge(s2_only, oa)
        results = merged + oa_only
    except Exception as e:
        errors.append(f"OpenAlex: {e}")

    results.sort(key=lambda x: x["score"], reverse=True)
    return jsonify({"results": results, "errors": errors, "total": len(results)})


# ── Frontend ──────────────────────────────────────────────
DIST_DIR = os.path.join(os.path.dirname(__file__), 'dist')


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, "index.html")

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  ⚕  Akadoktor TR — Akademik Doktor Sıralama")
    print("="*55)
    print("  📡 Semantic Scholar + OpenAlex API")
    print("  🌐 Tarayıcıda aç: http://localhost:5000")
    print("  ⛔ Durdurmak için: Ctrl+C")
    print("="*55 + "\n")
    app.run(debug=False, port=5000)
