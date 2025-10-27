"""
Routes d'authentification pour l'API AGI
Gestion des utilisateurs, sessions et tokens JWT
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import jwt
import bcrypt
import asyncpg

from backend.config.settings import get_settings
from backend.api.dependencies import CurrentUserDep

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
settings = get_settings()

# Modèles Pydantic pour les requêtes/réponses
class UserRegistration(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    username: str

class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

# Utilitaires pour JWT et mots de passe
def create_access_token(user_id: str, username: str) -> tuple[str, datetime]:
    """Crée un token JWT d'accès"""
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expires_at,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    return token, expires_at

def verify_token(token: str) -> Dict[str, Any]:
    """Vérifie et décode un token JWT"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Dependency pour récupérer l'utilisateur actuel
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Récupère l'utilisateur actuel depuis le token JWT"""
    payload = verify_token(credentials.credentials)
    
    # TODO: Récupérer les infos utilisateur depuis la base de données
    # Pour l'instant, retourner les infos du token
    return {
        "user_id": payload["user_id"],
        "username": payload["username"]
    }

# Routes d'authentification
@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegistration) -> TokenResponse:
    """Inscription d'un nouvel utilisateur"""
    
    try:
        # TODO: Intégrer avec la vraie base de données PostgreSQL
        # Pour l'instant, simulation de l'inscription
        
        # Vérifier si l'utilisateur existe déjà (simulation)
        # Dans la vraie implémentation, vérifier en base
        
        # Hasher le mot de passe
        hashed_password = hash_password(user_data.password)
        
        # Créer l'utilisateur (simulation)
        user_id = str(uuid4())
        
        # TODO: Insérer en base de données
        # INSERT INTO users (id, email, username, password_hash, full_name, created_at)
        # VALUES (user_id, user_data.email, user_data.username, hashed_password, user_data.full_name, NOW())
        
        # Créer le token d'accès
        access_token, expires_at = create_access_token(user_id, user_data.username)
        
        # TODO: Créer une session en base
        # INSERT INTO user_sessions (id, user_id, token_hash, expires_at, created_at)
        
        return TokenResponse(
            access_token=access_token,
            expires_in=86400,  # 24 heures en secondes
            user_id=user_id,
            username=user_data.username
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'inscription: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin) -> TokenResponse:
    """Connexion d'un utilisateur existant"""
    
    try:
        # TODO: Récupérer l'utilisateur depuis la base de données
        # SELECT id, username, password_hash FROM users WHERE email = login_data.email
        
        # Pour l'instant, simulation avec un utilisateur de test
        if login_data.email == "admin@agi.local" and login_data.password == "admin123":
            user_id = "test-user-uuid"
            username = "admin"
            
            # Créer le token d'accès
            access_token, expires_at = create_access_token(user_id, username)
            
            # TODO: Mettre à jour last_login et créer une session
            # UPDATE users SET last_login = NOW() WHERE id = user_id
            # INSERT INTO user_sessions (id, user_id, token_hash, expires_at, created_at)
            
            return TokenResponse(
                access_token=access_token,
                expires_in=86400,
                user_id=user_id,
                username=username
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la connexion: {str(e)}"
        )

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)) -> UserProfile:
    """Récupère le profil de l'utilisateur actuel"""
    
    try:
        # TODO: Récupérer les infos complètes depuis la base de données
        # SELECT id, email, username, full_name, created_at, last_login 
        # FROM users WHERE id = current_user["user_id"]
        
        # Pour l'instant, retourner des données simulées
        return UserProfile(
            id=current_user["user_id"],
            email="admin@agi.local",
            username=current_user["username"],
            full_name="Administrateur AGI",
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du profil: {str(e)}"
        )

@router.post("/logout")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    """Déconnexion de l'utilisateur (invalide le token)"""
    
    try:
        # TODO: Invalider la session en base de données
        # UPDATE user_sessions SET is_active = FALSE 
        # WHERE user_id = current_user["user_id"] AND is_active = TRUE
        
        return {"message": "Déconnexion réussie"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la déconnexion: {str(e)}"
        )

@router.post("/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)) -> TokenResponse:
    """Renouvelle le token d'accès"""
    
    try:
        # Créer un nouveau token
        access_token, expires_at = create_access_token(
            current_user["user_id"], 
            current_user["username"]
        )
        
        # TODO: Mettre à jour la session en base
        # UPDATE user_sessions SET token_hash = hash(access_token), expires_at = expires_at
        # WHERE user_id = current_user["user_id"] AND is_active = TRUE
        
        return TokenResponse(
            access_token=access_token,
            expires_in=86400,
            user_id=current_user["user_id"],
            username=current_user["username"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du renouvellement du token: {str(e)}"
        )

@router.get("/verify")
async def verify_token_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Vérifie la validité du token actuel"""
    
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "timestamp": datetime.utcnow().isoformat()
    }