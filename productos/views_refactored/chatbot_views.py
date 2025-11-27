from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings
import google.generativeai as genai
import json


# Configurar la API Key de Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


@csrf_protect
@require_http_methods(["POST"])
def chatbot_ajax(request):
    try:
        data = json.loads(request.body)
        history = data.get("history", [])
    except Exception:
        return JsonResponse({"respuesta": "Error al procesar la conversación."})

    if not history:
        return JsonResponse({"respuesta": "Por favor, escribe una pregunta."})

    # Construir prompt con todo el historial
    prompt = (
        "Eres un asistente virtual experto de la Tienda Naturista Los Girasoles en Ibagué, Colombia. "
        "SOLO puedes responder preguntas sobre:\n"
        "- Productos naturistas (hierbas, suplementos, vitaminas)\n"
        "- Beneficios de productos naturales\n"
        "- Usos y preparación de remedios naturales\n"
        "- Alimentación saludable y vida natural\n\n"
        "Si la pregunta NO está relacionada con estos temas, responde EXACTAMENTE: "
        "'Lo siento, solo puedo ayudarte con información sobre productos naturistas y vida saludable. "
        "¿Tienes alguna pregunta sobre hierbas, suplementos o remedios naturales?'\n\n"
        "HISTORIAL DE CONVERSACIÓN:\n"
    )

    for msg in history:
        rol = "Usuario" if msg["role"] == "user" else "Bot"
        prompt += f"{rol}: {msg['content']}\n"

    prompt += "\nResponde de forma amigable, clara y en español."

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        respuesta = response.text.strip() if response.text else (
            "Lo siento, no pude procesar tu pregunta en este momento. Intenta de nuevo."
        )
    except Exception as e:
        print(f"❌ Error en Gemini API: {str(e)}")
        respuesta = (
            "Disculpa, tuve un problema técnico. Intenta de nuevo. "
            "Puedo ayudarte con preguntas sobre productos naturistas, hierbas, suplementos y vida saludable."
        )

    return JsonResponse({"respuesta": respuesta})