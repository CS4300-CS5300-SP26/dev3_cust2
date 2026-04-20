from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
import decimal
from .models import Game

# Form used by developers to upload a new game
# ModelForm automatically creates fields based on the Game model
class GameUploadForm(forms.ModelForm):

    genre = forms.CharField(max_length=100, required=True)
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(decimal.Decimal('0.00')),
            MaxValueValidator(decimal.Decimal('9999.99')),
        ]
    )

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