import streamlit as st
import pandas as pd
import pickle

st.markdown(
"""
<style>
div.stButton > button{
    text-align:left;
    justify-content:flex-start;
}
</style>
""",
unsafe_allow_html=True
)

def show_home(conn):
    cursor = conn.cursor()
    @st.cache_data
    def load_home_data():

        search_books = pd.read_csv("models/search_books.csv")
        popularity_books = pd.read_csv("models/popularity_model.csv")
        with open("models/genre_popularity.pkl", "rb") as f:
            genre_popularity = pickle.load(f)
        return search_books, popularity_books, genre_popularity

    search_books, popularity_books, genre_popularity = load_home_data()

    # Cleaning Books
    def clean_books(df):
      df = df.copy()

      UNWANTED_GENRES = ["erotica","bdsm","reverse harem","dark romance"]
      UNWANTED_TITLE_WORDS = ["seduction","mistress","billionaire","alpha","sex","white hot","temptation","crashed","triology","summary","audiobooks"]
      df = df[
        ~df["genres"].fillna("").str.lower().str.contains(
        "|".join(UNWANTED_GENRES),
        regex=True
      )
      ]

      df = df[
        ~df["title"].fillna("").str.lower().str.contains(
        "|".join(UNWANTED_TITLE_WORDS),
        regex=True
      )
      ]
      df = df.drop_duplicates(subset="title", keep="first")
      df = df.drop_duplicates(subset="bookId",keep="first")
      df = (df.groupby("author", group_keys=False).head(2).reset_index(drop=True))
      return df

    # Randomizing Books
    st.session_state.popular_books_random = clean_books(popularity_books)
    for genre in genre_popularity:
      key = f"{genre}_random"
      if key not in st.session_state:
        books = clean_books( genre_popularity[genre]).head(100)
        st.session_state[key] = (books.sample(frac=1).reset_index(drop=True) )

    with st.sidebar:
        st.title("🍁 BookMate")

        if st.button("🟨 Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

        if st.button("🟪 Genres", use_container_width=True):
            st.session_state.page = "genres"
            st.rerun()

        if st.button("🟥 Recommendations", use_container_width=True):
            st.session_state.page = "recommendations"
            st.rerun()

        if st.button("🟧 Shelves", use_container_width=True):
            st.session_state.page = "shelves"
            st.rerun()

        st.divider()
        st.write(f"👤 **{st.session_state.username}**")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""
            st.session_state.page = "login"
            st.rerun()

    # Search option
    search = st.text_input("Search Books",placeholder="Search by title or keywords...")

    if search:
        results = search_books[
            search_books["title"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

        if len(results) > 0:
            selected_book = st.selectbox("Suggestions",results["title"].head(10))
            if st.button("Open Book"):
                book = results[results["title"] == selected_book].iloc[0]

                st.session_state.selected_book = book["bookId"]
                st.session_state.page = "book_details"
                st.rerun()
        else:
            st.warning("No books found.")

    # book grid Function
    def display_book_grid(
        books,
        key_prefix,
        max_books=20,
        start_index=0
    ):

        books = clean_books(books)
        books = books.iloc[start_index:start_index + max_books]
        cols_per_row = 6

        for i in range(0, len(books), cols_per_row):

            cols = st.columns(cols_per_row)
            row = books.iloc[i:i + cols_per_row]

            for col, (_, book) in zip(cols, row.iterrows()):
                with col:
                    cover = book["coverImg"]
                    if (
                        pd.notna(cover)
                        and str(cover).startswith("http")
                    ):
                        st.image(cover, width=140)

                    else:
                        st.image( "https://via.placeholder.com/140x210?text=No+Cover",width=140)
                    if st.button("Details",key=f"{key_prefix}_{book['bookId']}",help=book["title"]):
                          st.session_state.selected_book = book["bookId"]
                          st.session_state.page = "book_details"
                          st.rerun()

    if "show_popular_more" not in st.session_state:
        st.session_state.show_popular_more = False

    # Popular Books section
    st.subheader(" All Time Favourite Reads")

    display_book_grid(
        st.session_state.popular_books_random,
        "popular"
    )

    if st.button("View More", key="popular_more"):
      st.session_state.show_popular_more = True

    if st.session_state.show_popular_more:
      display_book_grid(
        st.session_state.popular_books_random,
        "popular_more",
        max_books=20,
        start_index=20
      )
    st.divider()
    
    if "show_genre_more" not in st.session_state:
        st.session_state.show_genre_more = False

    # Based on Your Favorite Genres section
    st.subheader(" Based on Your Selected Genres")

    cursor.execute(
     """
     SELECT favorite_genres
     FROM users
     WHERE id=?
     """,
     (st.session_state.user_id,)
    )

    result = cursor.fetchone()
    if result and result[0]:
        user_genres = [
            g.strip()
            for g in result[0].split(",")
            if g.strip()
        ]

        if len(user_genres) > 0:
            first_genre = user_genres[0]
            if first_genre in genre_popularity:
                display_book_grid(
                    st.session_state[f"{first_genre}_random"],
                    "genre"
                )
                if st.button("View More", key="genre_more"):
                   st.session_state.show_genre_more = True

                if st.session_state.show_genre_more:
                   display_book_grid(
                       st.session_state[f"{first_genre}_random"],
                       "genre_more",
                        max_books=20,
                        start_index=20
                    )
    else:
        st.info("Complete your preferences to receive genre recommendations." )