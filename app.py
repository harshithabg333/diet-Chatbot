import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq.chat_models import ChatGroq
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel

print("Working!")

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
mongo_uri = os.getenv("MONGO_URL")
print("Mongo URI:", mongo_uri)
#Set up a Mongo DB connection 
#client = mongo_client(mongo_uri)
client = MongoClient(mongo_uri)
db = client["Chat"]
collection = db["users"]
app = FastAPI()

class ChatRequest(BaseModel):
   user_id:str
   question:str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True   
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a diet specialist give me the output accoedingly"),
        ("placeholder","{history}"),
        ("user", "{question}")
      
    ]
)
   
llm = ChatGroq(api_key = groq_api_key, model = "openai/gpt-oss-20b")
chain = prompt | llm
#user_id = "user123"
user_id = str(uuid.uuid4())
print(user_id)
def get_history(user_id, limit = 6):
    chats = collection.find({"user_id":user_id}).sort("timestamp",-1).limit(limit)
    
    
   
    history = []
    #history = history[-5:]
    for chat in chats:
        #history.append((chat["role"]),chat["message"])
        # history = get_history(user_id, limit=10)
        # history = truncate_history(history, max_tokens=5000)
        history.append((chat["role"],chat["message"]))
    return history    

@app.get("/")
def home():
    return {"Welcome to diet specialist chatbot API!"}
@app.post("/chat")
def chat(request:ChatRequest):
     history = get_history(request.user_id,limit = 6) #string userid in class
     response = chain.invoke({"history":history,"question":request.question})
    #User data is stored in MongoDb 
     collection.insert_one({ 
            "user_id" : request.user_id, 
            "role":"user", 
            "message" : request.question, 
            "timestamp": datetime.now(timezone.utc) 
        }) 
        #Store the response 
     collection.insert_one({ 
            "user_id" : request.user_id, 
            "role":"assistant", 
            "message" : response.content, 
            "timestamp": datetime.now(timezone.utc)     
        }) 
     
     return {"response" : response.content}
     print(response.content) 


