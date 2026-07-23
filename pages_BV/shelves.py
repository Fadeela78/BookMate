import streamlit as st
import pandas as pd

def show_shelves(conn):
    cursor = conn.cursor()
    books = pd.read_csv("models/books_final.csv")
   
    def display_section(title, dataframe, table_name, expand_key):

        st.subheader(title)
        if dataframe.empty:
            st.info("No books found.")
            return
        show_all = st.session_state.get(expand_key, False)

        if show_all:
            display_books = dataframe
        else:
            display_books = dataframe.head(6)
        cols_per_row = 6
        for i in range(0, len(display_books), cols_per_row):

            cols = st.columns(cols_per_row)
            row = display_books.iloc[i:i + cols_per_row]
            for col, (_, book) in zip(cols, row.iterrows()):
                with col:
                    cover = book["coverImg"]
                    if pd.notna(cover) and str(cover).startswith("http"):
                        st.image(cover,width=120)

                    else:
                        st.image("https://via.placeholder.com/120x180?text=No+Cover",width=120)
                    st.caption(book["title"][:25])
                    c1, c2 = st.columns(2)

                    with c1:

                        if st.button(
                            "View",
                            key=f"view_{table_name}_{book['bookId']}"
                        ):
                            st.session_state.selected_book = book["bookId"]
                            st.session_state.page = "book_details"
                            st.rerun()
                    with c2:
                        if st.button(
                            "❌",
                            key=f"remove_{table_name}_{book['bookId']}"
                        ):

                            if table_name == "favorites":
                                cursor.execute(
                                    """
                                    DELETE FROM favorites
                                    WHERE user_id=? AND book_id=?
                                    """,
                                    (
                                        st.session_state.user_id,
                                        book["bookId"]
                                    )
                                )
                            else:
                                cursor.execute(
                                    """
                                    DELETE FROM shelves
                                    WHERE user_id=? AND book_id=?
                                    """,
                                    (
                                        st.session_state.user_id,
                                        book["bookId"]
                                    )
                                )
                            conn.commit()
                            st.rerun()

        if len(dataframe) > 6:
            if not show_all:
                if st.button(
                    f"View More {title}",
                    key=f"more_{expand_key}"
                ):
                    st.session_state[expand_key] = True
                    st.rerun()

            else:
                if st.button(
                    f"Show Less {title}",
                    key=f"less_{expand_key}"
                ):
                    st.session_state[expand_key] = False
                    st.rerun()

    # FAVORITES SHELF
    cursor.execute(
        """
        SELECT book_id
        FROM favorites
        WHERE user_id=?
        """,
        (
            st.session_state.user_id,
        )
    )

    favorite_ids = [row[0] for row in cursor.fetchall()]
    favorites = books[books["bookId"].isin(favorite_ids)]
    display_section(
        "❤️ Favorites",
        favorites,
        "favorites",
        "expand_favorites"
    )

    st.divider()

    # WANT TO READ SHELF
    cursor.execute(
        """
        SELECT book_id
        FROM shelves
        WHERE user_id=?
        AND shelf=?
        """,
        (
            st.session_state.user_id,
            "📖 Want to Read"
        )
    )
    want_ids = [row[0] for row in cursor.fetchall()]
    want_books = books[books["bookId"].isin(want_ids)]
    display_section(
        "📖 Want to Read",
        want_books,
        "want",
        "expand_want"
    )
    st.divider()

    # READING SHELF
    cursor.execute(
        """
        SELECT book_id
        FROM shelves
        WHERE user_id=?
        AND shelf=?
        """,
        (
            st.session_state.user_id,
            "📚 Reading"
        )
    )
    reading_ids = [row[0] for row in cursor.fetchall()]
    reading_books = books[books["bookId"].isin(reading_ids)]
    display_section(
        "📚 Reading",
        reading_books,
        "reading",
        "expand_reading"
    )
    st.divider()

    # FINISHED SHELF
    cursor.execute(
        """
        SELECT book_id
        FROM shelves
        WHERE user_id=?
        AND shelf=?
        """,
        (
            st.session_state.user_id,
            "✅ Finished"
        )
    )
    finished_ids = [row[0] for row in cursor.fetchall()]
    finished_books = books[books["bookId"].isin(finished_ids)]
    display_section(
        "✅ Finished",
        finished_books,
        "finished",
        "expand_finished"
    )
    st.divider()

    # DID NOT FINISH SHELF
    cursor.execute(
        """
        SELECT book_id
        FROM shelves
        WHERE user_id=?
        AND shelf=?
        """,
        (
            st.session_state.user_id,
            "❌ Did Not Finish"
        )
    )
    dnf_ids = [row[0] for row in cursor.fetchall()]
    dnf_books = books[
        books["bookId"].isin(dnf_ids)
    ]
    display_section(
        "❌ Did Not Finish",
        dnf_books,
        "dnf",
        "expand_dnf"
    )
    st.divider()

    # BACK BUTTON
    if st.button("⬅ Back to Home"):
        st.session_state.page = "home"
        st.rerun()