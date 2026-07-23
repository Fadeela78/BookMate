import streamlit as st
import pandas as pd
original_books = pd.read_csv("models/books.csv")

from utils.recommender import (
    recommend_books,
    collaborative_recommendations,
)

def show_book_details(conn):

    cursor = conn.cursor()
    books = pd.read_csv("models/books_final.csv")
    if (
        "selected_book" not in st.session_state
        or st.session_state.selected_book is None
    ):
        st.warning("No book selected.")
        return

    selected_book_id = st.session_state.selected_book
    book = books[books["bookId"] == selected_book_id]
    if book.empty:
        st.error("Book not found.")
        return
    
    book = book.iloc[0]
    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()
    st.divider()

    # Books details
    col1, col2 = st.columns([1, 2])
    with col1:
        if (
            "coverImg" in book
            and pd.notna(book["coverImg"])
            and str(book["coverImg"]).strip() != ""
        ):
            st.image(book["coverImg"],width=180)
        else:
            st.image("https://via.placeholder.com/250x380?text=No+Cover",width=180)

    with col2:
        st.title(book["title"].title())
        if pd.notna(book["author"]):
            st.write(f"**Author:** {book['author']}")

        if "genres" in book.index and pd.notna(book["genres"]):
            st.write(f"**Genres:** {book['genres']}")

        if "rating" in book.index and pd.notna(book["rating"]):
            st.write(f"⭐ **Rating:** {book['rating']}")

        if "pages" in book.index and pd.notna(book["pages"]):
            st.write(f" **Pages:** {book['pages']}")

        if "publisher" in book.index and pd.notna(book["publisher"]):
            st.write(f"**Publisher:** {book['publisher']}")

        if "publishDate" in book.index and pd.notna(book["publishDate"]):
            st.write(f"**Published:** {book['publishDate']}")

    st.divider()

    # Description section
    st.subheader("Description")
    if (
        pd.notna(book["description"])
        and str(book["description"]).strip() != ""
    ):
        original = original_books[original_books["bookId"] == book["bookId"]]
        if not original.empty:
            description = original.iloc[0]["description"]
        else:
            description = book["description"]
        st.write(description)
    else:
        st.info("No description available.")

    st.divider()
    st.subheader("Favorites")

    def save_to_favorites():
      cursor.execute("""
        SELECT id
        FROM favorites
        WHERE user_id = ?
        AND book_id = ?
      """, (
        st.session_state.user_id,
        selected_book_id
      ))

      existing = cursor.fetchone()
      if existing:
        st.info("Already in Favorites.")
        return

      cursor.execute("""
        INSERT INTO favorites
        (user_id, book_id)
        VALUES (?, ?)
      """, (
        st.session_state.user_id,
        selected_book_id
      ))
      conn.commit()
      st.success("Added to Favorites ❤️")

    if st.button("❤️ Add to Favorites"):
      save_to_favorites()


    st.subheader("My Shelf")

    col1, col2, col3, col4 = st.columns(4)
    shelves = {
        "Currently Reading": "currently_reading",
        "Want to Read": "want_to_read",
        "Finished": "finished",
        "Did Not Finish": "did_not_finish"
    }

    def save_to_shelf(shelf_name):
        if "user_id" not in st.session_state:
            st.error("Please login first.")
            return
        cursor.execute("""
            SELECT id
            FROM shelves
            WHERE user_id = ?
            AND book_id = ?
        """, (
            st.session_state.user_id,
            selected_book_id
        ))

        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE shelves
                SET shelf = ?
                WHERE user_id = ?
                AND book_id = ?
            """, (
                shelf_name,
                st.session_state.user_id,
                selected_book_id
            ))

        else:
            cursor.execute("""
                INSERT INTO shelves
                (user_id, book_id, shelf)
                VALUES (?, ?, ?)
            """, (
                st.session_state.user_id,
                selected_book_id,
                shelf_name,

            ))
        conn.commit()
        st.success(f"Added to '{shelf_name}'")

    with col1:
        if st.button(" Currently Reading"):
            save_to_shelf(shelves["Currently Reading"])

    with col2:
        if st.button(" Want to Read"):
            save_to_shelf(shelves["Want to Read"])

    with col3:
        if st.button(" Finished"):
            save_to_shelf(shelves["Finished"])

    with col4:
        if st.button(" Did Not Finish"):
            save_to_shelf(shelves["Did Not Finish"])
    st.divider()

    # Similar Books
    st.subheader("You Might Also Like")
    try:

        recommendations = recommend_books(
            selected_book_id,
            top_n=10
        )
        if recommendations is not None and len(recommendations) > 0:
            cols_per_row = 6

            for i in range(0, len(recommendations), cols_per_row):
              cols = st.columns(cols_per_row)
              row = recommendations.iloc[i:i+cols_per_row]
              for col, (_, rec) in zip(cols, row.iterrows()):
                with col:

                  cover = rec["coverImg"]
                  if pd.notna(cover) and str(cover).startswith("http"):
                     st.image(cover,width=140)
 
                  else:
                     st.image("https://via.placeholder.com/130x190?text=No+Cover",width=140)
                  st.caption(rec["title"][:28])

                  if st.button(
                    "Details",
                    key=f"content_{rec['bookId']}"
                  ):

                      st.session_state.selected_book = rec["bookId"]
                      st.session_state.page = "book_details"
                      st.rerun()
        else:
                st.info("No similar books found.")
    except Exception as e:
          st.error(f"Error: {e}")

    st.divider()
    # Collaborative Recommendations

    st.subheader("Readers Also Enjoyed")
    try:
        cf_recommendations = collaborative_recommendations(
            selected_book_id,
            top_n=10
        )

        if (
        cf_recommendations is not None
        and len(cf_recommendations) > 0
        ):
            cols_per_row = 6
            for i in range(0, len(cf_recommendations), cols_per_row):
               cols = st.columns(cols_per_row)
               row = cf_recommendations.iloc[i:i+cols_per_row]

               for col, (_, rec) in zip(cols, row.iterrows()):
                  with col:

                    cover = rec["coverImg"]
                    if pd.notna(cover) and str(cover).startswith("http"):
                      st.image(cover,width=140)
                    else:
                      st.image("https://via.placeholder.com/130x190?text=No+Cover",width=140)
                    st.caption(rec["title"][:28])

                    if st.button(
                        "Details",
                         key=f"cf_{rec['bookId']}"
                    ):
                      st.session_state.selected_book = rec["bookId"]
                      st.session_state.page = "book_details"
                      st.rerun()
        else:
              st.info("Reader activity for this book is limited,so collaborative recommendations aren't available yet.")

    except Exception as e:
        st.warning("Collaborative model unavailable.")
