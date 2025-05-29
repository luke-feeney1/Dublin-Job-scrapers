from serpapi import GoogleSearch
import pandas as pd
import datetime
import json
import time
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

role = "Software Engineer"
city = "Dublin, Ireland"
filter_by_keywords = ["Software Engineer", "Software Developer", "Graduate Software Engineer"]

def parse_posted_at(text):
    if not text:
        return None
    
    text = text.lower().strip()
    now = datetime.datetime.now()
    
    if any(x in text for x in ["just", "few seconds"]):
        return now
    
    text = text.replace("ago", "").strip()
    parts = text.split()
    
    if len(parts) < 2:
        return None
    
    try:
        value = int(parts[0])
    except ValueError:
        return None
    
    unit = parts[1]
    
    if "minute" in unit:
        return now - datetime.timedelta(minutes=value)
    elif "hour" in unit:
        return now - datetime.timedelta(hours=value)
    elif "day" in unit:
        return now - datetime.timedelta(days=value)
    elif "week" in unit:
        return now - datetime.timedelta(weeks=value)
    elif "month" in unit:
        return now - datetime.timedelta(days=value * 30)
    
    return None

print(f"🔍 Searching for '{role}' in {city}...")

filtered_jobs = []
params = {
    "engine": "google_jobs",
    "q": role,
    "location": city,
    "hl": "en",
    "api_key": API_KEY
}

page_count = 0
max_pages = 5

while page_count < max_pages:
    print(f"\n🔍 Page {page_count + 1} scraping...")
    search = GoogleSearch(params)
    results = search.get_dict()
    
    if "error" in results:
        print("Error:", results["error"])
        break
    
    jobs = results.get("jobs_results", [])
    print(f"➡️ Got {len(jobs)} jobs.")
    
    for job in jobs:
        title = job.get("title", "")
        if any(keyword.lower() in title.lower() for keyword in filter_by_keywords):
            filtered_jobs.append({
                "title": title,
                "company": job.get("company_name"),
                "location": job.get("location"),
                "publish_time": parse_posted_at(job.get("detected_extensions", {}).get("posted_at")),
                "link": job.get("apply_options", [{}])[0].get("link", job.get("share_link", ""))
            })
    
    next_token = results.get("serpapi_pagination", {}).get("next_page_token")
    if not next_token:
        print("🚫 No more pages.")
        break
    
    params["next_page_token"] = next_token
    page_count += 1
    time.sleep(1.5)

df = pd.DataFrame(filtered_jobs)

if df.empty:
    print("No jobs found.")
else:
    df = df.sort_values(by="publish_time", ascending=False, na_position="last")
    df = df.head(30)
    
    # Save as both CSV and Excel
    df.to_csv("dublin_jobs_top30.csv", index=False, encoding="utf-8-sig")
    df.to_excel("dublin_jobs_top30.xlsx", index=False, engine='openpyxl')
    
    print(f"✅ Saved {len(df)} jobs to dublin_jobs_top30.csv")
    print(f"✅ Saved {len(df)} jobs to dublin_jobs_top30.xlsx")

with open("dublin_jobs_raw_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✅ Saved raw results to dublin_jobs_raw_results.json")