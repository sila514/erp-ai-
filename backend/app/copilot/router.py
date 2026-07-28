import json

from fastapi import APIRouter, Depends
from google import genai
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.copilot.tools import COPILOT_TOOLS, execute_tool

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Client'ı ilk gerçek kullanımda oluşturur — GEMINI_API_KEY henüz
    ayarlanmamışsa (örn. testlerde, key eklenmeden önce) modül import'unu
    (dolayısıyla tüm uygulamayı) çökertmemek için."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


SYSTEM_PROMPT = (
    "Sen bir ERP sisteminin yönetici asistanısın. Sadece sana tanımlı fonksiyonlar "
    "üzerinden gerçek verilere erişebilirsin. Tahmin yürütme, sayı icat etme; "
    "her zaman fonksiyon çağırarak gerçek veriyi al ve onu Türkçe, kısa ve "
    "iş diliyle özetle. get_correlation_insights fonksiyonunu kullandığında: "
    "bu sonuçlar yalnızca istatistiksel ilişkidir, nedensellik değildir — asla "
    "'X, Y'ye sebep oluyor' gibi bir iddia kurma; 'X ile Y arasında ilişki "
    "gözlemleniyor' gibi ifadeler kullan."
)


class CopilotQuery(BaseModel):
    question: str


class CopilotAnswer(BaseModel):
    answer: str


def _extract_final_text(interaction) -> str:
    if getattr(interaction, "output_text", None):
        return interaction.output_text
    texts = []
    for step in interaction.steps:
        content = getattr(step, "content", None) or []
        for part in content:
            if getattr(part, "text", None):
                texts.append(part.text)
    return "".join(texts)


@router.post("/ask", response_model=CopilotAnswer)
def ask_copilot(payload: CopilotQuery, db: Session = Depends(get_db)):
    client = _get_client()
    interaction = client.interactions.create(
        model=settings.COPILOT_MODEL,
        system_instruction=SYSTEM_PROMPT,
        tools=COPILOT_TOOLS,
        input=payload.question,
    )

    # LLM bir fonksiyon çağırmak istediyse, çalıştır ve sonucu tekrar modele ver
    while True:
        function_calls = [s for s in interaction.steps if s.type == "function_call"]
        if not function_calls:
            break

        function_results = []
        for fc in function_calls:
            result = execute_tool(db, fc.name, dict(fc.arguments))
            function_results.append(
                {
                    "type": "function_result",
                    "name": fc.name,
                    "call_id": fc.id,
                    "result": [{"type": "text", "text": json.dumps(result)}],
                }
            )

        interaction = client.interactions.create(
            model=settings.COPILOT_MODEL,
            previous_interaction_id=interaction.id,
            tools=COPILOT_TOOLS,
            input=function_results,
        )

    return CopilotAnswer(answer=_extract_final_text(interaction))
