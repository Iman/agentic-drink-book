"""Allowlisted presentation languages; language selection never grants authority."""

from typing import Literal

Language = Literal["en", "fa"]

RESPONSE_LANGUAGE_RULES = {
    "en": "Respond in English, even when the question or history uses another language.",
    "fa": "Respond in Persian (Farsi), using Persian script, even when the question or history "
    "uses another language. Begin with درود. Use normal Persian spelling and word-internal "
    "half-spaces where appropriate. Preserve named cocktails: نگرونی means the Negroni cocktail, "
    "not نگرانی (worry). Include the Latin cocktail name in parentheses when helpful. "
    "Do not emit bidirectional formatting control characters.",
}

MESSAGES = {
    "en": {
        "neutral": "Hello. What would you like to know about drinks?",
        "out_of_scope": "I can help only with drinks: cocktails, ingredients, fermentation, "
        "wine, beer and spirits. Please ask a drinks-related question.",
        "unavailable": "I cannot process this request right now. Please try again later.",
        "blocked": "I couldn't safely complete that request. Please rephrase it.",
        "origin_denied": "Request origin is not allowed.",
        "invalid_language": "Choose English or Persian.",
        "session_expired": "Your session expired. Start a new conversation.",
        "verification_failed": "Request verification failed. Reconnect and try again.",
        "session_capacity": "Conversation capacity reached. Please try later.",
        "session_busy": "Wait for the current reply before resetting.",
        "json_required": "Send a JSON message.",
        "body_too_large": "Message is too large.",
        "invalid_message": "Send only a non-empty text message within the character limit.",
        "busy": "Too many requests or the service is busy. Please try again shortly.",
    },
    "fa": {
        "neutral": "درود. درباره کدام نوشیدنی می‌توانم کمکتان کنم؟",
        "out_of_scope": "درود. فقط درباره نوشیدنی‌ها، کوکتل‌ها، مواد اولیه، تخمیر، شراب، "
        "آبجو و نوشیدنی‌های تقطیری پاسخ می‌دهم. لطفاً پرسشی در همین زمینه بپرسید.",
        "unavailable": "درود. اکنون امکان پاسخ‌گویی ندارم. لطفاً کمی بعد دوباره تلاش کنید.",
        "blocked": "درود. نمی‌توانم به این درخواست پاسخ ایمن بدهم. لطفاً پرسش خود را بازنویسی کنید.",
        "origin_denied": "مبدأ درخواست مجاز نیست.",
        "invalid_language": "زبان انگلیسی یا فارسی را انتخاب کنید.",
        "session_expired": "نشست شما منقضی شده است. گفت‌وگوی تازه‌ای آغاز کنید.",
        "verification_failed": "درخواست تأیید نشد. دوباره متصل شوید و تلاش کنید.",
        "session_capacity": "ظرفیت گفت‌وگوها تکمیل شده است. لطفاً کمی بعد تلاش کنید.",
        "session_busy": "پیش از شروع گفت‌وگوی تازه، منتظر پایان پاسخ بمانید.",
        "json_required": "پیام را در قالب JSON ارسال کنید.",
        "body_too_large": "حجم پیام بیش از حد مجاز است.",
        "invalid_message": "فقط یک پیام متنی غیرخالی و در محدوده تعداد نویسه‌های مجاز ارسال کنید.",
        "busy": "تعداد درخواست‌ها زیاد است یا سرویس مشغول است. لطفاً کمی بعد تلاش کنید.",
    },
}


def translate(key: str, language: Language = "en") -> str:
    return MESSAGES[language][key]
