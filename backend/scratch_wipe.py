import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def wipe_concepts():
    print("Wiping all existing concepts to reset the mastery list...")
    # Delete all mastery records first (foreign key constraints)
    supabase.table("concept_mastery").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    # Delete the concepts themselves
    supabase.table("concepts").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    print("Concepts wiped successfully! You can now re-upload the PDF to generate a clean, short list.")

if __name__ == "__main__":
    wipe_concepts()
