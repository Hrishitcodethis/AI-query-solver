from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import duckdb, pandas as pd, time, io, os, json, subprocess, re
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, UTC
import plotly.express as px

# Load environment variables
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

DB_PATH = "uploaded.db"
TRIAL_DB_PATH = "complete_tpch.db"  # Main analysis database using trial.py format

# Initialize Groq AI
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("Please set your GROQ_API_KEY in the .env file")
    return Groq(api_key=api_key)

def extract_schema(path):
    con = duckdb.connect(path)
    tables = con.sql("SHOW TABLES").fetchall()
    schema = {}
    for (t,) in tables:
        cols = con.sql(f"DESCRIBE {t}").df()
        samples = con.sql(f"SELECT * FROM {t} LIMIT 5").df()
        schema[t] = {
            "columns": cols.to_dict(orient="records"),
            "sample_values": {col: samples[col].dropna().astype(str).head(5).tolist() for col in samples.columns}
        }
    return schema

def generate_query_graph(query_id, query_text, exec_time_ms, bottleneck_operator):
    """Generate HTML graph for a query using plotly"""
    try:
        # Create a simple performance graph
        # For now, we'll create a basic bar chart showing execution time
        # In a real implementation, you'd parse EXPLAIN ANALYZE output
        
        # Create mock operator data based on query analysis
        operators = []
        times = []
        
        # Basic operators that most queries have
        operators.append("TABLE_SCAN")
        times.append(exec_time_ms * 0.3)  # 30% of time
        
        if "JOIN" in query_text.upper():
            operators.append("HASH_JOIN")
            times.append(exec_time_ms * 0.4)  # 40% of time
            
        if "GROUP BY" in query_text.upper():
            operators.append("HASH_GROUP_BY")
            times.append(exec_time_ms * 0.2)  # 20% of time
            
        if "ORDER BY" in query_text.upper():
            operators.append("SORT")
            times.append(exec_time_ms * 0.1)  # 10% of time
        
        # Ensure we have at least one operator
        if not operators:
            operators = ["EXECUTION"]
            times = [exec_time_ms]
        
        # Create DataFrame
        df = pd.DataFrame({
            'operator_type': operators,
            'time_s': [t/1000 for t in times]  # Convert to seconds
        })
        
        # Create plotly bar chart
        fig = px.bar(
            df.sort_values("time_s", ascending=True),
            x="time_s", 
            y="operator_type", 
            orientation="h",
            title=f"Query {query_id} Profile (Execution Time per Operator)",
            labels={"time_s": "Execution Time (s)", "operator_type": "Operator"},
            color="time_s",
            color_continuous_scale="Blues"
        )
        
        # Update layout
        fig.update_layout(
            height=400,
            showlegend=False,
            font=dict(size=12)
        )
        
        # Ensure directory exists
        os.makedirs("query_html_files", exist_ok=True)
        
        # Save HTML file
        plot_filename = f"query_html_files/query_{query_id}_profile.html"
        fig.write_html(plot_filename)
        
        print(f"📊 Graph saved to {plot_filename}")
        return True
        
    except Exception as e:
        print(f"⚠️ Graph generation failed for query {query_id}: {e}")
        return False

