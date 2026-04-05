from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
import requests
import uvicorn
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
import json
import asyncio
import time
from enum import Enum

urllib3.disable_warnings(InsecureRequestWarning)

app = FastAPI(
    title="🤖 БПК AI Agent Pro",
    description="Профессиональный AI агент для БПК с расширенными возможностями",
    version="4.0.0"
)

# Настройка CORS для React Native
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Конфигурация
GIGACHAT_TOKEN = "MDE5ZDViY2ItYTljNy03NTRlLWE5NmMtNjVkNDNjZTMwY2JlOmFhYzYzZjEyLWRjMDQtNGU4ZC04YzgwLTYyMjMyNzk5MTEwZQ"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: Role = Role.USER
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = Field("GigaChat:latest", description="Модель ГигаЧат")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(3000, ge=1, le=8000)
    stream: bool = False

class TaskRequest(BaseModel):
    task: str
    category: Optional[str] = "general"
    model: Optional[str] = "GigaChat:latest"


class AgentMemory:
    def __init__(self, max_size: int = 50):
        self.memory = []
        self.max_size = max_size
    
    def add(self, role: str, content: str):
        self.memory.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content[:1000]
        })
        if len(self.memory) > self.max_size:
            self.memory.pop(0)
    
    def get_context(self, limit: int = 10) -> List[Dict]:
        return self.memory[-limit:]
    
    def clear(self):
        self.memory = []

agent_memory = AgentMemory()

# System Prompts
BPK_PROMPTS = {
    "general": "Ты эксперт. Отвечай профессионально, структурировано, на русском.",
    "code": "Ты программист. Пиши рабочий код с комментариями, обработкой ошибок.",
    "analysis": "Ты аналитик. Делай глубокий анализ, выводы, рекомендации.",
    "creative": "Ты креативный специалист. Генерируй идеи, концепции."
}

async def gigachat_stream(messages: List[Dict], model: str, temperature: float, max_tokens: int) -> AsyncGenerator[str, None]:
    """Streaming режим"""
    headers = {
        "Authorization": f"Bearer {GIGACHAT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }
    
    response = requests.post(CHAT_URL, headers=headers, json=payload, verify=False, stream=True, timeout=120)
    
    if response.status_code != 200:
        yield f"data: {json.dumps({'error': f'HTTP {response.status_code}'})}\n\n"
        return
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                data = decoded_line[6:]
                if data.strip() == "[DONE]":
                    yield "data: [DONE]\n\n"
                    break
                yield f"{decoded_line}\n"

def gigachat_request(messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Dict:
    """Обычный запрос"""
    headers = {
        "Authorization": f"Bearer {GIGACHAT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    response = requests.post(CHAT_URL, headers=headers, json=payload, verify=False, timeout=60)
    response.raise_for_status()
    return response.json()

@app.get("/")
async def root():
    return {
        "🤖": "БПК AI Agent Pro v4.0",
        "📊": {
            "memory": len(agent_memory.memory),
            "models": ["GigaChat:latest"],
            "features": ["stream", "tasks", "memory", "analysis"]
        },
        "🔗": "/docs",
        "🧪": "/test"
    }

@app.get("/test")
async def test():
    """🧪 Системный тест"""
    try:
        messages = [{"role": "user", "content": "Тест БПК AI Agent"}]
        result = gigachat_request(messages, "GigaChat:latest", 0.7, 100)
        return {
            "status": "✅ РАБОТАЕТ!",
            "model": result["model"],
            "answer": result["choices"][0]["message"]["content"][:150]
        }
    except Exception as e:
        return {"status": "❌ Ошибка", "error": str(e)}

@app.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """💬 Универсальный чат"""
    try:
        user_msg = request.messages[-1].content
        agent_memory.add("user", user_msg)
        
        system_prompt = {"role": "system", "content": BPK_PROMPTS["general"]}
        messages = [system_prompt] + [m.dict() for m in request.messages]
        
        if request.stream:
            return StreamingResponse(
                gigachat_stream(messages, request.model, request.temperature, request.max_tokens),
                media_type="text/plain"
            )
        
        result = gigachat_request(messages, request.model, request.temperature, request.max_tokens or 3000)
        answer = result["choices"][0]["message"]["content"]
        
        agent_memory.add("assistant", answer)
        
        return {
            "success": True,
            "answer": answer,
            "model": result["model"],
            "usage": result.get("usage", {}),
            "finish_reason": result["choices"][0].get("finish_reason")
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/agent/{category}")
async def agent_task(category: str, request: TaskRequest):
    """🎯 Специализированные задачи"""
    try:
        prompt_type = category if category in BPK_PROMPTS else "general"
        system_prompt = BPK_PROMPTS[prompt_type]
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Задача БПК: {request.task}"}
        ]
        
        result = gigachat_request(messages, request.model, 0.3, 4000)
        answer = result["choices"][0]["message"]["content"]
        
        agent_memory.add("task", f"{category}: {request.task[:100]}")
        agent_memory.add("assistant", answer[:200])
        
        return {
            "success": True,
            "category": category,
            "result": answer,
            "type": prompt_type
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/memory")
async def memory(limit: int = 20):
    """🧠 Полная память"""
    return {
        "memory": agent_memory.get_context(limit),
        "total": len(agent_memory.memory),
        "summary": f"Последние {len(agent_memory.get_context(5))} сообщений"
    }

@app.delete("/memory")
async def clear_memory():
    """🗑️ Очистка памяти"""
    agent_memory.clear()
    return {"message": "✅ Память очищена"}

@app.get("/stats")
async def stats():
    """📈 Статистика"""
    return {
        "uptime": time.time(),
        "memory_size": len(agent_memory.memory),
        "requests": "N/A",
        "status": "🟢 active"
    }

@app.get("/models")
async def models():
    """📋 Модели"""
    return {
        "available": ["GigaChat:latest"],
        "recommended": "GigaChat:latest",
        "capabilities": {
            "context": "128K tokens",
            "languages": ["ru", "en"]
        }
    }

if __name__ == "__main__":
    print("🚀 БПК AI Agent Pro запущен!")
    print("📍 Сервер доступен:")
    print("   - Локально: http://localhost:8000")
    print("   - Для Android эмулятора: http://10.0.2.2:8000")
    print("   - Для физических устройств: http://[ВАШ_IP]:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",
        port=8000, 
        reload=True, 
        log_level="info"
    )