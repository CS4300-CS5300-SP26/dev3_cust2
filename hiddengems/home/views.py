from django.shortcuts import render, redirect, get_object_or_404
from .forms import GameUploadForm
from .models import Game


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
    games = Game.objects.all().order_by('-created_at')
    return render(request, 'home/browse.html', {'games': games})


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
        "storefront": game.storefront,
        "price": game.price,
        "game_id": game.game_id,
    })