def run_trial_analysis_on_uploaded_db():
    """Run trial.py analysis on the uploaded database"""
    try:
        # Create a modified trial.py script for the uploaded database
        analysis_script = f"""
import duckdb
import time
import re
import json
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, UTC

DB_PATH = "{DB_PATH}"
TRIAL_DB_PATH = "{TRIAL_DB_PATH}"

# Connect to main analysis database
con = duckdb.connect(TRIAL_DB_PATH)

# Create query_log table if it doesn't exist (trial.py format)
con.execute('''
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
    )
''')

# Get all tables from uploaded database
upload_con = duckdb.connect(DB_PATH)
tables = upload_con.execute("SHOW TABLES").fetchall()

# Get next available query_id
max_id_result = con.execute("SELECT COALESCE(MAX(query_id), 0) FROM query_log").fetchone()
next_query_id = max_id_result[0] + 1 if max_id_result else 1

print(f"Starting analysis with query_id: {{next_query_id}}")

# Analyze each table with comprehensive queries
for (table_name,) in tables:
    try:
        print(f"Analyzing table: {{table_name}}")
        
        # Get table info
        table_info = upload_con.execute(f"DESCRIBE {{table_name}}").fetchall()
        sample_data = upload_con.execute(f"SELECT * FROM {{table_name}} LIMIT 10").fetchall()
        
        # Create comprehensive analysis queries
        queries = [
            f"SELECT COUNT(*) FROM {{table_name}}",
            f"SELECT * FROM {{table_name}} LIMIT 100",
            f"SELECT * FROM {{table_name}} ORDER BY 1 LIMIT 50",
            f"SELECT * FROM {{table_name}} WHERE 1=1 LIMIT 20"
        ]
        
        for query in queries:
            try:
                print(f"  Running query: {{query[:50]}}...")
                
                # Run query with timing
                start_time = time.time()
                result = upload_con.execute(query).fetchall()
                exec_time = (time.time() - start_time) * 1000
                
                # Analyze query performance
                scanned_rows = len(sample_data) * 10  # Estimate
                returned_rows = len(result)
                
                # Detect joins and aggregations
                joins_detected = len(re.findall(r'\\bJOIN\\b', query, re.IGNORECASE))
                aggs_detected = len(re.findall(r'\\b(COUNT|SUM|AVG|MIN|MAX)\\b', query, re.IGNORECASE))
                
                # Generate recommendation based on performance
                if exec_time < 100:
                    recommendation = "Query executed efficiently. Performance is good."
                    bottleneck = "NONE"
                elif exec_time < 1000:
                    recommendation = "Query performance is acceptable. Consider adding indexes for better performance."
                    bottleneck = "TABLE_SCAN"
                else:
                    recommendation = "Query is slow. Consider optimizing with indexes, query restructuring, or adding WHERE clauses."
                    bottleneck = "SLOW_QUERY"
                
                # Add specific recommendations based on query type
                if "COUNT(*)" in query:
                    recommendation += " For COUNT queries, consider using approximate counts or indexed columns."
                elif "ORDER BY" in query:
                    recommendation += " For ORDER BY queries, ensure the ordered column is indexed."
                elif "WHERE" in query:
                    recommendation += " For WHERE clauses, ensure the filtered columns are indexed."
                
                # Insert analysis result using trial.py format
                con.execute('''
                    INSERT INTO query_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [
                    next_query_id, query, "", exec_time, scanned_rows, returned_rows,
                    0, joins_detected, 0, aggs_detected, recommendation,
                    "", bottleneck, datetime.now(UTC)
                ])
                
                # Generate HTML graph
                try:
                    # Create mock operator data for graph
                    operators = []
                    times = []
                    
                    operators.append("TABLE_SCAN")
                    times.append(exec_time * 0.3)
                    
                    if "JOIN" in query.upper():
                        operators.append("HASH_JOIN")
                        times.append(exec_time * 0.4)
                        
                    if "GROUP BY" in query.upper():
                        operators.append("HASH_GROUP_BY")
                        times.append(exec_time * 0.2)
                        
                    if "ORDER BY" in query.upper():
                        operators.append("SORT")
                        times.append(exec_time * 0.1)
                    
                    if not operators:
                        operators = ["EXECUTION"]
                        times = [exec_time]
                    
                    # Create DataFrame
                    df = pd.DataFrame({{
                        'operator_type': operators,
                        'time_s': [t/1000 for t in times]
                    }})
                    
                    # Create plotly bar chart
                    fig = px.bar(
                        df.sort_values("time_s", ascending=True),
                        x="time_s", 
                        y="operator_type", 
                        orientation="h",
                        title=f"Query {{next_query_id}} Profile (Execution Time per Operator)",
                        labels={{"time_s": "Execution Time (s)", "operator_type": "Operator"}},
                        color="time_s",
                        color_continuous_scale="Blues"
                    )
                    
                    fig.update_layout(
                        height=400,
                        showlegend=False,
                        font=dict(size=12)
                    )
                    
                    # Ensure directory exists
                    os.makedirs("query_html_files", exist_ok=True)
                    
                    # Save HTML file
                    plot_filename = f"query_html_files/query_{{next_query_id}}_profile.html"
                    fig.write_html(plot_filename)
                    print(f"    📊 Graph saved to {{plot_filename}}")
                    
                except Exception as e:
                    print(f"    ⚠️ Graph generation failed: {{e}}")
                
                print(f"    Query {{next_query_id}} analyzed: {{exec_time:.2f}}ms")
                next_query_id += 1
                
            except Exception as e:
                print(f"    Error analyzing query: {{e}}")
                continue
                
    except Exception as e:
        print(f"Error analyzing table {{table_name}}: {{e}}")
        continue

con.close()
upload_con.close()
print("Analysis completed successfully!")
print(f"Total queries analyzed: {{next_query_id - 1}}")
"""
        
        # Write and execute analysis script
        with open("temp_upload_analysis.py", "w") as f:
            f.write(analysis_script)
        
        result = subprocess.run(["python3", "temp_upload_analysis.py"], 
                              capture_output=True, text=True, cwd=".")
        
        # Clean up
        if os.path.exists("temp_upload_analysis.py"):
            os.remove("temp_upload_analysis.py")
            
        return result.returncode == 0, result.stdout, result.stderr
        
    except Exception as e:
        return False, "", str(e)

