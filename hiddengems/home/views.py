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


def purchase_game(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)

    return render(request, "purchase_game.html", {
        "storefront" : game.storefront,
        "price" : game.price,
        "game_id" : game.game_id,
    
    })
