import csv
with open("remote_tech_leads.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
print(f"Total: {len(rows)} jobs")
for i, r in enumerate(rows[:3]):
    print(f"\n{i+1}. {r['company']}\n   Title: {r['title']}\n   URL:   {r['url']}")
