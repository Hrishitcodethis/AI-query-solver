from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
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
            model="qwen/qwen3-32b",  # Fast and free model
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

@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    user_msg = body["message"]

    # optional: load schema + logs for context
    schema = extract_schema(DB_PATH) if os.path.exists(DB_PATH) else {}
    logs = pd.read_csv(LOG_PATH).to_dict(orient="records") if os.path.exists(LOG_PATH) else []

    try:
        client = get_groq_client()
        prompt = f"""You are a helpful database assistant. Answer the user's question concisely and professionally.

User question: {user_msg}

Provide a helpful response about databases, SQL, or related topics."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",  # Current available fast model
            temperature=0.7,
            max_tokens=1000
        )
        
        response = chat_completion.choices[0].message.content
        # Remove <think></think> tags from response
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        return {"reply": response.strip()}
    except Exception as e:
        return {"reply": f"Error: {str(e)}. Please check your Groq API key configuration."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