def run_trial_analysis_on_user_query(query_text):
    """Run trial.py analysis on a user-executed query"""
    try:
        # Connect to main analysis database
        con = duckdb.connect(TRIAL_DB_PATH)
        
        # Get next available query_id
        max_id_result = con.execute("SELECT COALESCE(MAX(query_id), 0) FROM query_log").fetchone()
        next_query_id = max_id_result[0] + 1 if max_id_result else 1
        
        # Connect to uploaded database
        upload_con = duckdb.connect(DB_PATH)
        
        # Run query with timing
        start_time = time.time()
        try:
            result = upload_con.execute(query_text).fetchall()
            exec_time = (time.time() - start_time) * 1000
            success = True
            error_msg = None
        except Exception as e:
            exec_time = (time.time() - start_time) * 1000
            result = []
            success = False
            error_msg = str(e)
        
        if success:
            # Analyze query performance
            scanned_rows = len(result) * 2  # Estimate
            returned_rows = len(result)
            
            # Detect joins and aggregations
            joins_detected = len(re.findall(r'\bJOIN\b', query_text, re.IGNORECASE))
            aggs_detected = len(re.findall(r'\b(COUNT|SUM|AVG|MIN|MAX)\b', query_text, re.IGNORECASE))
            
            # Generate recommendation based on performance
            if exec_time < 100:
                recommendation = "Query executed efficiently. Performance is good."
                bottleneck = "NONE"
            elif exec_time < 1000:
                recommendation = "Query performance is acceptable. Consider adding indexes for better performance."
                bottleneck = "TABLE_SCAN"
            else:
                recommendation = "Query is slow. Consider optimizing with indexes, query restructuring, or adding WHERE clauses."
                bottleneck = "SLOW_QUERY"
            
            # Add specific recommendations based on query type
            if "COUNT(*)" in query_text:
                recommendation += " For COUNT queries, consider using approximate counts or indexed columns."
            elif "ORDER BY" in query_text:
                recommendation += " For ORDER BY queries, ensure the ordered column is indexed."
            elif "WHERE" in query_text:
                recommendation += " For WHERE clauses, ensure the filtered columns are indexed."
            elif "JOIN" in query_text:
                recommendation += " For JOIN queries, ensure join columns are indexed and consider query order."
            
            # Insert analysis result using trial.py format
            con.execute('''
                INSERT INTO query_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                next_query_id, query_text, "", exec_time, scanned_rows, returned_rows,
                0, joins_detected, 0, aggs_detected, recommendation,
                "", bottleneck, datetime.now(UTC)
            ])
            
            # Generate HTML graph
            generate_query_graph(next_query_id, query_text, exec_time, bottleneck)
            
            con.close()
            upload_con.close()
            
            return next_query_id, exec_time, len(result), True, None
        else:
            con.close()
            upload_con.close()
            return next_query_id, exec_time, 0, False, error_msg
            
    except Exception as e:
        return None, 0, 0, False, str(e)

@app.get("/query_graph/{query_id}")
async def get_query_graph(query_id: int):
    """Serve HTML visualization file for a specific query"""
    html_file = f"query_html_files/query_{query_id}_profile.html"
    if os.path.exists(html_file):
        return FileResponse(html_file, media_type="text/html")
    else:
        return {"error": f"Graph for query {query_id} not found"}

@app.get("/available_queries")
async def get_available_queries():
    """Get list of available queries with their analysis data"""
    try:
        if os.path.exists(TRIAL_DB_PATH):
            con = duckdb.connect(TRIAL_DB_PATH)
            results = con.execute("""
                SELECT query_id, exec_time_ms, bottleneck_operator, recommendation
                FROM query_log 
                ORDER BY exec_time_ms DESC
            """).fetchall()
            
            queries = []
            for row in results:
                html_exists = os.path.exists(f"query_html_files/query_{row[0]}_profile.html")
                queries.append({
                    "query_id": row[0],
                    "exec_time_ms": row[1],
                    "bottleneck_operator": row[2],
                    "recommendation": row[3][:100] + "..." if len(row[3]) > 100 else row[3],
                    "has_graph": html_exists
                })
            
            con.close()
            return {"queries": queries}
        else:
            return {"queries": [], "message": "No analysis data available. Upload a database to get started."}
    except Exception as e:
        return {"error": f"Failed to get queries: {str(e)}"}

@app.post("/upload")
async def upload(db_file: UploadFile, log_file: UploadFile = None):
    """Upload database file and run trial.py analysis"""
    try:
        # Save uploaded database
        with open(DB_PATH, "wb") as f:
            f.write(await db_file.read())
        
        # Extract schema
        schema = extract_schema(DB_PATH)
        
        # Run trial.py analysis on uploaded database
        success, stdout, stderr = run_trial_analysis_on_uploaded_db()
        
        return {
            "schema": schema, 
            "analysis_completed": success,
            "analysis_message": stdout if success else stderr,
            "message": "Database uploaded and analyzed with trial.py. Query IDs are now available for analysis."
        }
        
    except Exception as e:
        return {"error": f"Upload failed: {str(e)}"}

@app.post("/analyze")
async def analyze(payload: dict):
    """Execute a query and run trial.py analysis on it"""
    query = payload["query"]
    
    # Run trial.py analysis on the user query
    query_id, exec_time, rows_returned, success, error_msg = run_trial_analysis_on_user_query(query)
    
    if query_id is None:
        return {
            "error": "Failed to analyze query",
            "message": "Analysis failed. Please try again."
        }
    
    return {
        "query_id": query_id,
        "execution_time": exec_time,
        "rows_returned": rows_returned,
        "success": success,
        "error": error_msg if not success else None,
        "message": f"Query analyzed with trial.py! Query ID: {query_id}. Ask the AI assistant for detailed analysis."
    }

@app.get("/query/{query_id}")
async def get_query_by_id(query_id: int):
    """Get query details by ID from trial.py analysis database"""
    try:
        if not os.path.exists(TRIAL_DB_PATH):
            return {"error": "No analysis data available"}
        
        con = duckdb.connect(TRIAL_DB_PATH)
        result = con.execute("""
            SELECT query_id, query_text, exec_time_ms, scanned_rows, returned_rows, 
                   joins_detected, aggs_detected, recommendation, bottleneck_operator
            FROM query_log WHERE query_id = ?
        """, [query_id]).fetchone()
        
        if not result:
            con.close()
            return {"error": f"Query {query_id} not found"}
        
        query_id, query_text, exec_time, scanned_rows, returned_rows, joins_detected, aggs_detected, recommendation, bottleneck = result
        con.close()
        
        return {
            "query_id": query_id,
            "query": query_text,
            "execution_time": exec_time,
            "scanned_rows": scanned_rows,
            "returned_rows": returned_rows,
            "joins_detected": joins_detected,
            "aggs_detected": aggs_detected,
            "recommendation": recommendation,
            "bottleneck_operator": bottleneck
        }
        
    except Exception as e:
        return {"error": f"Failed to get query: {str(e)}"}

@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    user_msg = body["message"]

    try:
        client = get_groq_client()
        
        # Initialize variables
        query_text = None
        html_exists = False
        query_id = None
        
        # Check if user is asking about a specific query by ID (integer format)
        import re
        query_id_match = re.search(r'query\s+(\d+)', user_msg, re.IGNORECASE)
        graph_match = re.search(r'(show|display).*graph.*query\s+(\d+)', user_msg, re.IGNORECASE)
        
        if graph_match:
            query_id = int(graph_match.group(2))
            html_file = f"query_html_files/query_{query_id}_profile.html"
            html_exists = os.path.exists(html_file)
            
            if html_exists:
                response = f"Here's the performance graph for Query {query_id}:"
                return {
                    "reply": response,
                    "query_text": None,
                    "graph_url": f"http://localhost:8000/query_graph/{query_id}",
                    "query_id": query_id
                }
            else:
                response = f"Graph for Query {query_id} is not available. You can ask for performance analysis instead."
                return {
                    "reply": response,
                    "query_text": None,
                    "graph_url": None,
                    "query_id": query_id
                }
        
        elif query_id_match:
            query_id = int(query_id_match.group(1))
            
            # Get query analysis from trial.py database
            try:
                query_response = await get_query_by_id(query_id)
                if "error" in query_response:
                    response = f"Query {query_id} not found. Please check the query ID."
                else:
                    query_text = query_response["query"]
                    exec_time = query_response["execution_time"]
                    scanned_rows = query_response["scanned_rows"]
                    returned_rows = query_response["returned_rows"]
                    joins_detected = query_response["joins_detected"]
                    aggs_detected = query_response["aggs_detected"]
                    recommendation = query_response["recommendation"]
                    bottleneck = query_response["bottleneck_operator"]
                    
                    # Create analysis prompt based on what user is asking
                    analysis_type = "general"
                    if "optimize" in user_msg.lower() or "optimization" in user_msg.lower():
                        analysis_type = "optimization"
                    elif "performance" in user_msg.lower() or "slow" in user_msg.lower():
                        analysis_type = "performance"
                    elif "explain" in user_msg.lower() or "how" in user_msg.lower():
                        analysis_type = "explanation"
                    
                    if analysis_type == "optimization":
                        prompt = f"""Analyze this SQL query for optimization opportunities:

Query: {query_text}
Execution Time: {exec_time:.2f}ms
Scanned Rows: {scanned_rows}
Returned Rows: {returned_rows}
Joins Detected: {joins_detected}
Aggregations Detected: {aggs_detected}
Bottleneck: {bottleneck}

Current Recommendation: {recommendation}

Provide specific optimization recommendations and suggest improved SQL if possible."""
                    elif analysis_type == "performance":
                        prompt = f"""Analyze the performance of this SQL query:

Query: {query_text}
Execution Time: {exec_time:.2f}ms
Scanned Rows: {scanned_rows}
Returned Rows: {returned_rows}
Joins Detected: {joins_detected}
Aggregations Detected: {aggs_detected}
Bottleneck: {bottleneck}

Current Recommendation: {recommendation}

Identify performance bottlenecks and suggest improvements."""
                    elif analysis_type == "explanation":
                        prompt = f"""Explain what this SQL query does and how it works:

Query: {query_text}
Execution Time: {exec_time:.2f}ms
Scanned Rows: {scanned_rows}
Returned Rows: {returned_rows}
Joins Detected: {joins_detected}
Aggregations Detected: {aggs_detected}
Bottleneck: {bottleneck}

Provide a clear explanation of the query logic and purpose."""
                    else:
                        prompt = f"""Provide a comprehensive analysis of this SQL query:

Query: {query_text}
Execution Time: {exec_time:.2f}ms
Scanned Rows: {scanned_rows}
Returned Rows: {returned_rows}
Joins Detected: {joins_detected}
Aggregations Detected: {aggs_detected}
Bottleneck: {bottleneck}

Current Recommendation: {recommendation}

Analyze the query and provide insights."""
                    
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.1-8b-instant",
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    analysis = chat_completion.choices[0].message.content
                    analysis = re.sub(r'<think>.*?</think>', '', analysis, flags=re.DOTALL)
                    
                    response = f"**Query {query_id} Analysis**\n\n**Query:**\n```sql\n{query_text}\n```\n\n**Performance Metrics:**\n- Execution Time: {exec_time:.2f}ms\n- Scanned Rows: {scanned_rows}\n- Returned Rows: {returned_rows}\n- Joins: {joins_detected}\n- Aggregations: {aggs_detected}\n- Bottleneck: {bottleneck}\n\n**Analysis:**\n{analysis}"
                
                return {
                    "reply": response,
                    "query_text": query_text,
                    "graph_url": None,
                    "query_id": query_id
                }
            except Exception as e:
                response = f"Error analyzing query {query_id}: {str(e)}"
                return {
                    "reply": response,
                    "query_text": None,
                    "graph_url": None,
                    "query_id": query_id
                }
        
        # Check if user wants to list recent queries
        list_match = re.search(r'(list|show).*(?:queries|recent)', user_msg, re.IGNORECASE)
        if list_match:
            if os.path.exists(TRIAL_DB_PATH):
                try:
                    con = duckdb.connect(TRIAL_DB_PATH)
                    recent_queries = con.execute("""
                        SELECT query_id, LEFT(query_text, 50) as query_preview, exec_time_ms
                        FROM query_log 
                        ORDER BY logged_at DESC 
                        LIMIT 10
                    """).fetchall()
                    con.close()
                    
                    if recent_queries:
                        query_list = []
                        for row in recent_queries:
                            query_list.append(f"**Query {row[0]}**: {row[1]}{'...' if len(row[1]) == 50 else ''} ({row[2]:.2f}ms)")
                        
                        response = f"**Recent Queries:**\n\n" + "\n".join(query_list) + f"\n\nAsk 'analyze query [ID]' for detailed analysis of any query."
                        
                        return {
                            "reply": response,
                            "query_text": None,
                            "graph_url": None,
                            "query_id": None
                        }
                except Exception as e:
                    pass
        
        # Regular chat about database topics
        db_keywords = ['database', 'query', 'sql', 'performance', 'optimize', 'analyze', 'slow', 'bottleneck', 'index', 'join', 'table', 'schema']
        is_db_related = any(keyword in user_msg.lower() for keyword in db_keywords)
        
        if is_db_related:
            prompt = f"""You are a helpful database assistant. Answer the user's question about database topics concisely.

User question: {user_msg}

Provide helpful database advice and optimization tips. Keep response under 200 words."""
        else:
            prompt = f"""You are a helpful database assistant. The user said: "{user_msg}"

Respond naturally and ask how you can help with database-related questions."""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=300
        )
        
        response = chat_completion.choices[0].message.content
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        return {
            "reply": response.strip(),
            "query_text": query_text,
            "graph_url": None,
            "query_id": query_id
        }
        
    except Exception as e:
        return {
            "reply": f"Error: {str(e)}. Please check your Groq API key configuration.",
            "query_text": None,
            "graph_url": None,
            "query_id": None
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
