from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import duckdb, pandas as pd, time, io, os, json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

DB_PATH = "uploaded.db"
LOG_PATH = "query_log.csv"
TRIAL_DB_PATH = "complete_tpch.db"  # Database from trial.py

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
        
        return {"queries": queries}
    except Exception as e:
        return {"error": f"Failed to get queries: {str(e)}"}

@app.post("/upload")
async def upload(db_file: UploadFile, log_file: UploadFile):
    with open(DB_PATH, "wb") as f: f.write(await db_file.read())
    with open(LOG_PATH, "wb") as f: f.write(await log_file.read())
    schema = extract_schema(DB_PATH)
    logs = pd.read_csv(LOG_PATH).to_dict(orient="records")
    return {"schema": schema, "logs": logs}

@app.post("/analyze")
async def analyze(payload: dict):
    query = payload["query"]
    con = duckdb.connect(DB_PATH)

    start = time.time()
    try:
        con.execute(query)
    except:
        pass
    exec_time = (time.time()-start)*1000

    # Append to CSV
    new_log = pd.DataFrame([{"query": query, "exec_time_ms": exec_time, "timestamp": time.time()}])
    if os.path.exists(LOG_PATH):
        new_log.to_csv(LOG_PATH, mode='a', header=False, index=False)
    else:
        new_log.to_csv(LOG_PATH, index=False)

    logs = pd.read_csv(LOG_PATH)

    # Call Groq
    try:
        client = get_groq_client()
        schema = extract_schema(DB_PATH)
        prompt = f"""
        Schema: {json.dumps(schema)}
        Past query stats: {logs.describe().to_dict()}
        New query: {query}

        Find potential performance bottlenecks and recommend fixes.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="qwen/qwen3-32b",  # Qwen model
            temperature=0.7,
            max_tokens=1000
        )
        
        result = chat_completion.choices[0].message.content
        # Remove <think></think> tags from response
        import re
        result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
    except Exception as e:
        result = f'Error: {str(e)}'

    return {
        "analysis": result,
        "updated_logs": logs.to_dict(orient="records")
    }

@app.post("/analyze_query")
async def analyze_query(payload: dict):
    """Analyze a specific query by ID from trial.py data"""
    query_id = payload.get("query_id")
    
    if not query_id:
        return {"error": "query_id is required"}
    
    try:
        # Connect to the trial database
        con = duckdb.connect(TRIAL_DB_PATH)
        
        # Get query details from query_log table
        result = con.execute("""
            SELECT query_id, query_text, exec_time_ms, scanned_rows, returned_rows,
                   joins_expected, joins_detected, aggs_expected, aggs_detected,
                   recommendation, recommendation_snippets, bottleneck_operator
            FROM query_log 
            WHERE query_id = ?
        """, [query_id]).fetchone()
        
        if not result:
            return {"error": f"Query {query_id} not found"}
        
        # Check if HTML graph exists
        html_exists = os.path.exists(f"query_html_files/query_{query_id}_profile.html")
        
        # Get schema from trial database
        schema = extract_schema(TRIAL_DB_PATH)
        
        # Prepare analysis with Groq
        client = get_groq_client()
        prompt = f"""
        Analyze this database query performance:
        
        Query ID: {result[0]}
        Query Text: {result[1]}
        Execution Time: {result[2]} ms
        Scanned Rows: {result[3]}
        Returned Rows: {result[4]}
        Joins Expected: {result[5]}, Detected: {result[6]}
        Aggregations Expected: {result[7]}, Detected: {result[8]}
        Bottleneck Operator: {result[11]}
        Current Recommendation: {result[9]}
        
        Database Schema: {json.dumps(schema)}
        
        Provide a detailed analysis of this query's performance, including:
        1. Performance assessment
        2. Bottleneck identification
        3. Specific optimization recommendations
        4. SQL snippets for improvements
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="qwen/qwen3-32b",
            temperature=0.7,
            max_tokens=1500
        )
        
        analysis = chat_completion.choices[0].message.content
        # Remove <think></think> tags from response
        import re
        analysis = re.sub(r'<think>.*?</think>', '', analysis, flags=re.DOTALL)
        
        return {
            "query_id": result[0],
            "query_text": result[1],
            "exec_time_ms": result[2],
            "scanned_rows": result[3],
            "returned_rows": result[4],
            "joins_expected": result[5],
            "joins_detected": result[6],
            "aggs_expected": result[7],
            "aggs_detected": result[8],
            "bottleneck_operator": result[11],
            "current_recommendation": result[9],
            "recommendation_snippets": result[10],
            "ai_analysis": analysis,
            "has_graph": html_exists,
            "graph_url": f"http://localhost:8000/query_graph/{query_id}" if html_exists else None
        }
        
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

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
        
        # Check if user is asking about a specific query
        import re
        query_match = re.search(r'query\s+(\d+)', user_msg, re.IGNORECASE)
        graph_match = re.search(r'(show|display|graph|chart).*query\s+(\d+)', user_msg, re.IGNORECASE)
        
        if graph_match:
            query_id = int(graph_match.group(2))
            # Check if graph exists
            html_file = f"query_html_files/query_{query_id}_profile.html"
            if os.path.exists(html_file):
                graph_url = f"http://localhost:8000/query_graph/{query_id}"
                return {
                    "reply": f"Here's the performance graph for Query {query_id}:",
                    "graph_url": graph_url,
                    "query_id": query_id,
                    "query_text": None
                }
            else:
                return {"reply": f"Sorry, no graph available for Query {query_id}."}
        
        elif query_match:
            query_id = int(query_match.group(1))
            
            # Get query analysis from trial data
            try:
                con = duckdb.connect(TRIAL_DB_PATH)
                result = con.execute("""
                    SELECT query_id, query_text, exec_time_ms, recommendation, bottleneck_operator
                    FROM query_log WHERE query_id = ?
                """, [query_id]).fetchone()
                
                if result:
                    query_text = result[1]  # Store query text
                    html_exists = os.path.exists(f"query_html_files/query_{query_id}_profile.html")
                    
                    prompt = f"""
                    The user is asking about Query {query_id}. Here are the details:
                    
                    Query Text: {result[1]}
                    Execution Time: {result[2]} ms
                    Bottleneck: {result[4]}
                    Current Recommendation: {result[3]}
                    
                    User Question: {user_msg}
                    
                    Provide a clear, easy-to-read response about this query's performance. Use simple language and format it nicely with:
                    - Brief summary of what the query does
                    - Main performance issue
                    - Simple optimization suggestions
                    - Keep it concise and user-friendly
                    """
                else:
                    prompt = f"""
                    The user is asking about Query {query_id}, but it wasn't found in our analysis data.
                    User Question: {user_msg}
                    
                    Let them know the query wasn't found and suggest they check available queries.
                    """
            except:
                prompt = f"""
                User Question: {user_msg}
                
                The user is asking about a specific query, but I couldn't access the analysis data.
                Provide a helpful response about database query analysis.
                """
        else:
            # Regular chat about database topics
            # Check if user is asking about database/analysis topics
            db_keywords = ['database', 'query', 'sql', 'performance', 'optimize', 'analyze', 'slow', 'bottleneck', 'index', 'join', 'table', 'schema']
            is_db_related = any(keyword in user_msg.lower() for keyword in db_keywords)
            
            if is_db_related:
                # Include analysis data for database-related questions
                schema = extract_schema(TRIAL_DB_PATH) if os.path.exists(TRIAL_DB_PATH) else {}
                logs = []
                if os.path.exists(TRIAL_DB_PATH):
                    try:
                        con = duckdb.connect(TRIAL_DB_PATH)
                        logs = con.execute("SELECT query_id, exec_time_ms, recommendation FROM query_log ORDER BY exec_time_ms DESC LIMIT 10").fetchall()
                    except:
                        pass
                
                prompt = f"""You are a helpful database assistant. Answer the user's question concisely and professionally.

Available Analysis Data: {len(logs)} queries analyzed
Top Slow Queries: {logs[:3] if logs else 'None'}

User question: {user_msg}

Provide a helpful response about databases, SQL, or related topics. Mention that users can ask for graphs by saying "show graph for query X"."""
            else:
                # Simple greeting or non-database question
                prompt = f"""You are a helpful AI assistant. The user said: "{user_msg}"

Respond naturally and helpfully. If they're greeting you, respond warmly. If they ask about databases, let them know you can help with database analysis and optimization."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",  # Valid Groq model
            temperature=0.7,
            max_tokens=1000
        )
        
        response = chat_completion.choices[0].message.content
        # Remove <think></think> tags from response
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Add graph info if available (but don't include graph_url automatically)
        if query_match and html_exists:
            response += f"\n\n **Performance Graph Available**: You can ask 'show graph for query {query_id}' to see the detailed visualization."
            
        return {
            "reply": response.strip(),
            "query_text": query_text,
            "graph_url": None,  # Don't show graph automatically with analysis
            "query_id": query_id
        }
    except Exception as e:
        return {"reply": f"Error: {str(e)}. Please check your Groq API key configuration."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
