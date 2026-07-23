import streamlit as st
import pandas as pd
import pickle

from utils.recommender import (
    recommend_multiple_books,
    hybrid_recommendations
)

def show_recommendations(conn):

    cursor = conn.cursor()
    @st.cache_data
    def load_models():
        search_books = pd.read_csv("models/search_books.csv")
        popularity = pd.read_csv("models/popularity_model.csv")
        return search_books, popularity

    search_books, popularity = load_models()


    with st.sidebar:
        st.title("🍁 BookMate")
        if st.button("🟨 Home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

        if st.button("🟪 Genres", use_container_width=True):
            st.session_state.page = "genres"
            st.rerun()

        if st.button("🟥 Recommendations", use_container_width=True):
            st.rerun()

        if st.button("🟧 Shelves", use_container_width=True):
            st.session_state.page = "shelves"
            st.rerun()

        st.divider()
        st.write(f"👤 **{st.session_state.username}**")

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""
            st.session_state.page = "login"
            st.rerun()

    # Title
    st.markdown(
        "<h1 style='text-align:center;'>"
        " Get Your Personalized Book Recommendations"
        "</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center;'>"
        "Choose 2 or 3 books you enjoyed."
        "</p>",
        unsafe_allow_html=True
    )
    st.divider()

    # Book Search 1
    search1 = st.text_input("🔍 Search Book 1")
    book1 = ""

    if search1:
        results1 = search_books[
            search_books["display_title"].str.contains(
                search1,
                case=False,
                na=False
            )
        ]

        if len(results1) > 0:
            book1 = st.selectbox(
                "Suggestions",
                results1["display_title"].head(10),
                key="book1"
            )

    # Book Search 2
    search2 = st.text_input("🔍 Search Book 2")

    book2 = ""

    if search2:
        results2 = search_books[
            search_books["display_title"].str.contains(
                search2,
                case=False,
                na=False
            )
        ]

        if len(results2) > 0:
            book2 = st.selectbox(
                "Suggestions ",
                results2["display_title"].head(10),
                key="book2"
            )

    # Book Search 3

    search3 = st.text_input("🔍 Search Book 3 (Optional)")

    book3 = ""

    if search3:
        results3 = search_books[
            search_books["display_title"].str.contains(
                search3,
                case=False,
                na=False
            )
        ]

        if len(results3) > 0:
            book3 = st.selectbox(
                "Suggestions  ",
                results3["display_title"].head(10),
                key="book3"
            )

    st.divider()

    # for Generating Recommendations

    if st.button("Click here to Get Recommendations",use_container_width=True):

        selected_books = []
        if book1 != "":
            selected_books.append(book1)

        if book2 != "":
            selected_books.append(book2)

        if book3 != "":
            selected_books.append(book3)

        if len(selected_books) < 2:
            st.warning(
                "Please select at least 2 books."
            )
            st.stop()

        with st.spinner("Finding the books you'll love..."):
            recommendations = hybrid_recommendations(
            conn=conn,
            selected_books=selected_books,
            user_id=st.session_state.user_id,
            top_n=20
            )


            # Randomizing Recommendations
            if not recommendations.empty:

              recommendations = (
              recommendations
              .sample(frac=1)
              .reset_index(drop=True)
            )

            if len(recommendations) < 20:
                existing = set(
                    recommendations["bookId"]
                ) if not recommendations.empty else set()

                existing.update(
                    search_books[
                        search_books["display_title"].isin(selected_books)
                    ]["bookId"]
                )

                extra = popularity[~popularity["bookId"].isin(existing)]
                needed = 20 - len(recommendations)
                recommendations = pd.concat(
                    [
                        recommendations,
                        extra.head(needed)
                    ],
                    ignore_index=True
                )
        st.session_state.hybrid_results = recommendations
        st.success("Recommendations Ready!")
        st.balloons()

    if "hybrid_results" in st.session_state:

        recommendations = st.session_state.hybrid_results
        st.divider()
        st.subheader(" Top Recommendations For You!")
        cols_per_row = 6

        for i in range(
            0,
            len(recommendations),
            cols_per_row
        ):

            cols = st.columns(cols_per_row)
            row = recommendations.iloc[i:i + cols_per_row]
            for col, (_, book) in zip(cols,row.iterrows()):

                with col:
                    cover = book["coverImg"]

                    if pd.notna(cover) and str(cover).startswith("http"):
                        st.image(cover,width=140)

                    else:
                        st.image("https://via.placeholder.com/130x190?text=No+Cover",width=140)

                    st.caption(book["title"][:25])
                    if st.button("Details", key=f"rec_{book['bookId']}"):
                        st.session_state.selected_book = book["bookId"]
                        st.session_state.page = "book_details"
                        st.rerun()
    st.divider()

    if st.button("Back",use_container_width=True):
        st.session_state.page = "recommendations"
        st.rerun()