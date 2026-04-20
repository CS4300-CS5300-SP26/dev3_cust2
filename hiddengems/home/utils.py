from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Game
import re


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


def get_similar_games(game, min_similarity=0.4):
    """Return up to 6 games similar to the given game."""
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
    return [g for g, score in similar[:6]]