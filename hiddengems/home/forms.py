from django import forms
from .models import Game

# Form used by developers to upload a new game
# ModelForm automatically creates fields based on the Game model
class GameUploadForm(forms.ModelForm):

    class Meta:
        model = Game

        # Fields that will appear in the upload form
        fields = [
            "title",
            "description",
            "price",
            "genre",
            "playable_in_browser",
            "other_platforms",
            "thumbnail",
            "build_file",
        ]