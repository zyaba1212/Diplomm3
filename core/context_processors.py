from django.utils import translation

def language_processor(request):
    return {
        'current_language': translation.get_language(),
        'available_languages': ['ru', 'en'],
    }