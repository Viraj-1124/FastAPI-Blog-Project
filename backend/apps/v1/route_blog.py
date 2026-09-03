from pathlib import Path

from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from core.config import settings
from core.hashing import Hasher
from core.security import create_access_token
from db.models.user import User
from db.repository.blog import list_blogs, create_new_blog, retreive_blog, update_blog_by_id, delete_blog_by_id
from db.repository.login import get_user_by_email
from db.repository.users import create_new_user
from db.session import get_db
from schemas.blog import CreateBlog, UpdateBlog
from schemas.user import UserCreate

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter()


def get_current_user_from_cookie(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        return get_user_by_email(email=email, db=db)
    except JWTError:
        return None


@router.get("/", include_in_schema=False)
def home(request: Request, db: Session = Depends(get_db)):
    blogs = list_blogs(db)
    current_user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(
        "blogs/home.html",
        {"request": request, "blogs": blogs, "current_user": current_user},
    )


@router.get("/login", include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login", include_in_schema=False)
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(email=email, db=db)
    if not user or not Hasher.verify_password(password, user.password):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Incorrect email or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = create_access_token({"sub": user.email})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response


@router.get("/register", include_in_schema=False)
def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register", include_in_schema=False)
def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user_data = UserCreate(email=email, password=password)
    try:
        create_new_user(user=user_data, db=db)
    except Exception:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "This email is already registered"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/blogs/new", include_in_schema=False)
def create_blog_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "blogs/create.html",
        {"request": request, "current_user": current_user},
    )


@router.post("/blogs/new", include_in_schema=False)
def create_blog_submit(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    blog_data = CreateBlog(title=title, content=content)
    blog = create_new_blog(blog=blog_data, db=db, author_id=current_user.id)
    return RedirectResponse(url=f"/blogs/{blog.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/blogs/{id}", include_in_schema=False)
def blog_detail_page(id: int, request: Request, db: Session = Depends(get_db)):
    blog = retreive_blog(id=id, db=db)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    current_user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(
        "blogs/detail.html",
        {"request": request, "blog": blog, "current_user": current_user},
    )


@router.get("/blogs/{id}/edit", include_in_schema=False)
def blog_edit_page(id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    blog = retreive_blog(id=id, db=db)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if blog.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot edit this blog")

    return templates.TemplateResponse(
        "blogs/edit.html",
        {"request": request, "blog": blog, "current_user": current_user},
    )


@router.post("/blogs/{id}/edit", include_in_schema=False)
def blog_edit_submit(
    id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    updated_blog = UpdateBlog(title=title, content=content)
    blog = update_blog_by_id(id=id, blog=updated_blog, db=db, author_id=current_user.id)
    if isinstance(blog, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=blog.get("error"))
    return RedirectResponse(url=f"/blogs/{id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/blogs/{id}/delete", include_in_schema=False)
def blog_delete_submit(id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    message = delete_blog_by_id(id=id, db=db, author_id=current_user.id)
    if message.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message.get("error"))
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout", include_in_schema=False)
def logout(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response
