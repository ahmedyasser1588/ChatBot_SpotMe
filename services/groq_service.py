import os
import json
from groq import Groq
from services.player_service import PlayerService

# إنشاء Instance من الكلاس الخاص بك
player_service = PlayerService()

# 1️⃣ تعريف الأدوات (Tools) متوافقة مع البرامترات المكتوبة في كودك
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_players",
            "description": "البحث والفلترة والترتيب في قائمة لاعبي SpotMe حسب الرياضة والنادي والعمر والتقييم.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sport": {"type": "string", "description": "نوع الرياضة: football, basketball, handball, volleyball"},
                    "name_contains": {"type": "string", "description": "جزء من اسم اللاعب"},
                    "club_contains": {"type": "string", "description": "اسم النادي"},
                    "position": {"type": "string", "description": "المركز مثل ST, GK, CB"},
                    "min_age": {"type": "integer"},
                    "max_age": {"type": "integer"},
                    "min_ai_score": {"type": "number"},
                    "max_ai_score": {"type": "number"},
                    "min_height_cm": {"type": "number"},
                    "max_height_cm": {"type": "number"},
                    "max_injuries": {"type": "integer"},
                    "min_recovery": {"type": "number"},
                    "sort_by": {"type": "string", "description": "حقل الترتيب مثل ai_score أو age"},
                    "order": {"type": "string", "description": "asc أو desc"},
                    "limit": {"type": "integer", "description": "عدد النتائج المطلوبة"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_player",
            "description": "البحث عن لاعب واحد محدد بالاسم أو الرقم التعريف (ID)",
            "parameters": {
                "type": "object",
                "properties": {
                    "id_or_name": {"type": "string", "description": "اسم اللاعب أو الـ player_id"}
                },
                "required": ["id_or_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "database_overview",
            "description": "عرض نظرة عامة شاملة على قاعدة بيانات SpotMe والألعاب والأندية المتاحة",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

def run_groq_chat(messages_history):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY is missing from environment variables."

    client = Groq(api_key=api_key)
    model_name = "llama-3.3-70b-versatile"

    system_message = {
        "role": "system",
        "content": "You are SpotMe AI scouting assistant. Use the provided tools to search player database, view stats, and answer user queries accurately in Arabic or English based on user query."
    }

    full_messages = [system_message]
    for msg in messages_history:
        if isinstance(msg, dict):
            full_messages.append(msg)
        else:
            full_messages.append({"role": msg.role, "content": msg.content})

    # الاستدعاء الأول
    response = client.chat.completions.create(
        model=model_name,
        messages=full_messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.2
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # تنفيذ الـ Tool Calls
    if tool_calls:
        full_messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            function_response = None
            if function_name == "query_players":
                function_response = player_service.query_players(**function_args)
            elif function_name == "get_player":
                function_response = player_service.get_player(**function_args)
            elif function_name == "database_overview":
                function_response = player_service.database_overview()

            full_messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(function_response, ensure_ascii=False)
            })

        # الاستدعاء الثاني لإعطاء الإجابة النهائية
        second_response = client.chat.completions.create(
            model=model_name,
            messages=full_messages
        )
        return second_response.choices[0].message.content

    return response_message.content