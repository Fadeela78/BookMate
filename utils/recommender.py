import pandas as pd
import pickle
import re
import random
import isbnlib
from sklearn.metrics.pairwise import cosine_similarity

books_original = pd.read_csv("models/books.csv")
books = pd.read_csv("models/books_final.csv")

with open("models/tfidf_matrix.pkl", "rb") as f:
    tfidf_matrix = pickle.load(f)

with open("models/book_indices.pkl", "rb") as f:
    indices = pickle.load(f)

    books_cf = pd.read_csv("models/books_cf.csv")
    ratings = pd.read_csv("models/ratings_cf.csv")

EXCLUDE_PATTERNS = (
    r"box set|boxed set|collection|complete collection|"
    r"omnibus|gift set|slipcase|companion|"
    r"guide|study guide|summary|analysis|"
    r"illustrated|calendar|journal|"
    r"workbook|coloring|encyclopedia|"
    r"companion guide|notes"
)

# CLEAN AUTHOR FUNCTION
def clean_author(author):

    author = str(author)
    author = re.sub(r"\(.*?\)", "", author)

    author = re.sub(
        r"goodreads author",
        "",
        author,
        flags=re.IGNORECASE
    )

    author = re.split(
        r"\b(editor|illustrator|translator|narrator|introduction|foreword|afterword|compiled by|adapted by|pseudonym)\b",
        author,
        flags=re.IGNORECASE
    )[0]

    words = author.split()
    if len(words) >= 2:
       author = " ".join(words[:2])
    else:
       author = " ".join(words)
    author = re.sub(r"\s+", " ", author).strip()
    return author.title()

def format_genres(genres):
    if pd.isna(genres):
        return ""
    genres = str(genres)
    genres = genres.replace("[", "")
    genres = genres.replace("]", "")
    genres = genres.replace("'", "")
    genres = genres.replace('"', "")

    parts = []
    for item in genres.split(","):
        item = item.strip()
        if item != "":
            parts.append(item.title())
    return " • ".join(parts)

def normalize_title(title):
    title = str(title).lower()
    title = re.sub(
        EXCLUDE_PATTERNS,
        "",
        title,
        flags=re.IGNORECASE
    )
    title = re.sub(
        r"\s+",
        " ",
        title
    ).strip()
    return title

def filter_recommendations(candidate_indices,selected_books=None,top_n=10):
    recommendations = []
    seen_titles = set()
    author_count = {}
    if selected_books is None:
        selected_books = set()
    else:
        selected_books = set(selected_books)

    for i in candidate_indices:

        row = books.iloc[i]
        genres = str(row["genres"]).lower()

        UNWANTED_GENRES = [
        "erotica",
        "bdsm",
        "reverse harem",
        "dark romance"
        ]

        if any(g in genres for g in UNWANTED_GENRES):
            continue
        if not row["is_main_book"]:
            continue

        title = str(row["display_title"])

        UNWANTED_TITLE_WORDS = ["seduction","mistress","billionaire","alpha","sex","white hot","temptation","crashed","triology","set" ]

        if any(word in title.lower() for word in UNWANTED_TITLE_WORDS):
          continue

        if title in selected_books:
            continue

        normalized = normalize_title(title)
        if normalized in seen_titles:
            continue

        seen_titles.add(normalized)
        author = clean_author(row["author"])
        author = clean_author(row["author"])
        print(row["title"], "->", repr(author))
        print(repr(author))
        if author_count.get(author, 0) >= 2:
            continue

        author_count[author] = author_count.get(author, 0) + 1
        row = row.copy()
        row["author"] = author
        row["genres"] = format_genres(row["genres"])
        recommendations.append(row)
        if len(recommendations) >= top_n:
            break

    recommendations = pd.DataFrame(recommendations)
    recommendations.reset_index(drop=True, inplace=True)
    return recommendations

def get_random_candidates(similarity_scores,pool_size=100):
    sorted_indices = similarity_scores.argsort()[::-1]
    top_candidates = list(sorted_indices[:pool_size])
    random.shuffle(top_candidates)
    return top_candidates

# ISBN Functions
def get_isbn10_from_bookid(book_id):
    """
    Convert a BookMate bookId into ISBN-10
    """
    print("Received:", book_id)
    book = books_original[
        books_original["bookId"] == book_id
    ]
    print(book.head())

    if book.empty:
        return None

    isbn13 = str(book.iloc[0]["isbn"]).strip()

    if (
        isbn13 == ""
        or isbn13 == "9999999999999"
        or isbn13.lower() == "nan"
    ):
        return None

    try:
        return isbnlib.to_isbn10(isbn13)
    except Exception:
        return None

def get_cf_bookid_from_isbn10(isbn10):
    """
    Find the Goodbooks book_id from ISBN-10
    """
    isbn10 = isbn10.lstrip("0")
    match = books_cf[books_cf["isbn"].astype(str) == isbn10]
    if match.empty:
        return None
    return int(match.iloc[0]["book_id"])

def get_bookid_from_cf_bookid(cf_book_id):
    match = books_cf[books_cf["book_id"] == cf_book_id]
    if match.empty:
        return None
    isbn10 = str(match.iloc[0]["isbn"]).zfill(10)

    try:
        isbn13 = isbnlib.to_isbn13(isbn10)
    except Exception:
        return None
    original = books_original[books_original["isbn"].astype(str).str.strip() == isbn13]
    if original.empty:
        return None

    return original.iloc[0]["bookId"]


