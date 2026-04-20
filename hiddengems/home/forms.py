from django import forms
from django.core.exceptions import ValidationError
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

    def clean_price(self):
        # Validate that price is not negative
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError("Price cannot be negative.")
        # Validate that price does not exceed allowed maximum
        if price is not None and price >= 99999999:
            raise ValidationError("Price is too large.")
        return price