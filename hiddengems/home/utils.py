import re
from django.core.cache import cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Game, SimilarGame


def game_to_text(game):
    """Convert a game's fields into a single string for TF-IDF analysis."""
    return " ".join([
        game.title,
        game.genre,
        game.description,
        game.developer,
        game.publisher
    ])


def clean_title(title):
    stopwords = {'the', 'a', 'an', 'of', 'in', 'and', 'or', 'for'}
    return set(re.sub(r'[^\w\s]', '', title.lower()).split()) - stopwords


def title_similarity_boost(title1, title2):
    """Give a boost if games share significant title words using Jaccard similarity."""
    words1 = clean_title(title1)
    words2 = clean_title(title2)

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2
    jaccard = len(intersection) / len(union)

    # Boost if one title is a subset of the other (e.g. sequels/DLC)
    subset_boost = 0.3 if words1.issubset(words2) or words2.issubset(words1) else 0.0

    return jaccard + subset_boost


def publisher_developer_boost(game1, game2):
    """Give a boost if games share the same publisher or developer."""
    boost = 0.0
    if game1.publisher and game2.publisher:
        if game1.publisher.lower() == game2.publisher.lower():
            boost += 0.2
    if game1.developer and game2.developer:
        if game1.developer.lower() == game2.developer.lower():
            boost += 0.2
    return boost


def compute_tfidf_similarities(game, all_games):
    """Compute TF-IDF cosine similarity between a game and a list of games."""
    corpus = [game_to_text(game)] + [game_to_text(g) for g in all_games]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()


def compute_combined_scores(game, all_games, tfidf_scores):
    """Combine TF-IDF scores with title similarity boost."""
    results = []
    for i, other_game in enumerate(all_games):
        boost = title_similarity_boost(game.title, other_game.title)
        boost += publisher_developer_boost(game, other_game)
        combined_score = tfidf_scores[i] + (boost * 0.4)
        results.append((other_game, combined_score))
    return results


def deduplicate_by_title(scored_games):
    """Remove duplicate titles, keeping the highest scoring game."""
    seen_titles = set()
    deduped = []
    for g, score in scored_games:
        if g.title not in seen_titles:
            seen_titles.add(g.title)
            deduped.append((g, score))
    return deduped


def compute_similar_games(game, min_similarity=0.3):
    """Return up to 9 games similar to the given game."""
    all_games = list(Game.objects.exclude(pk=game.pk))

    if not all_games:
        return []

    tfidf_scores = compute_tfidf_similarities(game, all_games)
    scored_games = compute_combined_scores(game, all_games, tfidf_scores)

    similar = [
        (g, score) for g, score in scored_games
        if score >= min_similarity
    ]
    similar.sort(key=lambda x: x[1], reverse=True)
    similar = deduplicate_by_title(similar)

    return similar[:9]

def store_similar_games(game, scored_games):
    """Persist similar games to the database."""
    SimilarGame.objects.filter(game=game).delete()
    SimilarGame.objects.bulk_create([
        SimilarGame(game=game, similar=g, score=score)
        for g, score in scored_games
    ])


def get_similar_games(game):
    """
    Return up to 9 similar games using memory cache, then DB, then compute.
    Cache is per-game and expires after 1 hour.
    """
    cache_key = f"similar_games_{game.pk}"

    # 1. Check memory cache
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # 2. Check database
    db_results = list(
        SimilarGame.objects.filter(game=game)
        .select_related('similar')
        .order_by('-score')[:9]
    )
    if db_results:
        similar = [entry.similar for entry in db_results]
        cache.set(cache_key, similar, timeout=3600)
        return similar

    # 3. Compute fresh
    scored_games = compute_similar_games(game)
    store_similar_games(game, scored_games)
    similar = [g for g, score in scored_games]
    cache.set(cache_key, similar, timeout=3600)
    return similar