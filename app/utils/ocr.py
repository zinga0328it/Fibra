import re
from typing import Dict, Any


def extract_wr_fields(text: str) -> Dict[str, Any]:
    text = text or ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    joined = "\n".join(lines)
    data: Dict[str, Any] = {}
    _debug = {'candidates': [], 'methods': []}

    # Numero WR patterns - collect multiple matches and prefer numeric one
    wr_pattern = re.compile(r"\b(?:WR|Numero\s*WR|Nr\.?\s*WR|WR:)\s*[:#-]?\s*([A-Za-z0-9\-_/]+)\b", flags=re.IGNORECASE)
    wr_matches = []
    # collect WR-like matches but ignore matches that follow 'UID' to avoid UID WR artifacts
    for m in wr_pattern.finditer(joined):
        start = m.start()
        pre = joined[max(0, start-10):start]
        if re.search(r"\bUID\s*$", pre, flags=re.IGNORECASE):
            continue
        wr_matches.append(m.group(1).strip())
    if wr_matches:
        # prefer a numeric-only match if available
        numeric_match = next((w for w in wr_matches if re.match(r"^\d+$", w)), None)
        sel = numeric_match or wr_matches[0]
        data["numero_wr"] = sel
        _debug['methods'].append('label:WR')
    # Check for 'Pratica' label which acts like a WR numbering in some payloads
    if 'numero_wr' not in data:
        # Try 'Pratica' with optional 'N' or 'Nr.' suffix like 'Pratica N. 12345' or 'Pratica: 12345'
        m = re.search(r"\bPratica(?:\s*(?:N(?:r|°|\.)?)?)\s*[:#-]?\s*([A-Za-z0-9\-_/]+)\b", joined, flags=re.IGNORECASE)
        if not m:
            # Try patterns like 'N° Pratica 12345' or 'N. Pratica 12345'
            m = re.search(r"\bN(?:°|r|\.)\s*Pratica\s*[:#-]?\s*([A-Za-z0-9\-_/]+)\b", joined, flags=re.IGNORECASE)
        if m:
            data["numero_wr"] = m.group(1).strip()
            _debug['methods'].append('label:Pratica')
    # Also accept ID: or ID - common patterns that hide WR numbers without WR explicit label
    if 'numero_wr' not in data:
        # look for digits following ID label, skip named suffixes e.g. 'ID Xme: 283.233'
        m = re.search(r"\b(?:ID|Id|id|Pratica ID)\b[^0-9]{0,10}([0-9][0-9\.,\-_/]+)", joined, flags=re.IGNORECASE)
        if m:
            # sanitize number like 283.233 -> 283233, but we can keep as string; we only use numeric candidates for fallback
            raw_id = m.group(1).strip()
            # normalize numbers by removing punctuation dots/commas used as thousands/decimal separators
            raw_id_norm = re.sub(r"[\.,]", "", raw_id)
            data['numero_wr'] = raw_id_norm
            _debug['methods'].append('label:ID')
    # Try NW patterns in case 'N° Impianto: NW: 15699897' is used in the payload
    if 'numero_wr' not in data:
        # direct NW label like 'NW:' or 'N° Impianto NW:'
        m = re.search(r"\bNW[:#\s-]+([0-9A-Za-z\-_/]+)\b", joined, flags=re.IGNORECASE)
        if m:
            data['numero_wr'] = m.group(1).strip()
            _debug['methods'].append('label:NW')
    if 'numero_wr' not in data:
        # N° Impianto (Italian) with number afterwards
        m = re.search(r"\bN(?:°|r|\.)?\s*Impianto[:#\s-]*([0-9A-Za-z\-_/]+)\b", joined, flags=re.IGNORECASE)
        if m:
            data['numero_wr'] = m.group(1).strip()
            _debug['methods'].append('label:N-IMPIANTO')

    # Operatore
    m = re.search(r"\b(?:Operatore|ISP|Fornitore)[: ]+(.+?)\b(?:\n|$)", joined, flags=re.IGNORECASE)
    if m:
        data["operatore"] = m.group(1).strip()
    else:
        # Try common operator names
        for op in ["Open Fiber", "Fastweb", "ENI", "Vodafone"]:
            if re.search(op, joined, flags=re.IGNORECASE):
                data["operatore"] = op
                break

    # Indirizzo
    m = re.search(r"\b(?:Indirizzo|Address)[: ]+(.+?)\b(?:\n|$)", joined, flags=re.IGNORECASE)
    if m:
        data["indirizzo"] = m.group(1).strip()
    else:
        # fallback: look for line that contains street words
        for line in lines:
            if re.search(r"\b(Via|Piazza|P.zza|Corso|Strada|Viale)\b", line, flags=re.IGNORECASE):
                data["indirizzo"] = line
                break

    # Cliente
    m = re.search(r"\b(?:Cliente|Intestatario|Nome cliente)[: ]+(.+?)\b(?:\n|$)", joined, flags=re.IGNORECASE)
    if m:
        data["nome_cliente"] = m.group(1).strip()

    # Tipo lavoro
    m = re.search(r"\b(?:Tipo\s*lavoro|Lavoro|Intervento)[: ]+(attivazione|guasto|manutenzione)\b", joined, flags=re.IGNORECASE)
    if m:
        data["tipo_lavoro"] = m.group(1).strip().lower()

    # Appuntamento
    m = re.search(r"\b(?:Appuntamento|Data|Orario)[: ]+(.+?)\b(?:\n|$)", joined, flags=re.IGNORECASE)
    if m:
        data["appuntamento"] = m.group(1).strip()

    # Splitter / PTE / ODF
    m = re.search(r"\b(Splitter|PTE|ODF)[: ]+(.+?)\b(?:\n|$)", joined, flags=re.IGNORECASE)
    if m:
        data[m.group(1).strip()] = m.group(2).strip()

    # Final fallback: if no numero_wr, attempt to find numeric-only candidates of reasonable length
    if 'numero_wr' not in data:
        # look for possible numeric references that are likely WR numbers (7+ digits)
        m2 = re.search(r"\b(\d{7,})\b", joined)
        if m2:
            candidate = m2.group(1)
            data['numero_wr'] = candidate
            _debug['methods'].append('candidate:numeric')
            _debug['candidates'].append(candidate)
    # attach debug info for later inspection
    if _debug['methods'] or _debug['candidates']:
        data['_parse_debug'] = _debug
    return data


