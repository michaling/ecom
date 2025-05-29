# globals.py
from supabase import create_client

# Supabase credentials
SUPABASE_URL = "https://nallltanfjxhuaxvlwaf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5hbGxsdGFuZmp4aHVheHZsd2FmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3NTA5NzAsImV4cCI6MjA2MTMyNjk3MH0.QJi8v8eKu2QOEGPyRbgGL7Yaaj3zj22Mi8PEDz6WcbE"

# Shared instances
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
