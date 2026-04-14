import json
import os

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from openai import OpenAI

from .forms import GameUploadForm
from .models import Game


def _ai_parse_query(query):
    #Send the search query to OpenAI and return structured filter parameters
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a game search assistant. Parse the user's natural language search query "
                    "into structured filters for an indie game database.\n\n"
                    "Return a JSON object with these fields:\n"
                    "- keywords: list of text keywords to match against title, description, and developer (can be empty)\n"
                    "- genre: a genre string to filter by (e.g. 'RPG', 'Platformer'), or null if not specified\n"
                    "- free_only: boolean, true only if the user explicitly asks for free games\n"
                    "- max_price: maximum price as a number, or null if not specified\n\n"
                    "Only set genre if the user clearly references a game genre."
                ),
            },
            {
                "role": "user",
                "content": f"Parse this game search query: {query}",
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=200,
    )
    return json.loads(response.choices[0].message.content)


# View that renders the homepage
def index(request):
    return render(request, 'index.html')


# View that handles the game upload page
def upload_game(request):

    # Redirect unauthenticated users to homepage
    if not request.user.is_authenticated:
        return redirect('index')

    # If the form was submitted
    if request.method == "POST":

        # Create form with submitted data and uploaded files
        form = GameUploadForm(request.POST, request.FILES)

        # Validate form data
        if form.is_valid():

            # Save the form but don't commit to database yet
            game = form.save(commit=False)

            # Assign the currently logged-in user as the developer
            game.developer = request.user

            # Save the game to the database
            game.save()

            # Redirect user after successful upload
            return redirect("index")

    else:
        # If this is a normal page request, display empty form
        form = GameUploadForm()

    # Render the upload page template
    return render(request, "home/upload_game.html", {"form": form})


def browse(request):
    query = request.GET.get("q", "").strip()
    games = Game.objects.all().order_by("-created_at")

    if query:
        try:
            filters = _ai_parse_query(query)

            keywords = filters.get("keywords") or []
            if keywords:
                kw_filter = Q()
                for kw in keywords:
                    kw_filter |= (
                        Q(title__icontains=kw)
                        | Q(description__icontains=kw)
                        | Q(developer__icontains=kw)
                        | Q(publisher__icontains=kw)
                    )
                games = games.filter(kw_filter)

            genre = filters.get("genre")
            if genre:
                games = games.filter(genre__icontains=genre)

            if filters.get("free_only"):
                games = games.filter(price=0)
            elif filters.get("max_price") is not None:
                games = games.filter(price__lte=filters["max_price"])

        except Exception:
            # plain text search across key fields if AI search fails
            games = games.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(developer__icontains=query)
                | Q(genre__icontains=query)
            )

    return render(request, "home/browse.html", {"games": games, "query": query})


def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)

    return render(request, "game_detail.html", {
        "title": game.title,
        "description": game.description,
        "publisher": game.publisher,
        "developer": game.developer,
        "storefront": game.storefront,
        "price": game.price,
        "game_id": game.game_id,
    })


def purchase_game(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)

    return render(request, "purchase_game.html", {
        "storefront": game.storefront,
        "price": game.price,
        "game_id": game.game_id,
    })
