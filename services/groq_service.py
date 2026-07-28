import os
import json
from groq import Groq
from services.player_service import search_players, get_player_details # دبيات أدواتك المعتادة

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 1️⃣ تعريف الأدوات (Tools Definition - OpenAI Format)
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_players",
            "description": "Search and filter players based on sport, position, min ai score, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sport": {"type": "string", "description": "Sport type (football, basketball, etc.)"},
                    "position": {"type": "string", "description": "Player position (ST, GK, CB, etc.)"},
                    "min_ai_score": {"type": "number", "description": "Minimum AI score limit"}
                },
                "required": []
            }
        }
    }
]

def run_groq_chat(messages_history):
    # استخدام موديل Llama 3.3 70B القوي في الـ Function Calling
    MODEL_NAME = "llama-3.3-70b-versatile"

    # إضافة System Prompt في البداية لو مش موجود
    system_message = {
        "role": "system",
        "content": "You are SpotMe AI scouting assistant. Help users analyze player data using the provided tools."
    }
    
    full_messages = [system_message] + messages_history

    # الاستدعاء الأول للموديل
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=full_messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.2
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 2️⃣ التحقق إذا كان الموديل قرر يستدعي Tool (Function Calling)
    if tool_calls:
        # إضافة رد الموديل اللي طلب الـ Tool للتاريخ
        full_messages.append(response_message)

        # تنفيذ الدوال المطلوبة
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # استدعاء الدالة المناسبة
            if function_name == "search_players":
                function_response = search_players(**function_args)

            # إرجاع نتيجة الدالة للموديل
            full_messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": "search_players",
                "content": json.dumps(function_response)
            })

        # الاستدعاء الثاني للموديل لتوليد الإجابة النهائية بعد الحصول على البيانات
        second_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=full_messages
        )
        return second_response.choices[0].message.content

    return response_message.content