"""Full ShelfIQ v3.0 API test — all 12 endpoint groups."""
import httpx

BASE = "http://127.0.0.1:8000"

print("=" * 65)
print("  ShelfIQ v3.0 — Full API Verification")
print("=" * 65)

# 1. Health
r = httpx.get(f"{BASE}/health")
h = r.json()
print(f"\n 1. Health            {r.status_code}  DB={h['db']}  ML={h['ml_models'][:30]}")

# 2. Login
r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": "owner@rajesh-supermart.in", "password": "owner123"})
token = r.json()["access_token"]
user = r.json()["user"]
H = {"Authorization": f"Bearer {token}"}
print(f" 2. Auth/Login        {r.status_code}  {user['name']} ({user['role']})")

# 3. Events
r = httpx.get(f"{BASE}/api/v1/events/upcoming", headers=H)
events = r.json()
print(f" 3. Events/Upcoming   {r.status_code}  {events['total']} events")

# 4. Forecast
r = httpx.get(f"{BASE}/api/v1/forecast/SKU001?store_id=STORE01", headers=H)
if r.status_code == 200:
    fc = r.json()
    print(f" 4. Forecast/SKU001   {r.status_code}  {len(fc['data'])} points, {len(fc['festival_annotations'])} festivals")
else:
    print(f" 4. Forecast/SKU001   {r.status_code}  {r.text[:60]}")

# 5. Compliance
r = httpx.get(f"{BASE}/api/v1/compliance/STORE01", headers=H)
c = r.json()
print(f" 5. Compliance        {r.status_code}  {c['overall_score']}% Grade {c['grade']}, {len(c['violations'])} violations")

# 6. Heatmap
r = httpx.get(f"{BASE}/api/v1/analytics/heatmap?store_id=STORE01", headers=H)
hm = r.json()
print(f" 6. Heatmap           {r.status_code}  {len(hm['data'])} cells")

# 7. Revenue Recovery
r = httpx.get(f"{BASE}/api/v1/analytics/revenue-recovery?store_id=STORE01", headers=H)
rv = r.json()
print(f" 7. Revenue Recovery  {r.status_code}  Lost=Rs{rv['total_revenue_lost']:.0f} Recovered=Rs{rv['total_revenue_recovered']:.0f} Rate={rv['recovery_rate']}%")

# 8. Alerts
r = httpx.get(f"{BASE}/api/v1/alerts", headers=H)
al = r.json()
print(f" 8. Alerts            {r.status_code}  {al['total']} alerts, page {al['page']}")

# 9. Shelves
r = httpx.get(f"{BASE}/api/v1/shelves/STORE01", headers=H)
print(f" 9. Shelves           {r.status_code}")

# 10. Billing Plans
r = httpx.get(f"{BASE}/api/v1/billing/plans", headers=H)
bp = r.json()
plan_names = [p['name'] for p in bp['plans']]
print(f"10. Billing Plans     {r.status_code}  {', '.join(plan_names)} (INR, +GST)")

# 11. Billing Status
r = httpx.get(f"{BASE}/api/v1/billing/status", headers=H)
bs = r.json()
print(f"11. Billing Status    {r.status_code}  Plan={bs['plan']} Status={bs['status']} {bs.get('days_left','')}d left")

# 12. QC Platforms
r = httpx.get(f"{BASE}/api/v1/qcommerce/platforms", headers=H)
qc = r.json()
qc_names = [p['name'] for p in qc['platforms']]
print(f"12. QC Platforms      {r.status_code}  {', '.join(qc_names)}")

# 13. QC Sync (stub)
r = httpx.post(f"{BASE}/api/v1/qcommerce/sync?platform=blinkit&store_id=STORE01", headers=H)
qs = r.json()
print(f"13. QC Sync (Blinkit) {r.status_code}  {qs.get('status')}, {qs.get('items_synced',0)} items")

# 14. QC Orders (stub)
r = httpx.get(f"{BASE}/api/v1/qcommerce/orders?platform=zepto&store_id=STORE01", headers=H)
qo = r.json()
print(f"14. QC Orders (Zepto) {r.status_code}  {qo.get('total_orders',0)} orders")

# 15. Root
r = httpx.get(f"{BASE}/")
print(f"15. Root              {r.status_code}")

# Summary
total = 15
passed = sum(1 for _ in range(1))  # placeholder
print("\n" + "=" * 65)
print(f"  All {total} endpoints tested. Swagger UI: {BASE}/docs")
print("  Frontend: http://localhost:5173")
print("=" * 65)
