import json
import os

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET
from openai import OpenAI

from .forms import GameUploadForm
from .models import Game
from .utils import get_similar_games


def _ai_parse_query(query):
    # Send the search query to OpenAI and return structured filter parameters
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.responses.create(
        model="gpt-5.1-codex-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a game search assistant. Parse the user's natural language search query "
                    "into structured filters for an indie game database.\n\n"
                    "Respond with ONLY a raw JSON object — no markdown, no code fences, no explanation.\n\n"
                    "JSON fields:\n"
                    "- keywords: list of descriptive words to match against game titles and descriptions. "
                    "Include synonyms and related terms (e.g. 'scary' → ['horror', 'scary', 'spooky', 'terror']). "
                    "Do NOT include the word 'free' or price-related words here — use free_only instead. "
                    "Do NOT include genre words here if you already set the genre field.\n"
                    "- vibe_keywords: list of mood, atmosphere, or style words extracted from the query "
                    "(e.g. 'relaxing', 'cozy', 'fast-paced', 'dark', 'cute', 'challenging', 'peaceful'). "
                    "Use this for any descriptive vibe the user is looking for. Can overlap with keywords.\n"
                    "- genre: a single genre string (e.g. 'RPG', 'Platformer', 'Puzzle', 'Horror', 'Strategy'), "
                    "or null if not specified. Only set this if the user clearly references a game genre.\n"
                    "- free_only: boolean, true if the user asks for free games, games that cost nothing, or $0 games\n"
                    "- max_price: maximum price as a number, or null if not specified\n\n"
                    "Be generous with keywords and vibe_keywords — err on the side of more terms to avoid empty results. "
                    "For purely vibe-based queries (e.g. 'something relaxing'), populate vibe_keywords even if keywords is empty."
                ),
            },
            {
                "role": "user",
                "content": f"Parse this game search query: {query}",
            },
        ],
    )
    raw = response.output_text
    print(raw)
    # Strip markdown code fences if the model wraps output in them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


# View that renders the homepage
def index(request):
    return render(request, 'index.html')


# View that handles the game upload page
def upload_game(request):

    # Redirect unauthenticated users to login page, then back to upload after login
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/upload/")

    # If the form was submitted
    if request.method == "POST":

        # Create form with submitted data and uploaded files
        form = GameUploadForm(request.POST, request.FILES)

        # Validate form data
        if form.is_valid():

            # Save the form but don't commit to database yet
            game = form.save(commit=False)

            # Assign the currently logged-in user as the uploader
            game.uploaded_by = request.user

            # Use username as developer name if not set
            if not game.developer:
                game.developer = request.user.username

            # Save the game to the database
            game.save()

            # Redirect user after successful upload
            return redirect("index")

    else:
        # If this is a normal page request, display empty form
        form = GameUploadForm()

    # Render the upload page template
    return render(request, "home/upload_game.html", {"form": form})


@require_GET
def browse(request):
    query = request.GET.get("q", "").strip()
    games = Game.objects.all().order_by("-created_at")

    if query:
        try:
            filters = _ai_parse_query(query)

            # Build a combined text filter from keywords + vibe_keywords
            keywords = filters.get("keywords") or []
            vibe_keywords = filters.get("vibe_keywords") or []
            all_terms = list({kw.lower() for kw in keywords + vibe_keywords})

            text_filter = Q()
            for term in all_terms:
                text_filter |= (
                    Q(title__icontains=term)
                    | Q(description__icontains=term)
                    | Q(developer__icontains=term)
                    | Q(publisher__icontains=term)
                )

            genre = filters.get("genre")

            # Apply price filter
            if filters.get("free_only"):
                games = games.filter(price__lte=0)
            elif filters.get("max_price") is not None:
                games = games.filter(price__lte=filters["max_price"])

            # Apply text + genre filters. Combine them with OR so that a game
            # matching the vibe OR the genre qualifies — this avoids zero results
            # when genre tags in the DB don't perfectly match the AI's genre label.
            if all_terms and genre:
                games = games.filter(text_filter | Q(genre__icontains=genre))
            elif all_terms:
                games = games.filter(text_filter)
            elif genre:
                games = games.filter(genre__icontains=genre)
            # If neither terms nor genre were extracted, return all games
            # (price filter already narrowed the set above)

        except Exception as e:
            # plain text search across key fields if AI search fails
            print(e)
            games = games.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(developer__icontains=query)
                | Q(genre__icontains=query)
            )

    return render(request, "home/browse.html", {"games": games, "query": query})


@xframe_options_sameorigin
def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)
    similar_games = get_similar_games(game)

    return render(request, "game_detail.html", {
        "game": game,  # Pass full game object — template accesses all fields via game.field
        "similar_games": similar_games,
    })


def purchase_game(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)

    return render(request, "purchase_game.html", {
        "storefront": game.storefront,
        "price": game.price,
        "game_id": game.game_id,
    })