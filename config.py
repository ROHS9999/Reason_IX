"""Central settings. Every tunable number lives here so you can explain (and change) it in one place."""
import os
from dotenv import load_dotenv

load_dotenv()

# langchain-groq reads GROQ_API_KEY from the environment, we just fail early if it is missing.
if not os.getenv("GROQ_API_KEY"):
    raise EnvironmentError("GROQ_API_KEY environment variable is required (put it in .env).")

# Groq shut down llama-3.1-8b-instant / llama-3.3-70b on 16 Aug 2026. gpt-oss-20b is the fast production model;
# switch to "openai/gpt-oss-120b" for better judgement (zip 3 compares them with numbers).
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
EMBED_MODEL = "all-MiniLM-L6-v2"

# --- storage -----------------------------------------------------------------
DATA_DIR = os.getenv("DATA_DIR", "data")          # per-session JSON state lives in data/sessions/
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")     # persistent vector DB
MAX_SESSIONS_IN_MEMORY = 50

# --- chunking (sentence-aware, with overlap; chunks never cross a PDF page) --------
CHUNK_CHARS = 2000           # about 330 words
CHUNK_OVERLAP = 200          # last sentences of a chunk are repeated at the start of the next one

# --- retrieval for /compare (hybrid search + rerank) -------------------------------
FETCH_K = 12                 # candidates taken from EACH retriever (vectors, BM25)
USE_RERANKER = os.getenv("USE_RERANKER", "1") == "1"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# --- claim extraction (step 1) ----------------------------------------------
MAX_CHUNKS_PER_SOURCE = int(os.getenv("MAX_CHUNKS_PER_SOURCE", "5"))    # evenly spread over the document; ONE LLM call per source reads all of them
MAX_CLAIMS_PER_SOURCE = 12

# --- cross-source pairing (step 2) ------------------------------------------
PAIR_TOP_K = 2               # for each claim, only its 2 most similar claims in every OTHER source
PAIR_MIN_SIMILARITY = 0.45   # cosine similarity; below this the claims are about different things
MAX_PAIRS = int(os.getenv("MAX_PAIRS", "20"))               # all pairs are judged in ONE batched LLM call

# --- verification step of the LangGraph pipeline ----------------------------------
VERIFY_MODEL = os.getenv("VERIFY_MODEL", "openai/gpt-oss-120b")   # bigger model re-checks shaky conflicts
VERIFY_BELOW = 75            # contradictions with confidence below this get a second opinion
MAX_VERIFY = 10

# --- hallucination guard: every extracted claim is checked against its own source text (NLI) ----
NLI_MODEL = "cross-encoder/nli-deberta-v3-base"
GUARD_MODE = os.getenv("GUARD_MODE", "filter")   # filter = drop unsupported claims | flag = only mark them | off
GUARD_ENTAIL = 0.5           # NLI says the source text entails the claim with at least this probability
GUARD_CONTRADICT = 0.5       # ... or the quote is verbatim AND the source does not contradict the claim by this much
MIN_PAIR_SUPPORT = float(os.getenv("MIN_PAIR_SUPPORT", "0.2"))   # claims whose NLI support is below this are shown but never compared

# --- web verification (on demand, per claim) ----------------------------------------
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")  # optional; without it the keyless `ddgs` package is used
WEB_RESULTS = 5
MAX_WEB_CHECKS = 30          # per session

# --- API limits + security -----------------------------------------------------------
ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
MAX_FILES = 10
MAX_FILE_MB = 20
MAX_TEXT_CHARS = 200_000
MAX_URLS = 5
MAX_URL_BYTES = 5_000_000

# --- rate limiting (per client IP, in memory; protects your Groq quota on a public deployment) ----------
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"
RATE_UPLOADS_PER_HOUR = int(os.getenv("RATE_UPLOADS_PER_HOUR", "20"))
RATE_QUESTIONS_PER_HOUR = int(os.getenv("RATE_QUESTIONS_PER_HOUR", "60"))
RATE_WEB_CHECKS_PER_HOUR = int(os.getenv("RATE_WEB_CHECKS_PER_HOUR", "30"))
TRUST_PROXY = os.getenv("TRUST_PROXY", "0") == "1"   # set to 1 behind a reverse proxy (Cloud Run, nginx) to use X-Forwarded-For

# --- LLM calls ---------------------------------------------------------------
LLM_RETRIES = 4
LLM_RETRY_WAIT = 5           # seconds, multiplied by the attempt number (only used for 429 / 5xx errors)
LLM_WORKERS = 4              # sources are analysed in parallel
