#!/usr/bin/env python3
"""
AI-Powered Database Profiler (integrated, improved)
- Runs TPC-H queries in DuckDB
- Captures EXPLAIN ANALYZE (text)
- Captures JSON profiling (operator times)
- Generates context-aware, actionable recommendations (SQL snippets included)
- Logs results to query_log and saves per-query profile HTML (Plotly)
"""

import duckdb
import time
import sys
import re
import json
import pandas as pd
import plotly.express as px
import os
import tempfile
from datetime import datetime, UTC

DB_PATH = "complete_tpch.db"
PLOT_PROFILES = True   # set False to skip generating HTML plots

# Regex for EXPLAIN text parsing
ROWS_REGEX = re.compile(r'(\d+)\s+Rows')
TIME_REGEX = re.compile(r'\((\d+\.\d+)s\)')
JOIN_REGEX_PLAN = re.compile(r'\bJOIN\b', re.IGNORECASE)
AGG_REGEX_PLAN = re.compile(r'AGGREGATE', re.IGNORECASE)

# Regex for SQL text (expected intent)
JOIN_REGEX_SQL = re.compile(r'\bJOIN\b', re.IGNORECASE)
AGG_REGEX_SQL = re.compile(r'\b(SUM|AVG|COUNT|MIN|MAX)\b', re.IGNORECASE)
SUBSTRING_REGEX = re.compile(r'\bsubstring\s*\(|\bsubstr\s*\(', re.IGNORECASE)


# -------------------------
# Parsing Functions
# -------------------------
def parse_explain_analyze(explain_text: str):
    """
    Extract scanned_rows, returned_rows, exec_time_ms from textual EXPLAIN ANALYZE output.
    These heuristics are best-effort (DuckDB textual formats vary).
    """
    rows = [int(r) for r in ROWS_REGEX.findall(explain_text)]
    times = [float(t) for t in TIME_REGEX.findall(explain_text)]
    scanned_rows = max(rows) if rows else None
    # choose a reasonable candidate for returned rows (smallest positive)
    returned_rows = None
    if rows:
        positive = [r for r in rows if r >= 0]
        if positive:
            returned_rows = min(positive)
        else:
            returned_rows = 0
    exec_time_ms = max(times) * 1000 if times else None
    return scanned_rows, returned_rows, exec_time_ms


def count_expected_operators(sql_text: str):
    joins_expected = len(JOIN_REGEX_SQL.findall(sql_text))
    aggs_expected = len(AGG_REGEX_SQL.findall(sql_text))
    return joins_expected, aggs_expected


def count_detected_operators(explain_text: str):
    joins_detected = len(JOIN_REGEX_PLAN.findall(explain_text))
    aggs_detected = len(AGG_REGEX_PLAN.findall(explain_text))
    return joins_detected, aggs_detected


# -------------------------
# Profiling (JSON)
# -------------------------
def run_with_profiling(con, query, profile_path):
    """
    Enable JSON profiling, run the query, write JSON profile to profile_path.
    """
    con.execute("PRAGMA enable_profiling = 'json';")
    con.execute(f"PRAGMA profiling_output = '{profile_path}';")
    # standard is usually sufficient; 'detailed' yields more fields if available
    con.execute("PRAGMA profiling_mode = 'standard';")
    # Execute the query to generate profiling output
    con.execute(query).fetchall()
    con.execute("PRAGMA disable_profiling;")
    return profile_path


