from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext as _
from typing import List, Optional
from .models import User, NetworkNode, Equipment, UserProposal, Comment, NewsArticle
from .services.solana_client import SolanaClient
import uuid

api = NinjaAPI(title="Z96A API", version="1.0.0")

class SolanaAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            solana_client = SolanaClient()
            is_valid = solana_client.verify_signature(token)
            if is_valid:
                # Get or create user based on wallet address
                wallet_address = solana_client.get_address_from_token(token)
                user, created = User.objects.get_or_create(
                    wallet_address=wallet_address,
                    defaults={'username': f"user_{wallet_address[:8]}"}
                )
                return user
        except:
            pass
        return AnonymousUser()

class WalletConnectSchema(Schema):
    wallet_address: str
    signature: str
    message: str

class ProposalSchema(Schema):
    title: str
    description: str
    proposal_type: str
    target_node: Optional[uuid.UUID] = None
    proposed_equipment: Optional[uuid.UUID] = None
    quantity: int = 1
    justification: str
    solana_tx_signature: str

class CommentSchema(Schema):
    content: str
    parent_comment: Optional[uuid.UUID] = None

@api.post("/connect-wallet", auth=None)
def connect_wallet(request, data: WalletConnectSchema):
    """Connect Solana wallet and authenticate user"""
    solana_client = SolanaClient()
    
    try:
        # Verify signature
        is_valid = solana_client.verify_signature(
            data.signature,
            data.message,
            data.wallet_address
        )
        
        if not is_valid:
            return {"success": False, "error": _("Invalid signature")}
        
        # Get or create user
        user, created = User.objects.get_or_create(
            wallet_address=data.wallet_address,
            defaults={
                'username': f"user_{data.wallet_address[:8]}",
                'nickname': f"User_{data.wallet_address[-8:]}"
            }
        )
        
        # Generate auth token
        token = solana_client.generate_auth_token(user.wallet_address)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "nickname": user.nickname,
                "wallet_address": user.wallet_address,
                "is_verified": user.is_verified,
                "reputation_score": user.reputation_score
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@api.get("/network/nodes")
def get_network_nodes(request):
    """Get all network nodes"""
    nodes = NetworkNode.objects.all()
    return [
        {
            "id": str(node.id),
            "name": node.name,
            "type": node.node_type,
            "network_type": node.network_type,
            "latitude": node.latitude,
            "longitude": node.longitude,
            "altitude": node.altitude,
            "country": node.country,
            "city": node.city,
            "capacity_gbps": node.capacity_gbps,
        }
        for node in nodes
    ]

@api.get("/network/connections")
def get_network_connections(request):
    """Get all network connections"""
    connections = NetworkConnection.objects.filter(is_active=True)
    return [
        {
            "id": str(conn.id),
            "name": conn.name,
            "type": conn.connection_type,
            "from_node": str(conn.from_node_id),
            "to_node": str(conn.to_node_id),
            "path": conn.geojson_path,
            "capacity_gbps": conn.capacity_gbps,
            "length_km": conn.length_km,
        }
        for conn in connections
    ]

@api.get("/equipment")
def get_equipment(request, equipment_type: Optional[str] = None):
    """Get equipment list with optional filtering"""
    queryset = Equipment.objects.all()
    if equipment_type:
        queryset = queryset.filter(equipment_type=equipment_type)
    
    return [
        {
            "id": str(eq.id),
            "name": eq.name,
            "type": eq.equipment_type,
            "manufacturer": eq.manufacturer,
            "model": eq.model,
            "image_url": eq.image.url if eq.image else None,
            "throughput_gbps": eq.throughput_gbps,
            "specifications": eq.specifications,
        }
        for eq in queryset
    ]

@api.post("/proposals/submit", auth=SolanaAuth())
def submit_proposal(request, data: ProposalSchema):
    """Submit a new proposal"""
    user = request.auth
    
    # Verify transaction
    solana_client = SolanaClient()
    tx_valid = solana_client.verify_transaction(
        data.solana_tx_signature,
        user.wallet_address
    )
    
    if not tx_valid:
        return {"success": False, "error": _("Invalid transaction")}
    
    # Check if proposal already exists with this transaction
    if UserProposal.objects.filter(solana_tx_signature=data.solana_tx_signature).exists():
        return {"success": False, "error": _("Proposal with this transaction already exists")}
    
    # Create proposal
    proposal = UserProposal.objects.create(
        user=user,
        title=data.title,
        description=data.description,
        proposal_type=data.proposal_type,
        target_node_id=data.target_node if data.target_node else None,
        proposed_equipment_id=data.proposed_equipment if data.proposed_equipment else None,
        quantity=data.quantity,
        justification=data.justification,
        solana_tx_signature=data.solana_tx_signature,
        status="pending"
    )
    
    return {
        "success": True,
        "proposal_id": str(proposal.id),
        "message": _("Proposal submitted successfully")
    }

@api.get("/proposals")
def get_proposals(request, status: Optional[str] = None, user_wallet: Optional[str] = None):
    """Get proposals with optional filtering"""
    queryset = UserProposal.objects.all().order_by('-created_at')
    
    if status:
        queryset = queryset.filter(status=status)
    
    if user_wallet:
        queryset = queryset.filter(user__wallet_address=user_wallet)
    
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "type": p.proposal_type,
            "user": p.user.nickname,
            "user_wallet": p.user.wallet_address,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
            "solana_tx": p.solana_tx_signature,
            "solana_tx_url": f"https://solscan.io/tx/{p.solana_tx_signature}",
        }
        for p in queryset
    ]

@api.post("/comments", auth=SolanaAuth())
def add_comment(request, data: CommentSchema):
    """Add a new comment"""
    user = request.auth
    
    comment = Comment.objects.create(
        user=user,
        content=data.content,
        parent_comment_id=data.parent_comment if data.parent_comment else None
    )
    
    return {
        "success": True,
        "comment_id": str(comment.id),
        "created_at": comment.created_at.isoformat()
    }

@api.get("/news")
def get_news(request, source: Optional[str] = None, limit: int = 20):
    """Get news articles"""
    queryset = NewsArticle.objects.all().order_by('-published_date')
    
    if source:
        queryset = queryset.filter(source=source)
    
    queryset = queryset[:limit]
    
    return [
        {
            "id": str(article.id),
            "title": article.title,
            "excerpt": article.excerpt,
            "source": article.source,
            "author": article.author,
            "published_date": article.published_date.isoformat(),
            "source_url": article.source_url,
            "tags": article.tags,
        }
        for article in queryset
    ]

@api.get("/stats")
def get_stats(request):
    """Get website statistics"""
    return {
        "total_nodes": NetworkNode.objects.count(),
        "total_equipment": Equipment.objects.count(),
        "total_connections": NetworkConnection.objects.count(),
        "total_proposals": UserProposal.objects.count(),
        "total_users": User.objects.count(),
        "total_comments": Comment.objects.count(),
        "total_news": NewsArticle.objects.count(),
    }