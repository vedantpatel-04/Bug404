"""
Shelf Optimizer Dashboard Page — AI Shelf Arrangement Optimizer.
Displays optimization results, tier breakdowns, revenue lift comparison,
and the interactive optimized planogram grid.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import json

from dashboard.components.kpi_cards import (
    render_kpi_row,
    render_section_header,
    render_page_header,
    render_footer,
)
from config.settings import (
    STORE_CONFIG,
    OPTIMIZER_OUTPUT_DIR,
    EYE_LEVEL_SHELVES,
    SHELF_VISIBILITY_MULTIPLIER,
    DATABASE_PATH,
    POS_DATA_DIR,
)


def _load_optimized_planogram(store_id: str) -> dict | None:
    """Load the optimized planogram JSON for a store."""
    path = OPTIMIZER_OUTPUT_DIR / f"optimized_planogram_{store_id.lower()}.json"
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return None


def _load_sku_metrics(store_id: str) -> pd.DataFrame:
    """Load SKU metrics from the database for the given store."""
    import sqlite3
    if not DATABASE_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(DATABASE_PATH))
    try:
        df = pd.read_sql_query("""
            SELECT
                pt.sku_id,
                pt.product_name,
                pt.category,
                AVG(pt.unit_price) AS unit_price,
                SUM(pt.quantity_sold) AS total_quantity,
                SUM(pt.revenue) AS total_revenue,
                COUNT(DISTINCT pt.date) AS num_days
            FROM pos_transactions pt
            WHERE pt.store_id = ?
            GROUP BY pt.sku_id, pt.product_name, pt.category
            ORDER BY total_revenue DESC
        """, conn, params=(store_id,))
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def _load_engagement(store_id: str) -> pd.DataFrame:
    """Load engagement data for the store."""
    path = POS_DATA_DIR / "customer_engagement.csv"
    if path.exists():
        df = pd.read_csv(str(path))
        return df[df["store_id"] == store_id].reset_index(drop=True)
    return pd.DataFrame()


def _compute_tier(composite: float, p80: float, p50: float) -> str:
    if composite >= p80:
        return "Premium"
    elif composite >= p50:
        return "Standard"
    return "Economy"


def render(store_id: str):
    """Render the Shelf Optimizer page."""

    render_page_header("AI OPTIMIZATION", "Shelf Arrangement Optimizer")

    planogram_data = _load_optimized_planogram(store_id)
    sales_df = _load_sku_metrics(store_id)
    engagement_df = _load_engagement(store_id)

    if planogram_data is None or sales_df.empty:
        st.markdown("""
        <div class="panel" style="padding:40px;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:12px;">&#x1F6D2;</div>
            <div style="color:#dbe2f9;font-size:1.1rem;font-weight:700;margin-bottom:6px;">
                No Optimized Planogram Found
            </div>
            <div style="color:#bcc9ca;font-size:0.82rem;margin-bottom:20px;">
                Run the optimizer to generate results for this store.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Run Optimizer Now", key="run_opt", use_container_width=False):
            with st.spinner("Running full optimization pipeline..."):
                try:
                    from optimization.shelf_optimizer import optimize_store, PlanogramBuilder
                    planogram_obj, _ = optimize_store(store_id)
                    PlanogramBuilder().save_planogram(planogram_obj)
                    st.success("Optimization complete! Refreshing...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Optimization failed: {e}")
        render_footer()
        return

    # ── Compute metrics for display ──
    config = STORE_CONFIG[store_id]
    total_slots = config["aisles"] * config["shelves_per_aisle"] * config["sections_per_shelf"]

    # Count filled sections
    filled = 0
    eye_level_skus = set()
    all_placed_skus: dict[str, int] = {}  # sku_id → shelf_number
    for aisle in planogram_data.get("aisles", []):
        for shelf in aisle.get("shelves", []):
            for sec in shelf.get("sections", []):
                if sec.get("sku_id", "EMPTY") != "EMPTY":
                    filled += 1
                    all_placed_skus[sec["sku_id"]] = shelf["shelf_number"]
                    if shelf["shelf_number"] in EYE_LEVEL_SHELVES:
                        eye_level_skus.add(sec["sku_id"])

    # Merge sales + engagement for tier calculation
    merged = sales_df.copy()
    if not engagement_df.empty:
        merged = merged.merge(
            engagement_df[["sku_id", "impression_count", "pick_count", "conversion_rate"]],
            on="sku_id", how="left"
        )
    for col in ["impression_count", "pick_count", "conversion_rate"]:
        if col not in merged.columns:
            merged[col] = 0
    merged = merged.fillna(0)

    num_weeks = max(merged["num_days"].max() / 7.0, 1.0)
    merged["sales_velocity"] = merged["total_quantity"] / num_weeks
    merged["profit_contribution"] = merged["total_quantity"] * merged["unit_price"]
    max_imp = max(merged["impression_count"].max(), 1)
    merged["engagement_score"] = 0.6 * merged["conversion_rate"] + 0.4 * (merged["impression_count"] / max_imp)

    for col in ["sales_velocity", "profit_contribution", "engagement_score"]:
        mx = merged[col].max()
        merged[f"{col}_norm"] = merged[col] / mx if mx > 0 else 0
    merged["composite"] = 0.4 * merged["sales_velocity_norm"] + 0.35 * merged["profit_contribution_norm"] + 0.25 * merged["engagement_score_norm"]

    p80 = merged["composite"].quantile(0.80)
    p50 = merged["composite"].quantile(0.50)
    merged["tier"] = merged["composite"].apply(lambda x: _compute_tier(x, p80, p50))

    premium_count = (merged["tier"] == "Premium").sum()
    standard_count = (merged["tier"] == "Standard").sum()
    economy_count = (merged["tier"] == "Economy").sum()

    premium_skus_set = set(merged[merged["tier"] == "Premium"]["sku_id"])
    premium_at_eye = len(premium_skus_set & eye_level_skus)
    eye_pct = int(premium_at_eye / max(len(premium_skus_set), 1) * 100)

    # Revenue estimation
    avg_vis = float(np.mean(list(SHELF_VISIBILITY_MULTIPLIER.values())))
    baseline_rev = sum(merged["sales_velocity"] * merged["unit_price"] * avg_vis)
    optimized_rev = 0.0
    for _, row in merged.iterrows():
        base = row["sales_velocity"] * row["unit_price"]
        if row["sku_id"] in all_placed_skus:
            vis = SHELF_VISIBILITY_MULTIPLIER.get(all_placed_skus[row["sku_id"]], 1.0)
        else:
            vis = avg_vis
        optimized_rev += base * vis
    lift_pct = ((optimized_rev - baseline_rev) / baseline_rev * 100) if baseline_rev > 0 else 0

    # ── KPI Row ──
    render_kpi_row([
        {
            "label": "Revenue Lift",
            "value": f"+{lift_pct:.1f}%",
            "chip_text": f"${optimized_rev - baseline_rev:+,.0f}/wk",
            "icon": "&#x1F4C8;",
            "accent": "primary" if lift_pct > 0 else "error",
        },
        {
            "label": "SKUs Placed",
            "value": f"{filled}/{total_slots}",
            "chip_text": f"{filled/total_slots*100:.0f}% fill",
            "icon": "&#x1F4E6;",
            "accent": "primary",
        },
        {
            "label": "Eye-Level Premium",
            "value": f"{premium_at_eye}/{premium_count}",
            "chip_text": f"{eye_pct}% coverage",
            "icon": "&#x1F441;",
            "accent": "primary" if eye_pct >= 70 else "error",
        },
        {
            "label": "Weekly Revenue (Opt.)",
            "value": f"${optimized_rev:,.0f}",
            "chip_text": f"vs ${baseline_rev:,.0f} baseline",
            "icon": "&#x1F4B0;",
            "accent": "secondary",
        },
    ])

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Two-column layout: Tier Breakdown + Planogram Grid ──
    col_left, col_right = st.columns([2, 3])

    with col_left:
        # Tier Breakdown Panel
        render_section_header("SKU Tier Breakdown", f"{len(merged)} products scored")
        _render_tier_breakdown(merged, premium_count, standard_count, economy_count)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # Top performers table
        render_section_header("Top 10 Performers", "By composite score")
        _render_top_performers(merged)

    with col_right:
        render_section_header("Optimized Planogram Layout", config["name"])
        _render_planogram_grid(planogram_data, merged)

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Category Distribution ──
    render_section_header("Category Distribution Across Aisles")
    _render_category_distribution(planogram_data)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # ── Actions Row ──
    act_c1, act_c2, act_c3, _ = st.columns([1, 1, 1, 2])
    with act_c1:
        # Download optimized planogram JSON
        path = OPTIMIZER_OUTPUT_DIR / f"optimized_planogram_{store_id.lower()}.json"
        if path.exists():
            st.download_button(
                "Download Planogram JSON",
                data=path.read_text(),
                file_name=f"optimized_planogram_{store_id.lower()}.json",
                mime="application/json",
                key="dl_planogram",
                use_container_width=True,
            )
    with act_c2:
        if st.button("Re-run Optimizer", key="rerun_opt", use_container_width=True):
            with st.spinner("Re-optimizing..."):
                try:
                    from optimization.shelf_optimizer import optimize_store, PlanogramBuilder
                    planogram_obj, _ = optimize_store(store_id)
                    PlanogramBuilder().save_planogram(planogram_obj)
                    st.success("Done!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
    with act_c3:
        # Download tier report CSV
        csv_data = merged[["sku_id", "product_name", "category", "tier", "composite",
                           "sales_velocity", "profit_contribution", "engagement_score"]].to_csv(index=False)
        st.download_button(
            "Download Tier Report CSV",
            data=csv_data,
            file_name=f"sku_tier_report_{store_id.lower()}.csv",
            mime="text/csv",
            key="dl_tier_csv",
            use_container_width=True,
        )

    render_footer()


# ══════════════════════════════════════════════════════════════
#  Sub-render functions
# ══════════════════════════════════════════════════════════════

def _render_tier_breakdown(df: pd.DataFrame, premium: int, standard: int, economy: int):
    """Render the tier breakdown bars."""
    total = len(df)
    tiers = [
        ("Premium", premium, "#6ee6ee", "Top 20% — eye-level placement"),
        ("Standard", standard, "#cecb5b", "Mid 30% — standard shelves"),
        ("Economy", economy, "#69758a", "Bottom 50% — bottom/top shelves"),
    ]
    html_parts = []
    for name, count, color, desc in tiers:
        pct = count / total * 100 if total > 0 else 0
        html_parts.append(
            f'<div style="margin-bottom:14px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
            f'<div>'
            f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};margin-right:6px;"></span>'
            f'<span style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">{name}</span>'
            f'<span style="color:#69758a;font-size:0.7rem;margin-left:6px;">{desc}</span>'
            f'</div>'
            f'<span style="color:{color};font-size:0.85rem;font-weight:700;">{count} SKUs</span>'
            f'</div>'
            f'<div class="compliance-bar-track">'
            f'<div class="compliance-bar-fill" style="width:{pct}%;background:{color};"></div>'
            f'</div>'
            f'</div>'
        )

    inner = ''.join(html_parts)
    st.markdown(
        f'<div class="panel" style="padding:18px;">{inner}</div>',
        unsafe_allow_html=True,
    )