def parse_profile_json(profile_path):
    """
    Load the profiling JSON and return a DataFrame of operators:
    columns: id, parent, operator_type, time_s, rows_count
    """
    with open(profile_path, 'r') as f:
        j = json.load(f)

    rows = []

    def walk(node, parent="ROOT"):
        # Try common keys (DuckDB versions vary slightly)
        typ = node.get("operator_type") or node.get("operator") or node.get("name") or "UNKNOWN"
        # timings/ cardinality keys may vary; try several possibilities
        timing = node.get("operator_timing") or node.get("time") or node.get("timing", 0.0)
        # if operator_timing is object: try 'total' or 'time'
        if isinstance(timing, dict):
            timing = timing.get("time", timing.get("total", 0.0))
        try:
            time_s = float(timing)
        except Exception:
            time_s = 0.0
        card = node.get("operator_cardinality") or node.get("cardinality") or node.get("rows") or 0
        try:
            card = int(card)
        except Exception:
            card = 0

        node_id = f"{typ}-{len(rows)}"
        rows.append({
            "id": node_id,
            "parent": parent,
            "operator_type": typ,
            "time_s": time_s,
            "rows_count": card
        })
        for child in node.get("children", []) or []:
            walk(child, parent=node_id)

    # try common root locations
    if isinstance(j, dict) and "children" in j:
        for c in j["children"]:
            walk(c, parent="ROOT")
    else:
        walk(j, parent="ROOT")

    df = pd.DataFrame(rows)
    if df.empty:
        # safe fallback: return small empty DF
        return pd.DataFrame(columns=["id", "parent", "operator_type", "time_s", "rows_count"])
    return df


# -------------------------
# Recommendation Engine (SMART)
# -------------------------
# Operator -> set of recommendation templates with SQL snippets where applicable.
OPERATOR_TEMPLATES = {
    "TABLE_SCAN": {
        "short": "Full table scan detected",
        "reason": "Query performs a full table scan on a large table which often indicates missing index or predicate not sargable.",
        "suggestions": [
            {
                "action": "create_index",
                "template_sql": "CREATE INDEX IF NOT EXISTS idx_{table}_{col} ON {table}({col});",
                "detail": "Add index on filter column"
            },
            {
                "action": "computed_column",
                "template_sql": "ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col}_computed AS ({expr});\nCREATE INDEX IF NOT EXISTS idx_{table}_{col}_computed ON {table}({col}_computed);",
                "detail": "Add computed column for expression and index it"
            },
            {
                "action": "materialized_view",
                "template_sql": "CREATE MATERIALIZED VIEW IF NOT EXISTS mv_{table}_{hint} AS\nSELECT * FROM {table} WHERE {filter};",
                "detail": "Materialize filtered data for faster repeated queries"
            }
        ]
    },
    "HASH_JOIN": {
        "short": "Expensive hash join",
        "reason": "Join operation is spending substantial time. Ensure join keys are indexed and compatible.",
        "suggestions": [
            {
                "action": "index_join_keys",
                "template_sql": "CREATE INDEX IF NOT EXISTS idx_{table}_{join_key} ON {table}({join_key});",
                "detail": "Index join keys on join-side tables"
            },
            {
                "action": "materialized_join",
                "template_sql": "CREATE MATERIALIZED VIEW IF NOT EXISTS mv_join_{hint} AS\nSELECT a.*, b.* FROM {left} a JOIN {right} b ON a.{key}=b.{key};",
                "detail": "Precompute join results"
            }
        ]
    },
    "HASH_GROUP_BY": {
        "short": "Heavy aggregation (GROUP BY)",
        "reason": "Aggregation is expensive. Consider pre-aggregation or grouping by integer surrogate keys.",
        "suggestions": [
            {
                "action": "materialized_agg",
                "template_sql": "CREATE MATERIALIZED VIEW IF NOT EXISTS mv_aggr_{hint} AS\nSELECT {group_cols}, SUM({agg_col}) AS agg_val FROM {table} GROUP BY {group_cols};",
                "detail": "Pre-aggregate for frequent queries"
            },
            {
                "action": "use_surrogate",
                "template_sql": "-- Consider using an integer surrogate key for {group_col} and index it",
                "detail": "Convert group key to integer id for faster grouping"
            }
        ]
    },
    "ORDER_BY": {
        "short": "Sorting / ORDER BY heavy",
        "reason": "Sorting large result sets is costly; an index on the ORDER BY columns can help.",
        "suggestions": [
            {
                "action": "index_order",
                "template_sql": "CREATE INDEX IF NOT EXISTS idx_{table}_{col}_order ON {table}({col});",
                "detail": "Create index that supports ordering"
            }
        ]
    }
}

