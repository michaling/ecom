# globals.py
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SERVICE_ROLE_KEY = os.getenv("SERVICE_ROLE_KEY")

# Shared instances
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase.postgrest.auth(SERVICE_ROLE_KEY)

# OpenAI key
OPENAI_KEY = os.getenv("OPENAI_API_KEY")