import os
import re
import camelot
import pandas as pd
from sqlalchemy import create_engine
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#KEYWORD + WHITELISTING SENDERS

# === SETTINGS ===
DESTINATION_FOLDER = r"D:\MyWorkspace\Data Sets\test01"  # Change to local storage path for CWC pdfs
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']  # allows marking as read
KEYWORDS = ["bulletin", "morning", "evening"]  # case-insensitive match
WHITELIST_SENDERS = ["hie.rohitb@gmail.com","hiu.wrd@gmail.com"]  # allowed senders


def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def download_new_pdfs():
    service = authenticate_gmail()

    try:
        # Build 'from' part of the query
        from_filter = " OR ".join([f"from:{email}" for email in WHITELIST_SENDERS])

        # Gmail search query
        search_query = (
            f'is:unread has:attachment filename:pdf '
            f'(filename:Bulletin OR filename:Morning OR filename:Evening) '
            f'({from_filter})'
        )

        results = service.users().messages().list(
            userId='me',
            q=search_query
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            print("No new matching PDF attachments found from whitelisted senders.")
            return

        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            for part in msg_data['payload'].get('parts', []):
                filename = part['filename']
                # Double check: keyword match and PDF extension
                if filename.lower().endswith('.pdf') and any(k in filename.lower() for k in KEYWORDS):
                    att_id = part['body']['attachmentId']
                    attachment = service.users().messages().attachments().get(
                        userId='me', messageId=msg['id'], id=att_id
                    ).execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'])

                    file_path = os.path.join(DESTINATION_FOLDER, filename)
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    print(f"✅ Saved: {file_path}")

            # Mark email as read
            service.users().messages().modify(
                userId='me',
                id=msg['id'],
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

    except HttpError as error:
        print(f"❌ An error occurred: {error}")

if __name__ == '__main__':
    download_new_pdfs()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#MAIN CODE : READING, PARSING CWC PDFs INTO DATABASE --CAMELOT

# ========= CONFIG =========
FOLDER_PATH = r"D:\MyWorkspace\Data Sets\CWC pdfs"   # <-- change if needed
TABLE_NAME  = "river_levels_bulletin"

DB = dict(host="localhost", port=5432, db="CWCv2", user="postgres", password="12345")
ENGINE = create_engine(f"postgresql://{DB['user']}:{DB['password']}@{DB['host']}:{DB['port']}/{DB['db']}")

# Final schema (order matters for DB insert)
FINAL_COLS = [
    "unique_id", "river", "sl_no", "station", "district",
    "warning_level_m", "danger_level_m", "hfl_m",
    "water_level_0800hrs_m", "water_level_1800hrs_m",
    "trend", "trend_01",
    "forecast_waterlevel_m", "forecast_time", "forecast_date",
    "fc_no", "rainfall_mm", "remarks", "source_file"
]

# ========= UTILITIES =========
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

def extract_file_number(name: str) -> int:
    m = re.search(r"(\d+)(?=\.pdf$)", name, re.IGNORECASE)
    return int(m.group(1)) if m else -1

def extract_date_from_name(name: str) -> str:
    m = re.search(r"(\d{2}[.\-]\d{2}[.\-]\d{4})", name)
    return m.group(1).replace("-", ".") if m else "0000.00.00"

def detect_session_from_name(name: str) -> str:
    name_low = name.lower()
    if "morning" in name_low or "(mor" in name_low or "0800" in name_low:
        return "Morning"
    if "evening" in name_low or "(eve" in name_low or "1800" in name_low:
        return "Evening"
    return "Unknown"

def normalize_header(h: str) -> str:
    """Aggressive header normalizer → DB schema names."""
    c = str(h or "").strip().lower()
    c = re.sub(r"[^\w\s]", "_", c)
    c = re.sub(r"\s+", "_", c)
    c = re.sub(r"__+", "_", c).strip("_")

    # NEW: any header that contains 'rainfall' → rainfall_mm
    if "rainfall" in c:
        return "rainfall_mm"

    mapping = {
        "sl_no": "sl_no", "slno": "sl_no", "sl__no": "sl_no",
        "station": "station", "district": "district", "river": "river",

        "warning_level_m": "warning_level_m",
        "warning_level__m": "warning_level_m",
        "warning_level__amz": "warning_level_m",
        "warning_level_amz": "warning_level_m",

        "danger_level_m": "danger_level_m",
        "danger_level__m": "danger_level_m",
        "danger_level__amz": "danger_level_m",
        "danger_level_amz": "danger_level_m",

        "hfl_m": "hfl_m",
        "h_f_l_m": "hfl_m",
        "h_f_l__m": "hfl_m",
        "h_f_l__amz": "hfl_m",
        "h_f_l_amz": "hfl_m",

        # Water level time columns
        "water_level_at_0800_hrs_m": "water_level_0800hrs_m",
        "water_level_0800_hrs_m": "water_level_0800hrs_m",
        "water_level_0800hrs_m": "water_level_0800hrs_m",
        "water_level_at__0800_hrs__m": "water_level_0800hrs_m",

        "water_level_at_1800_hrs_m": "water_level_1800hrs_m",
        "water_level_1800_hrs_m": "water_level_1800hrs_m",
        "water_level_1800hrs_m": "water_level_1800hrs_m",
        "water_level_at__1800_hrs__m": "water_level_1800hrs_m",

        "trend": "trend", "trend_01": "trend_01",

        # Forecast 3-way header
        "forecast": "forecast",
        "forecast_water_level_m": "forecast_waterlevel_m",
        "forecast_waterlevel_m": "forecast_waterlevel_m",
        "forecast_time": "forecast_time",
        "forecast_date": "forecast_date",

        "fc_no": "fc_no", "f_c_no": "fc_no", "f_c__no": "fc_no", "f_c_no_": "fc_no",

        # (older hard-coded rainfall variants kept, but generic rule above handles most cases)
        "rainfall_mm": "rainfall_mm",
        "rainfall_mm_recorded_in_last_24_hours": "rainfall_mm",
        "rainfall_mm_recorded_in_last_24_hours_upto_0830hrs_ist": "rainfall_mm",

        "remarks": "remarks"
    }
    return mapping.get(c, c)

def coerce_number(x):
    if x is None:
        return None
    s = str(x).strip()
    if s in ("", "-", "—"):
        return None
    m = NUM_RE.search(s)
    return float(m.group(0)) if m else None

def coerce_time(x):
    if not x or str(x).strip() == "":
        return None
    s = str(x).strip().replace(".", ":")
    if re.fullmatch(r"\d{4}", s):
        s = f"{s[:2]}:{s[2:]}"
    try:
        return pd.to_datetime(s, errors="raise").time()
    except Exception:
        return None
#-----------------------------------------------------------------------------------------------------------------------------------------------------
def coerce_date(x):
    if not x or str(x).strip() == "":
        return None
    s = str(x).strip().replace("/", "-").replace(".", "-")
    try:
        return pd.to_datetime(s, errors="raise", dayfirst=True).date()
    except Exception:
        return None

def ensure_three_after_forecast(cols):
    out, i = [], 0
    while i < len(cols):
        c = str(cols[i] or "")
        if normalize_header(c) == "forecast" and i + 2 < len(cols):
            out.extend(["forecast_waterlevel_m", "forecast_time", "forecast_date"])
            i += 3
        else:
            out.append(cols[i])
            i += 1
    return out

def finalize_headers(raw_cols):
    cols = ensure_three_after_forecast(list(raw_cols))
    cols = [normalize_header(c) for c in cols]

    # Handle duplicate 'trend'
    seen_trend = 0
    final = []
    for c in cols:
        if c == "trend":
            final.append("trend" if seen_trend == 0 else "trend_01")
            seen_trend += 1
        else:
            final.append(c)
    return final

def fallback_fill_levels(df):
    present = set(df.columns)

    def try_backfill(target, patterns):
        if target in present and df[target].notna().any():
            return
        for col in df.columns:
            name = col.lower()
            if any(p.search(name) for p in patterns):
                df[target] = df[target].fillna(df[col].apply(coerce_number)) if target in present else df[col].apply(coerce_number)
                break

    warn_pat   = [re.compile(r"warning.*m"), re.compile(r"w_?l.*m")]
    danger_pat = [re.compile(r"danger.*m"),  re.compile(r"d_?l.*m")]
    hfl_pat    = [re.compile(r"h[\W_]*f[\W_]*l.*m"), re.compile(r"hfl.*m")]

    if "warning_level_m" not in df.columns:
        df["warning_level_m"] = None
    if "danger_level_m" not in df.columns:
        df["danger_level_m"] = None
    if "hfl_m" not in df.columns:
        df["hfl_m"] = None

    try_backfill("warning_level_m", warn_pat)
    try_backfill("danger_level_m", danger_pat)
    try_backfill("hfl_m", hfl_pat)

def route_water_levels(df, session):
    if "water_level_0800hrs_m" in df.columns or "water_level_1800hrs_m" in df.columns:
        if "water_level_0800hrs_m" in df.columns:
            df["water_level_0800hrs_m"] = df["water_level_0800hrs_m"].apply(coerce_number)
        else:
            df["water_level_0800hrs_m"] = None
        if "water_level_1800hrs_m" in df.columns:
            df["water_level_1800hrs_m"] = df["water_level_1800hrs_m"].apply(coerce_number)
        else:
            df["water_level_1800hrs_m"] = None
        return

    # Fallback single "water level" column detection
    candidate = None
    for col in df.columns:
        c = col.lower()
        if "water" in c and "level" in c:
            candidate = col
            break

    if candidate is None:
        df["water_level_0800hrs_m"] = None
        df["water_level_1800hrs_m"] = None
        return

    vals = df[candidate].apply(coerce_number)
    if session == "Morning":
        df["water_level_0800hrs_m"] = vals
        df["water_level_1800hrs_m"] = None
    elif session == "Evening":
        df["water_level_0800hrs_m"] = None
        df["water_level_1800hrs_m"] = vals
    else:
        df["water_level_0800hrs_m"] = vals
        df["water_level_1800hrs_m"] = None

def coerce_types(df):
    for col in ["warning_level_m", "danger_level_m", "hfl_m",
                "water_level_0800hrs_m", "water_level_1800hrs_m",
                "forecast_waterlevel_m", "rainfall_mm"]:
        if col in df.columns:
            df[col] = df[col].apply(coerce_number)

    if "forecast_time" in df.columns:
        df["forecast_time"] = df["forecast_time"].apply(coerce_time)
    if "forecast_date" in df.columns:
        df["forecast_date"] = df["forecast_date"].apply(coerce_date)

def build_unique_ids(n_rows, date_str, session):
    return [f"{i+1}_{date_str}_{session}" for i in range(n_rows)]

# --- NEW: drop only real junk at the top; never blindly drop index 0/1
HEADER_TOKENS = ("warning", "danger", "h.f.l", "hfl", "water level", "forecast", "rainfall", "remarks", "trend", "station", "district", "sl")

def row_looks_like_headerish(series) -> bool:
    text = " ".join(str(x) for x in series if pd.notna(x)).lower()
    return any(tok in text for tok in HEADER_TOKENS)

def keep_numeric_slno(df: pd.DataFrame) -> pd.DataFrame:
    if "sl_no" not in df.columns:
        return df
    mask = df["sl_no"].astype(str).str.fullmatch(r"\d+")
    if mask.any():
        return df[mask].reset_index(drop=True)
    return df  # fallback if nothing matched

# ========= CORE: CLEAN A SINGLE PDF =========
def parse_pdf_to_df(pdf_path: str, is_first: bool) -> pd.DataFrame:
    fname = os.path.basename(pdf_path)
    date_str = extract_date_from_name(fname)
    session  = detect_session_from_name(fname)

    #tables = camelot.read_pdf(pdf_path, pages="1-end", flavor="lattice")
    tables = camelot.read_pdf(pdf_path, pages="1-end", flavor="lattice", split_text = True)
    if tables.n == 0:
        #tables = camelot.read_pdf(pdf_path, pages="1-end", flavor="stream")
        tables = camelot.read_pdf(pdf_path, pages="1-end", flavor="stream", split_text = True)
    if tables.n == 0:
        raise RuntimeError("No tables found")

    df = tables[0].df.copy()

    # Set header from first row once (do NOT drop any data rows yet)
    if isinstance(df.columns[0], int):
        df.columns = df.iloc[0]
        df = df.drop(index=0).reset_index(drop=True)

    # Normalize headers (expands forecast, fixes rainfall)
    headers = finalize_headers(df.columns)
    df.columns = headers

    # Drop only header-like/unit rows at the very top (0..2), if present
    # This prevents losing the first real record.
    for _ in range(3):
        if len(df) and row_looks_like_headerish(df.iloc[0]):
            df = df.drop(index=0).reset_index(drop=True)
#---------------------------------------------------------------------------------------------------------
    # Keep only rows with numeric sl_no when available (robust data guard), switch it off for all data entry
    df = keep_numeric_slno(df)
#--------------------------------------------------------------------------------------------------------------
    # Ensure forecast triple exists
    for col in ["forecast_waterlevel_m", "forecast_time", "forecast_date"]:
        if col not in df.columns:
            df[col] = None

    # Ensure trend, trend_01 exist
    if "trend" not in df.columns:
        df["trend"] = None
    if "trend_01" not in df.columns:
        df["trend_01"] = None

    # Ensure optional key cols exist (including rainfall_mm which is now normalized)
    for col in ["sl_no", "station", "district", "river", "fc_no", "rainfall_mm", "remarks"]:
        if col not in df.columns:
            df[col] = None

    # Fill warning/danger/hfl if missing
    fallback_fill_levels(df)

    # Route water level per session
    route_water_levels(df, session)

    # Coerce numeric/time/date types (includes rainfall_mm → numeric)
    coerce_types(df)

    # Forward fill river name within the bulletin
    df["river"] = df["river"].replace("", None).ffill()

    # Unique ID + source
    df.insert(0, "unique_id", build_unique_ids(len(df), date_str, session))
    df["source_file"] = fname

    # Align to final columns
    for col in FINAL_COLS:
        if col not in df.columns:
            df[col] = None
    df = df[FINAL_COLS]

    # Drop obvious noise
    df = df[~(df["station"].isna() & df["district"].isna())].reset_index(drop=True)

    return df

# ========= BATCH PROCESS =========
def process_folder(folder_path: str):
    files = sorted(
        [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")],
        key=extract_file_number
    )

    first = True
    total = 0
    for f in files:
        pdf_path = os.path.join(folder_path, f)
        print(f"Processing: {f}")
        try:
            df = parse_pdf_to_df(pdf_path, is_first=first)
            first = False

            df = df.where(df.notna(), None)
            df.to_sql(TABLE_NAME, ENGINE, if_exists="append", index=False)
            total += len(df)
            print(f"  → inserted {len(df)} rows")
        except Exception as e:
            print(f"  × failed: {e}")

    print(f"\n✅ Done. Inserted total {total} rows into '{TABLE_NAME}'")

if __name__ == "__main__":
    process_folder(FOLDER_PATH)



