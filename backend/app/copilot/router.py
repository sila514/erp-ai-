from anthropic import Anthropic
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.copilot.tools import COPILOT_TOOLS, execute_tool

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = (
    "Sen bir ERP sisteminin yönetici asistanısın. Sadece sana tanımlı fonksiyonlar "
    "üzerinden gerçek verilere erişebilirsin. Tahmin yürütme, sayı icat etme; "
    "her zaman fonksiyon çağırarak gerçek veriyi al ve onu Türkçe, kısa ve "
    "iş diliyle özetle."
)


class CopilotQuery(BaseModel):
    question: str


class CopilotAnswer(BaseModel):
    answer: str


@router.post("/ask", response_model=CopilotAnswer)
def ask_copilot(payload: CopilotQuery, db: Session = Depends(get_db)):
    messages = [{"role": "user", "content": payload.question}]

    response = client.messages.create(
        model=settings.COPILOT_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=COPILOT_TOOLS,
        messages=messages,
    )

    # LLM bir tool çağırmak istediyse, çalıştır ve sonucu tekrar modele ver
    while response.stop_reason == "tool_use":
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in tool_use_blocks:
            result = execute_tool(db, block.name, block.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": str(result)}
            )

        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=settings.COPILOT_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=COPILOT_TOOLS,
            messages=messages,
        )

    final_text = "".join(b.text for b in response.content if b.type == "text")
    return CopilotAnswer(answer=final_text)
