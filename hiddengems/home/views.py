from django.shortcuts import render, get_object_or_404
from .models import Game


def index(request):
    return render(request, 'index.html')



def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)

    return render(request, "game_detail.html", {
        "title": game.title,
        "description": game.description,
        "publisher": game.publisher,
        "developer": game.developer,
    })