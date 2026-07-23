import streamlit as st
import pickle
import pandas as pd

def show_genres(conn):
    @st.cache_data
    def load_genres():

        with open("models/genre_popularity.pkl", "rb") as f:
            genre_popularity = pickle.load(f)
        return genre_popularity
    genre_popularity = load_genres()

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

    st.title("📚 Browse by Genre")

    def display_genre(genre_name):
        if genre_name not in genre_popularity:
            return

        random_key = f"{genre_name}_random"
        if random_key not in st.session_state:
            st.session_state[random_key] = (
                genre_popularity[genre_name]
                .sample(frac=1)
                .reset_index(drop=True)
            )

        books = st.session_state[random_key]

        # Filtering unwanted books
        UNWANTED_GENRES = ["erotica","bdsm","reverse harem","dark romance"]
        UNWANTED_TITLE_WORDS = ["seduction","mistress","billionaire","alpha","sex","white hot","temptation","crashed","triology","summary","audiobooks"]

        books = books[
           ~books["genres"].fillna("").str.lower().str.contains(
           "|".join(UNWANTED_GENRES),
           regex=True
        )
        ]

        books = books[
          ~books["title"].fillna("").str.lower().str.contains(
          "|".join(UNWANTED_TITLE_WORDS),
           regex=True
        )
        ]

        view_more_key = f"view_more_{genre_name}"
        if view_more_key not in st.session_state:
            st.session_state[view_more_key] = False
        st.subheader(f"📖 {genre_name}")

        if st.session_state[view_more_key]:
            display_books = books.iloc[6:12]
        else:
            display_books = books.iloc[:6]

        cols_per_row = 6
        for i in range(0, len(display_books), cols_per_row):
            cols = st.columns(cols_per_row)
            row = display_books.iloc[i:i + cols_per_row]
            for col, (_, book) in zip(cols, row.iterrows()):
                with col:
                    cover = book["coverImg"]
                    if (
                        pd.notna(cover)
                        and str(cover).startswith("http")
                    ):
                        st.image(cover,width=140)

                    else:
                        st.image("https://via.placeholder.com/140x210?text=No+Cover",width=140)
                    st.caption(book["title"][:22])

                    if st.button(
                        "Details",
                        key=f"{genre_name}_{book['bookId']}"
                    ):
                        st.session_state.selected_book = book["bookId"]
                        st.session_state.page = "book_details"
                        st.rerun()

        if len(books) > 6:
            if not st.session_state[view_more_key]:

                if st.button(
                    "View More",
                    key=f"more_{genre_name}"
                ):
                    st.session_state[view_more_key] = True
                    st.rerun()
            else:

                if st.button(
                    "Show Less",
                    key=f"less_{genre_name}"
                ):
                    st.session_state[view_more_key] = False
                    st.rerun()

        st.divider()

    # Popular Genres
    popular_genres = ["Fantasy","Classics","Romance","Mystery","Science Fiction","Young Adult","Historical Fiction"]
    for genre in popular_genres:
        display_genre(genre)

    st.divider()
    if st.button(
        "⬅ Back to Home",
        use_container_width=True
    ):
        st.session_state.page = "home"
        st.rerun()