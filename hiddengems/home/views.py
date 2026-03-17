from django.shortcuts import render, get_object_or_404
from .models import Game


def index(request):
    return render(request, 'index.html')



def purchase_game(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)

    return render(request, "purchase_game.html", {
        "storefront" : game.storefront,
        "price" : game.price,
        "game_id" : game.game_id,
    })