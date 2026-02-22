from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing Supabase environment variables")