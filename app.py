import streamlit as st
import sqlite3
import hashlib

st.set_page_config(
    page_title="BookMate AI",
    page_icon="📒",
    layout="wide"
)

# Database Connection
conn = sqlite3.connect("database.db",check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    favorite_genres TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS shelves(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    book_id TEXT,
    shelf TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS favorites(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    book_id TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS recently_viewed(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    book_id TEXT,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
# Session State

if "page" not in st.session_state:
    st.session_state.page = "login"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""

if "selected_book" not in st.session_state:
    st.session_state.selected_book = None

# Password Hash Function
def hash_password(password):
    return hashlib.sha256( password.encode()).hexdigest()

# LOGIN PAGE
if st.session_state.page == "login":
    st.title("Hello, nice to meet You 👋😊")
    st.write("Login to get your recommendations.")
    username = st.text_input("Username")
    password = st.text_input(
        "Password",
        type="password"
    )

    col1, col2 = st.columns(2)
    with col1:

        if st.button("Login", use_container_width=True):
            cursor.execute(
                "SELECT * FROM users WHERE username=?",
                (username,)
            )
            user = cursor.fetchone()
            if user is None:
                st.error(
                    "User doesn't exist. Please Sign Up first."
                )

            elif user[2] != hash_password(password):
                st.error("Incorrect Password.")

            else:
                st.success("Login Successful!")
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]
                st.session_state.page = "home"
                st.rerun()

    with col2:
        if st.button("Sign Up", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

# SIGN UP PAGE
elif st.session_state.page == "signup":
    st.title("Create Your Account")
    new_username = st.text_input("Username")
    new_password = st.text_input("Password",type="password")
    genres = st.multiselect(
        "Favorite Genres",
        ["Adventure","Fantasy","Classics","Mystery","Romance","Science Fiction","Thriller","Horror","Historical","Young Adult",],
        max_selections=3
    )

    if st.button( "Create Account", use_container_width=True):
        if new_username == "" or new_password == "":
            st.warning("Please fill all the fields.")

        elif len(genres) == 0:
            st.warning("Please choose at least one genre.")

        else:
            cursor.execute(
                "SELECT * FROM users WHERE username=?",
                (new_username,)
            )

            existing_user = cursor.fetchone()
            if existing_user:
                st.error("Username already exists.")
            else:
                cursor.execute(
                    """
                    INSERT INTO users
                    (username,password,favorite_genres)
                    VALUES(?,?,?)
                    """,
                    (
                        new_username,
                        hash_password(new_password),
                        ",".join(genres)
                    )
                )
                conn.commit()
                st.success("Account Created Successfully!")
                st.session_state.page = "login"
                st.rerun()

# HOME
elif st.session_state.page == "home":
    from pages_BV.home import show_home
    show_home(conn)

# GENRES
elif st.session_state.page == "genres":
    from pages_BV.genres import show_genres
    show_genres(conn)

# HYBRID RECOMMENDATIONS
elif st.session_state.page == "recommendations":
    from pages_BV.recommendations import show_recommendations
    show_recommendations(conn)

# SHELVES
elif st.session_state.page == "shelves":
    from pages_BV.shelves import show_shelves
    show_shelves(conn)

# BOOK DETAILS
elif st.session_state.page == "book_details":
    from pages_BV.book_details import show_book_details
    show_book_details(conn)