def extract_table_name(query_text, default="main_table"):
    """
    Try to extract the first table name from the SQL query.
    Falls back to default if nothing is found.
    """
    # Common FROM / JOIN patterns
    match = re.search(r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_text, re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_text, re.IGNORECASE)
    if match:
        return match.group(1)

    return default



def synthesize_recommendations(bottleneck_op, scanned_rows, returned_rows, joins_expected, joins_detected, aggs_expected, aggs_detected, query_text):
    """
    Produce human-readable recommendations and SQL snippets using:
      - bottleneck operator type
      - pattern detection in query text (substring usage, filters)
      - scan/return selectivity heuristic
    """
    recs = []
    snippets = []

    # Compute selectivity if possible
    selectivity = None
    if scanned_rows and returned_rows is not None:
        selectivity = returned_rows / max(scanned_rows, 1)

    if selectivity is not None and selectivity < 0.01:
        recs.append(f"Very low selectivity ({selectivity:.6f}) — consider indexing filter columns or partitioning.")
    elif selectivity is not None and selectivity < 0.1:
        recs.append(f"Low selectivity ({selectivity:.4f}) — indexing may help.")

    if bottleneck_op:
        op = bottleneck_op.upper()
        matched = None
        for key in OPERATOR_TEMPLATES.keys():
            if key in op:
                matched = OPERATOR_TEMPLATES[key]
                break
        if matched:
            recs.append(f"{matched['short']}: {matched['reason']}")

            # Detect table and filter cols
            tab = extract_table_name(query_text, default="unknown_table")
            filter_cols = re.findall(r'([a-zA-Z0-9_\.]+)\s*(?:=|>|<|IN|LIKE)', query_text, flags=re.IGNORECASE)
            simple_col = filter_cols[0].split('.')[-1] if filter_cols else None

            # Special: substring() detection
            if SUBSTRING_REGEX.search(query_text):
                inside = re.findall(r'substring\s*\(\s*([a-zA-Z0-9_\.]+)', query_text, flags=re.IGNORECASE)
                col = inside[0] if inside else simple_col
                if col:
                    colname = col.split('.')[-1]
                    snippet = (
                        f"ALTER TABLE {tab} ADD COLUMN IF NOT EXISTS {colname}_computed "
                        f"AS (substring({col},1,2));\n"
                        f"CREATE INDEX IF NOT EXISTS idx_{tab}_{colname}_computed "
                        f"ON {tab}({colname}_computed);"
                    )
                    snippets.append(snippet)
                    recs.append("Detected substring on a column — create a computed column and index it.")

            # If filter col exists → build specific index snippet
            elif simple_col:
                snippet = f"CREATE INDEX IF NOT EXISTS idx_{tab}_{simple_col} ON {tab}({simple_col});"
                snippets.append(snippet)
                recs.append(f"Suggest creating an index on {tab}({simple_col}).")

            # If no filter col but join bottleneck → try join keys
            elif "JOIN" in op:
                snippet = f"-- Ensure join keys are indexed\nCREATE INDEX IF NOT EXISTS idx_{tab}_joinkey ON {tab}(<join_key>);"
                snippets.append(snippet)
                recs.append(f"Suggest indexing join keys on {tab}.")

            # Aggregations
            elif "GROUP_BY" in op or "AGGREGATE" in op:
                snippet = (
                    f"CREATE MATERIALIZED VIEW IF NOT EXISTS mv_aggr_{tab} AS\n"
                    f"SELECT <group_col>, SUM(<agg_col>) AS agg_val FROM {tab} GROUP BY <group_col>;"
                )
                snippets.append(snippet)
                recs.append(f"Suggest pre-aggregating results for {tab}.")

            # Sorting
            elif "ORDER" in op:
                snippet = f"CREATE INDEX IF NOT EXISTS idx_{tab}_order ON {tab}(<order_col>);"
                snippets.append(snippet)
                recs.append(f"Suggest indexing ORDER BY column(s) in {tab}.")

            else:
                recs.append("Suggested generic optimization — review execution plan for hotspots.")

    if joins_detected > 5 or joins_expected > 5:
        recs.append("Multiple joins detected — consider denormalization or materialized pre-joins.")
    if aggs_expected > 0 and scanned_rows and scanned_rows > 1_000_000:
        recs.append("Large aggregation over >1M rows — consider pre-aggregation or materialized view.")

    if not recs:
        recs.append("No obvious issues detected — query looks OK.")

    return {
        "recommendation_text": " | ".join(recs),
        "sql_snippets": snippets
    }