def extract_wr_entries(text: str) -> list[Dict[str, Any]]:
    """Attempt to split the input text into multiple WR entries and extract fields for each.

    Strategy:
    - Find occurrences of the 'WR' keyword (or common variants) and split the text between them.
    - For each slice, call extract_wr_fields to get a dict of fields. Return only slices that provide at least one meaningful field (numero_wr or nome_cliente).
    - If no WR occurrences found, fall back to treating the whole text as one entry.
    """
    if not text:
        return []
    joined = text
    # Find starts for entries using a robust WR-like pattern
    # Include 'Pratica' as it commonly denotes a work number (WR-like)
    pattern = re.compile(r"\b(?:WR|Pratica|NW|N(?:°|r|\.)?\s*Impianto|ID|Numero\s*WR|Numero\s*Pratica|Nr\.?\s*WR|WR:)\s*[:#-]?\s*[A-Za-z0-9\-_/]+", flags=re.IGNORECASE)
    matches = list(pattern.finditer(joined))
    starts = []
    for m in matches:
        # ignore matches like 'UID WR:' to avoid splitting on UID fields
        pre = joined[max(0, m.start()-10):m.start()]
        if re.search(r"\bUID\s*$", pre, flags=re.IGNORECASE):
            continue
        starts.append(m.start())
    entries = []
    if len(starts) == 0:
        # Try to detect multiple sections per page using 'Cliente' as a boundary or 'Indirizzo'
        # Heuristic: split by repeated occurrences of 'Cliente' or 'Indirizzo'
        boundaries = list(re.finditer(r"\b(?:Cliente|Intestatario|Indirizzo)[: ]+", joined, flags=re.IGNORECASE))
        if len(boundaries) > 1:
            idxs = [b.start() for b in boundaries]
            idxs.append(len(joined))
            for i in range(len(idxs)-1):
                slice_text = joined[idxs[i]:idxs[i+1]]
                s = extract_wr_fields(slice_text)
                if s and (s.get('numero_wr') or s.get('nome_cliente')):
                    # Attach the raw slice so UI can highlight the text that's been parsed
                    try:
                        s['_raw'] = slice_text
                    except Exception:
                        pass
                    entries.append(s)
        # if still no splitting, fallback to whole text
        if not entries:
            s = extract_wr_fields(joined)
            if s and (s.get('numero_wr') or s.get('nome_cliente')):
                try:
                    s['_raw'] = joined
                except Exception:
                    pass
                entries.append(s)
        return entries
    elif len(starts) == 1:
        # A single WR-like start exists; capture from that start until end as a single entry
        starts.append(len(joined))
        for i in range(len(starts)-1):
            sl = joined[starts[i]:starts[i+1]]
            s = extract_wr_fields(sl)
            if s and (s.get('numero_wr') or s.get('nome_cliente')):
                try:
                    s['_raw'] = sl
                except Exception:
                    pass
                entries.append(s)
        return entries
    # There are at least two WR matches: split slices
    # We'll determine ranges between starts
    starts.append(len(joined))
    for i in range(len(starts)-1):
        sl = joined[starts[i]:starts[i+1]]
        s = extract_wr_fields(sl)
        if s and (s.get('numero_wr') or s.get('nome_cliente')):
            entries.append(s)
    return entries


def normalize_numero_wr(s: str | None) -> str | None:
    """Normalize a WR number string to a canonical format.

    Examples:
    - '1764902551' -> 'WR-1764902551'
    - 'wr1764902551' -> 'WR-1764902551'
    - 'WR-1764902551' -> 'WR-1764902551'
    - None -> None
    """
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    # uppercase and remove surrounding spaces
    s = s.upper()
    # Remove weird characters except alnum and dash and underscore and slash
    s = re.sub(r"[^A-Z0-9\-_/]", "", s)
    # Ensure it uses 'WR-' prefix if it seems to be numeric or already prefixed without dash
    m = re.match(r'^(?:WR[-_]?)(\d+)$', s, flags=re.IGNORECASE)
    if m:
        return f"WR-{m.group(1)}"
    # if it's purely numeric, add prefix
    if re.match(r'^\d+$', s):
        return f"WR-{s}"
    # fallback: return uppercase cleaned string
    return s
