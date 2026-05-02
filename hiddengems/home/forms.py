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

    # Steam Integration fields
    on_steam = forms.BooleanField(
        required=False,
        label="Is this game on Steam?"
    )
    steam_id = forms.IntegerField(
        required=False,
        label="Steam App ID",
        help_text="Enter the numeric Steam App ID (e.g. 440 for Team Fortress 2)"
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
            "on_steam",
            "steam_id",
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

    def clean_steam_id(self):
        on_steam = self.cleaned_data.get('on_steam')
        steam_id = self.cleaned_data.get('steam_id')

        # Only validate Steam App ID if the user indicated the game is on Steam
        if on_steam:
            if not steam_id:
                raise ValidationError("Please enter a Steam App ID.")

            # Check uniqueness — exclude the current game if this is an edit
            qs = Game.objects.filter(storefront='steam', game_id=steam_id)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    "A game with this Steam App ID is already listed on Hidden Gems."
                )

        return steam_id

    def save(self, commit=True):
        game = super().save(commit=False)
        # Map the form's steam fields → model's storefront/game_id fields
        if self.cleaned_data.get('on_steam'):
            game.storefront = 'steam'
            game.game_id = self.cleaned_data.get('steam_id')
        else:
            game.storefront = ''
            game.game_id = None
        if commit:
            game.save()
        return game

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