from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.hashing import Hasher
from core.security import create_access_token
from db.base import Base
from db.models.blog import Blog
from db.models.user import User
from db.session import get_db
from main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def reset_db():
    db = SessionTesting()
    db.query(Blog).delete()
    db.query(User).delete()
    db.commit()
    db.close()


def override_get_db():
    db = SessionTesting()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def test_home_page_renders_html():
    reset_db()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Blog" in response.text
    assert "Login" in response.text


def test_create_blog_page_renders_form():
    reset_db()
    db = SessionTesting()
    user = User(email="alice@example.com", password=Hasher.get_password_hash("secret123"), is_active=True)
    db.add(user)
    db.commit()
    db.close()

    client = TestClient(app)
    token = create_access_token({"sub": "alice@example.com"})
    response = client.get("/blogs/new", cookies={"access_token": token})
    assert response.status_code == 200
    assert "Create Blog" in response.text
    assert "title" in response.text.lower()


def test_blog_detail_page_renders_post():
    reset_db()
    db = SessionTesting()
    blog = Blog(title="My First Post", slug="my-first-post", content="Some details", author_id=1, is_active=True)
    db.add(blog)
    db.commit()
    db.close()

    client = TestClient(app)
    response = client.get("/blogs/1")
    assert response.status_code == 200
    assert "My First Post" in response.text