# ContentBased Recommendation
def recommend_books(bookId, top_n=6):
    book = books[books["bookId"] == bookId]
    if book.empty:
        return pd.DataFrame()

    display_title = book.iloc[0]["display_title"]
    if display_title not in indices:
        return pd.DataFrame()
    idx = indices[display_title]

    similarity_scores = cosine_similarity(tfidf_matrix[idx],tfidf_matrix).flatten()
    candidate_indices = get_random_candidates(similarity_scores,pool_size=100)
    return filter_recommendations(
        candidate_indices=candidate_indices,
        selected_books=[display_title],
        top_n=top_n
    )

# Multi Book Recommendation

def recommend_multiple_books(book_list, top_n=20):
    similarity = None
    valid_books = 0
    for title in book_list:
        if title not in indices:
            continue
        idx = indices[title]
        scores = cosine_similarity(
            tfidf_matrix[idx],
            tfidf_matrix
        ).flatten()

        if similarity is None:
            similarity = scores
        else:
            similarity += scores

        valid_books += 1

    if valid_books == 0:
        return pd.DataFrame()
    similarity = similarity / valid_books
    candidate_indices = get_random_candidates(similarity,pool_size=100)
    return filter_recommendations(
        candidate_indices=candidate_indices,
        selected_books=book_list,
        top_n=top_n
    )


# Random Genre Books
def get_random_genre_books(genre,
                           top_n=12,
                           pool_size=100):

    genre_books = books.copy()
    genre_books = genre_books[
        genre_books["genres"]
        .str.contains(
            genre,
            case=False,
            na=False
        )
    ]
    genre_books = genre_books[genre_books["is_main_book"] == True]
    if genre_books.empty:
        return pd.DataFrame()
    if "rating" in genre_books.columns:
        genre_books = genre_books.sort_values(
            by="rating",
            ascending=False
        )

    if len(genre_books) > pool_size:
        genre_books = genre_books.head(pool_size)
    genre_books = genre_books.sample(
        frac=1
    ).reset_index(drop=True)

    recommendations = []
    seen_titles = set()
    author_count = {}

    for _, row in genre_books.iterrows():
        title = str(row["display_title"])
        normalized = normalize_title(title)
        if normalized in seen_titles:
            continue

        seen_titles.add(normalized)
        author = clean_author(row["author"])
        if author_count.get(author, 0) >= 2:
            continue
        author_count[author] = author_count.get(author, 0) + 1
        row = row.copy()
        row["author"] = author
        row["genres"] = format_genres(row["genres"])
        recommendations.append(row)

        if len(recommendations) >= top_n:
            break

    return pd.DataFrame(recommendations).reset_index(drop=True)

# Collaborative Recommendation
def collaborative_recommendations(book_id, top_n=10):
    isbn10 = get_isbn10_from_bookid(book_id)
    if isbn10 is None:
        return pd.DataFrame()
    cf_book_id = get_cf_bookid_from_isbn10(isbn10)
    if cf_book_id is None:
        return pd.DataFrame()

    users = ratings[
        ratings["book_id"] == cf_book_id
    ]["user_id"].unique()
    if len(users) == 0:
        return pd.DataFrame()

    candidate_books = ratings[ratings["user_id"].isin(users)]
    candidate_books = candidate_books[candidate_books["book_id"] != cf_book_id]
    candidate_books = candidate_books[candidate_books["rating"] >= 4]
 
    # Score books using popularity and average rating
    scores = (
      candidate_books
      .groupby("book_id")
      .agg(
         user_count=("user_id", "count"),
         avg_rating=("rating", "mean")
      )
    )

    scores["score"] = (scores["user_count"] * scores["avg_rating"])
    counts = (scores.sort_values("score", ascending=False).head(200) )
    recommendations = []

    seen = set()
    author_count = {}

    for cf_id in counts.index:

        bv_id = get_bookid_from_cf_bookid(cf_id)
        if bv_id is None:
            continue
        if bv_id in seen:
            continue
        seen.add(bv_id)
        book = books[books["bookId"] == bv_id]
        if book.empty:
            continue

        row = book.iloc[0]
        if not row["is_main_book"]:
            continue

        row = row.copy()
        if row["bookId"] == book_id:
          continue

        author = clean_author(row["author"])
        if author_count.get(author, 0) >= 2:
          continue

        author_count[author] = author_count.get(author, 0) + 1
        row["author"] = author
        row["genres"] = format_genres(row["genres"])
        recommendations.append(row)
        if len(recommendations) >= top_n:
            break

    return pd.DataFrame(recommendations).reset_index(drop=True)

# Hybrid Recommendation

def hybrid_recommendations(
    conn,
    user_id,
    selected_books,
    top_n=20
):
    
    cursor = conn.cursor()
    all_books = list(selected_books)
    content = recommend_multiple_books(
        all_books,
        top_n=50
    )
    print("Content recommendations:", len(content))

    selected_ids = books[
        books["display_title"].isin(all_books)
    ]["bookId"].tolist()
    collaborative = pd.DataFrame()

    for book_id in selected_ids:
       cf = collaborative_recommendations(
          book_id,
          top_n=20
       )
       if not cf.empty:
          collaborative = pd.concat(
              [collaborative, cf],
              ignore_index=True
            )
    print("Collaborative recommendations:", len(collaborative))

    # Merge Recommendations
    content["recommendation_type"] = "Content"
    collaborative["recommendation_type"] = "Collaborative"
    recommendations = pd.concat([collaborative, content],ignore_index=True)
    print("Merged recommendations:", len(recommendations))

    if recommendations.empty:
        return recommendations

    recommendations = recommendations.drop_duplicates(subset="bookId")
    print("After duplicate removal:", len(recommendations))
    
    recommendations = recommendations[~recommendations["bookId"].isin(selected_ids)]
    recommendations = recommendations.reset_index(drop=True)

    print("Final recommendations:", len(recommendations.head(top_n)))
    return recommendations.head(top_n)