def _hex_to_rgba(hex_color: str, alpha: float = 0.12) -> str:
    """Convert hex color to rgba string."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _render_top_performers(df: pd.DataFrame):
    """Render the top 10 performing SKUs table."""
    top = df.nlargest(10, "composite")
    rows = ""
    for _, row in top.iterrows():
        tier = row["tier"]
        t_color = "#6ee6ee" if tier == "Premium" else "#cecb5b" if tier == "Standard" else "#69758a"
        t_bg = _hex_to_rgba(t_color, 0.12)
        p_name = row['product_name']
        s_id = row['sku_id']
        score = f"{row['composite']:.3f}"
        revenue = f"${row['total_revenue']:,.0f}"
        rows += (
            '<tr style="border-bottom:1px solid rgba(61,73,74,0.08);">'
            '<td style="padding:8px 10px;">'
            f'<div style="color:#dbe2f9;font-size:0.78rem;font-weight:600;">{p_name}</div>'
            f'<div style="color:#69758a;font-size:0.65rem;">{s_id}</div>'
            '</td>'
            '<td style="padding:8px 10px;text-align:center;">'
            f'<span style="color:{t_color};font-size:0.7rem;font-weight:700;background:{t_bg};padding:2px 8px;border-radius:4px;">{tier}</span>'
            '</td>'
            f'<td style="padding:8px 10px;text-align:right;color:#dbe2f9;font-size:0.78rem;font-weight:600;">{score}</td>'
            f'<td style="padding:8px 10px;text-align:right;color:#bcc9ca;font-size:0.78rem;">{revenue}</td>'
            '</tr>'
        )

    table_html = (
        '<div class="panel" style="overflow-x:auto;padding:0;">'
        '<table style="width:100%;border-collapse:collapse;">'
        '<thead><tr style="border-bottom:1px solid rgba(61,73,74,0.15);">'
        '<th style="text-align:left;padding:10px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;">Product</th>'
        '<th style="text-align:center;padding:10px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;">Tier</th>'
        '<th style="text-align:right;padding:10px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;">Score</th>'
        '<th style="text-align:right;padding:10px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;">Revenue</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


def _render_planogram_grid(planogram: dict, metrics_df: pd.DataFrame):
    """Render a visual grid of the optimized planogram."""
    # Build tier lookup
    tier_lookup: dict[str, str] = {}
    for _, row in metrics_df.iterrows():
        tier_lookup[row["sku_id"]] = row.get("tier", "Economy")

    aisles = planogram.get("aisles", [])
    # Show max 4 aisles at a time in dropdown
    aisle_names = [f"{a['aisle_id']} — {a['aisle_name']}" for a in aisles]
    selected_aisle_idx = st.selectbox("Select Aisle", range(len(aisle_names)),
                                       format_func=lambda i: aisle_names[i],
                                       key="opt_aisle_select")

    if selected_aisle_idx is not None and selected_aisle_idx < len(aisles):
        aisle = aisles[selected_aisle_idx]
        shelves = aisle.get("shelves", [])
        # Sort shelves top to bottom (highest shelf number first for visual top-down)
        shelves_sorted = sorted(shelves, key=lambda s: s["shelf_number"], reverse=True)

        grid_html = ""
        for shelf in shelves_sorted:
            snum = shelf["shelf_number"]
            is_eye = snum in EYE_LEVEL_SHELVES
            shelf_badge = '<span style="background:rgba(110,230,238,0.15);color:#6ee6ee;font-size:0.55rem;padding:2px 6px;border-radius:3px;font-weight:600;">EYE LEVEL</span>' if is_eye else ""
            label_bg = "rgba(110,230,238,0.06)" if is_eye else "transparent"

            cells = ""
            for sec in shelf.get("sections", []):
                sku_id = sec.get("sku_id", "EMPTY")
                if sku_id == "EMPTY":
                    cells += (
                        '<div style="flex:1;min-width:60px;height:56px;background:rgba(20,27,44,0.4);'
                        'border:1px dashed rgba(61,73,74,0.2);border-radius:6px;'
                        'display:flex;align-items:center;justify-content:center;'
                        'color:#3d494a;font-size:0.55rem;">&mdash;</div>'
                    )
                else:
                    tier = tier_lookup.get(sku_id, "Economy")
                    if tier == "Premium":
                        bg = "rgba(110,230,238,0.12)"
                        border = "1px solid rgba(110,230,238,0.3)"
                        dot = "#6ee6ee"
                    elif tier == "Standard":
                        bg = "rgba(206,203,91,0.08)"
                        border = "1px solid rgba(206,203,91,0.2)"
                        dot = "#cecb5b"
                    else:
                        bg = "rgba(105,117,138,0.08)"
                        border = "1px solid rgba(105,117,138,0.15)"
                        dot = "#69758a"

                    name = sec.get("product_name", "")[:14]
                    full_name = sec.get("product_name", "")
                    cells += (
                        f'<div style="flex:1;min-width:60px;height:56px;background:{bg};'
                        f'border:{border};border-radius:6px;padding:4px 6px;'
                        f'display:flex;flex-direction:column;justify-content:center;'
                        f'cursor:default;" title="{full_name} ({sku_id})">'
                        f'<div style="display:flex;align-items:center;gap:3px;">'
                        f'<span style="width:5px;height:5px;border-radius:50%;background:{dot};flex-shrink:0;"></span>'
                        f'<span style="color:#dbe2f9;font-size:0.6rem;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name}</span>'
                        f'</div>'
                        f'<div style="color:#69758a;font-size:0.5rem;margin-top:2px;">{sku_id}</div>'
                        f'</div>'
                    )

            grid_html += (
                f'<div style="margin-bottom:8px;background:{label_bg};border-radius:8px;padding:6px 8px;">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                f'<span style="color:#bcc9ca;font-size:0.65rem;font-weight:600;">Shelf {snum}</span>'
                f'{shelf_badge}'
                f'</div>'
                f'<div style="display:flex;gap:6px;">'
                f'{cells}'
                f'</div>'
                f'</div>'
            )

        st.markdown(
            f'<div class="panel" style="padding:14px;">{grid_html}</div>',
            unsafe_allow_html=True,
        )


def _render_category_distribution(planogram: dict):
    """Show which categories ended up in which aisles."""
    aisle_categories: dict[str, dict[str, int]] = {}
    for aisle in planogram.get("aisles", []):
        aid = aisle["aisle_id"]
        aisle_categories[aid] = {}
        for shelf in aisle.get("shelves", []):
            for sec in shelf.get("sections", []):
                sku = sec.get("sku_id", "EMPTY")
                if sku != "EMPTY":
                    # We don't have category in planogram JSON directly,
                    # but product_name can help. Use a simple lookup via DB
                    cat = sec.get("category", "")
                    if not cat:
                        # Try to infer from product name patterns
                        cat = _infer_category(sec.get("product_name", ""))
                    aisle_categories[aid][cat] = aisle_categories[aid].get(cat, 0) + 1

    # Render as a compact grid
    rows = ""
    cat_colors = {
        "Beverages": "#4ecad2", "Snacks": "#cecb5b", "Dairy": "#a78bfa",
        "Bakery": "#f59e0b", "Canned Goods": "#69758a", "Frozen Foods": "#60a5fa",
        "Personal Care": "#f472b6", "Household": "#34d399", "Condiments": "#fb923c",
        "Cereals": "#c084fc", "Other": "#6b7280",
    }

    for aid, cats in sorted(aisle_categories.items()):
        if not cats:
            continue
        total = sum(cats.values())
        pills = ""
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            color = cat_colors.get(cat, "#6b7280")
            bg = _hex_to_rgba(color, 0.15)
            pills += (
                f'<span style="background:{bg};color:{color};font-size:0.65rem;'
                f'padding:3px 8px;border-radius:4px;font-weight:600;margin-right:4px;">'
                f'{cat} ({count})</span>'
            )

        rows += (
            '<div style="display:flex;align-items:center;gap:12px;padding:8px 0;'
            'border-bottom:1px solid rgba(61,73,74,0.06);">'
            f'<span style="color:#dbe2f9;font-size:0.78rem;font-weight:700;min-width:40px;">{aid}</span>'
            f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{pills}</div>'
            '</div>'
        )

    content = rows if rows else '<div style="color:#69758a;text-align:center;padding:20px;">No data</div>'
    st.markdown(
        f'<div class="panel" style="padding:14px;">{content}</div>',
        unsafe_allow_html=True,
    )


def _infer_category(product_name: str) -> str:
    """Simple heuristic to infer category from product name."""
    name = product_name.lower()
    if any(w in name for w in ["cola", "pepsi", "sprite", "juice", "water"]):
        return "Beverages"
    elif any(w in name for w in ["chips", "doritos", "pringles", "oreo", "kitkat"]):
        return "Snacks"
    elif any(w in name for w in ["milk", "yogurt", "cheese", "butter", "cream cheese"]):
        return "Dairy"
    elif any(w in name for w in ["bread", "croissant", "bagel", "muffin"]):
        return "Bakery"
    elif any(w in name for w in ["canned", "beans", "soup", "corn canned", "chickpeas", "tuna"]):
        return "Canned Goods"
    elif any(w in name for w in ["frozen", "ice cream", "fish fingers", "berries"]):
        return "Frozen Foods"
    elif any(w in name for w in ["shampoo", "toothpaste", "soap", "deodorant", "tissue"]):
        return "Personal Care"
    elif any(w in name for w in ["dish", "laundry", "trash", "paper towel", "sponge"]):
        return "Household"
    elif any(w in name for w in ["ketchup", "mustard", "soy sauce", "hot sauce", "olive oil"]):
        return "Condiments"
    elif any(w in name for w in ["flakes", "granola", "oatmeal", "krispies", "muesli"]):
        return "Cereals"
    return "Other"
