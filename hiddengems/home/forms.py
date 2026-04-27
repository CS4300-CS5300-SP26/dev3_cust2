from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
import decimal
from .models import Game
from django.core.validators import FileExtensionValidator  # add to imports

# Form used by developers to upload a new game
# ModelForm automatically creates fields based on the Game model
class GameUploadForm(forms.ModelForm):

    genre = forms.CharField(max_length=100, required=False)
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
    from django.core.validators import FileExtensionValidator  # add to imports

    # Inside class Meta, update the model fields in models.py instead,
    # but you can also add clean methods here in forms.py:

    def clean_build_file(self):
        f = self.cleaned_data.get('build_file')
        if f:
            allowed = ['zip', 'wasm']
            ext = f.name.rsplit('.', 1)[-1].lower()
            if ext not in allowed:
                raise ValidationError("Build file must be a .zip or .wasm file.")
        return f

    def clean_thumbnail(self):
        f = self.cleaned_data.get('thumbnail')
        if f:
            allowed = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            ext = f.name.rsplit('.', 1)[-1].lower()
            if ext not in allowed:
                raise ValidationError("Thumbnail must be jpg, png, gif, or webp. SVG is not allowed.")
        return f