# -------------------------
# Main
# -------------------------
def main():
    reset = "--reset" in sys.argv

    with duckdb.connect(DB_PATH) as con:
        if reset:
            print("♻️ Resetting tables...")
            con.execute("DROP TABLE IF EXISTS query_workload;")
            con.execute("DROP TABLE IF EXISTS query_log;")

        # Create workload table (from built-in tpch queries)
        con.execute("""
        CREATE TABLE IF NOT EXISTS query_workload AS
        SELECT query_nr AS query_id, query AS query_text
        FROM tpch_queries();
        """)

        # Extended query_log to include snippets column
        con.execute("""
        CREATE TABLE IF NOT EXISTS query_log (
            query_id INTEGER,
            query_text VARCHAR,
            explain_text VARCHAR,
            exec_time_ms DOUBLE,
            scanned_rows BIGINT,
            returned_rows BIGINT,
            joins_expected INTEGER,
            joins_detected INTEGER,
            aggs_expected INTEGER,
            aggs_detected INTEGER,
            recommendation VARCHAR,
            recommendation_snippets VARCHAR,
            bottleneck_operator VARCHAR,
            logged_at TIMESTAMP
        );
        """)

        queries = con.execute("SELECT query_id, query_text FROM query_workload ORDER BY query_id").fetchall()

        for qid, qtext in queries:
            print(f"\n▶ Running Q{qid}...")
            print(f"   📝 Query (truncated): {qtext[:200].replace('\\n',' ')}\n")

            explain_text = ""
            scanned_rows = returned_rows = exec_time_ms = None
            joins_expected = joins_detected = aggs_expected = aggs_detected = 0
            bottleneck_op = None
            rec_text = ""
            rec_snips = []

            # 1) Run textual EXPLAIN ANALYZE (best-effort)
            try:
                # textual explain analyze often returns tuple rows; pick first text column found
                res = con.execute("EXPLAIN ANALYZE " + qtext).fetchall()
                if res and len(res) > 0:
                    # find the first string-like column
                    row0 = res[0]
                    explain_text = next((str(x) for x in row0 if isinstance(x, (str,))), str(row0))
                scanned_rows, returned_rows, exec_time_ms = parse_explain_analyze(explain_text)
                joins_expected, aggs_expected = count_expected_operators(qtext)
                joins_detected, aggs_detected = count_detected_operators(explain_text)
            except Exception as e:
                explain_text = f"EXPLAIN_FAILED: {e}"
                print("⚠️ Text EXPLAIN failed:", e)

            # 2) JSON profiling for operator-level times (best-effort)
            df_plan = pd.DataFrame()
            try:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
                profile_file = tmp.name
                tmp.close()
                run_with_profiling(con, qtext, profile_file)
                df_plan = parse_profile_json(profile_file)
                os.remove(profile_file)

                if not df_plan.empty:
                    # optional: save interactive plot
                    if PLOT_PROFILES:
                        fig = px.bar(
                            df_plan.sort_values("time_s", ascending=True),
                            x="time_s", y="operator_type", orientation="h",
                            title=f"Query {qid} Profile (Execution Time per Operator)",
                            labels={"time_s": "Execution Time (s)", "operator_type": "Operator"},
                        )
                        plot_filename = f"query_html_files/query_{qid}_profile.html"
                        fig.write_html(plot_filename)
                        print(f"📊 Plot saved to {plot_filename}")

                    # bottleneck operator
                    bottleneck_row = df_plan.loc[df_plan["time_s"].idxmax()]
                    bottleneck_op = str(bottleneck_row["operator_type"])
                    print("\n--- Bottleneck Operator ---")
                    print(bottleneck_row.to_string())
                else:
                    print("⚠️ Profiling produced empty operator list.")
            except Exception as e:
                print("⚠️ JSON profiling failed (maybe older DuckDB build):", e)

            # 3) Fallback: run the query normally to get exec time & returned rows
            try:
                t0 = time.perf_counter()
                rows = con.execute(qtext).fetchall()
                t1 = time.perf_counter()
                if returned_rows is None:
                    returned_rows = len(rows)
                if exec_time_ms is None:
                    exec_time_ms = (t1 - t0) * 1000.0
            except Exception as e:
                print("❌ Query execution failed:", e)

            # 4) Detected operators from explain_text (fallback counts)
            if joins_expected is None:
                joins_expected, aggs_expected = count_expected_operators(qtext)
            if joins_detected is None:
                joins_detected, aggs_detected = count_detected_operators(explain_text)

            # 5) Smart recommendations
            rec = synthesize_recommendations(
                bottleneck_op=bottleneck_op,
                scanned_rows=scanned_rows,
                returned_rows=returned_rows,
                joins_expected=joins_expected,
                joins_detected=joins_detected,
                aggs_expected=aggs_expected,
                aggs_detected=aggs_detected,
                query_text=qtext
            )
            rec_text = rec["recommendation_text"]
            rec_snips = rec["sql_snippets"]

            # 6) Insert into query_log
            try:
                con.execute("""
                INSERT INTO query_log
                (query_id, query_text, explain_text, exec_time_ms,
                 scanned_rows, returned_rows,
                 joins_expected, joins_detected,
                 aggs_expected, aggs_detected,
                 recommendation, recommendation_snippets, bottleneck_operator, logged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, [
                    qid, qtext, explain_text, exec_time_ms or 0.0,
                    scanned_rows or 0, returned_rows or 0,
                    joins_expected or 0, joins_detected or 0,
                    aggs_expected or 0, aggs_detected or 0,
                    rec_text, "\n\n".join(rec_snips), bottleneck_op or "", datetime.now(UTC)
                ])
            except Exception as e:
                print("❌ Failed to write to query_log:", e)

            # 7) Console summary
            print(f"✅ Logged Q{qid}: time={(exec_time_ms or 0.0):.2f} ms, "
                  f"rows_returned={returned_rows or 0}, scanned={scanned_rows or 'N/A'}, "
                  f"joins_expected={joins_expected}, joins_detected={joins_detected}, "
                  f"aggs_expected={aggs_expected}, aggs_detected={aggs_detected}")
            print(f"   💡 Recommendation: {rec_text}")
            if rec_snips:
                print("   🧾 Example SQL snippets (inspect/modify before running):")
                for s in rec_snips:
                    print("   ---")
                    for line in s.splitlines():
                        print("   ", line)
            if bottleneck_op:
                print(f"   🔎 Bottleneck Operator: {bottleneck_op}")

        print("\n🎯 All queries processed. Example top slow queries:")
        rows = con.execute(
            "SELECT query_id, exec_time_ms, joins_detected, aggs_detected, recommendation FROM query_log ORDER BY exec_time_ms DESC LIMIT 10"
        ).fetchall()
        for r in rows:
            print(r)

        print("\nTo inspect logs: SELECT * FROM query_log ORDER BY logged_at DESC LIMIT 50;")

if __name__ == "__main__":
    main()
