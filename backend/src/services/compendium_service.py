"""
Compendium Service - D&D Beyond Style Encyclopedia
Provides search, filtering, and retrieval of D&D content
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import json

from backend.src.logging import get_logger
from backend.src.models.compendium import (
    CompendiumCategory,
    CompendiumEntry,
    CompendiumRating,
    CompendiumComment,
    UserHomebrew
)

logger = get_logger('compendium')


class CompendiumService:
    """Service for managing compendium data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Category Operations
    
    def get_all_categories(self, include_entries: bool = False) -> List[Dict[str, Any]]:
        """Get all compendium categories"""
        categories = self.db.query(CompendiumCategory).filter(
            CompendiumCategory.parent_id.is_(None)
        ).all()
        
        result = []
        for cat in categories:
            cat_data = {
                'id': cat.id,
                'name': cat.name,
                'description': cat.description,
                'icon': cat.icon,
                'entry_count': len(cat.entries) if include_entries else None
            }
            
            if include_entries:
                cat_data['entries'] = [
                    {
                        'id': entry.id,
                        'name': entry.name,
                        'type': entry.type
                    }
                    for entry in cat.entries
                ]
            
            result.append(cat_data)
        
        logger.info(
            "Retrieved categories",
            extra={'count': len(result), 'include_entries': include_entries}
        )
        
        return result
    
    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID with subcategories"""
        category = self.db.query(CompendiumCategory).filter(
            CompendiumCategory.id == category_id
        ).first()
        
        if not category:
            return None
        
        return {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'icon': category.icon,
            'subcategories': [
                {
                    'id': sub.id,
                    'name': sub.name,
                    'description': sub.description
                }
                for sub in category.subcategories
            ],
            'entries': [
                {
                    'id': entry.id,
                    'name': entry.name,
                    'type': entry.type
                }
                for entry in category.entries
            ]
        }
    
    # Entry Operations
    
    def search_entries(
        self,
        query: str,
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search compendium entries
        
        Args:
            query: Search query string
            category: Filter by category name
            entry_type: Filter by type (spell, item, monster, etc.)
            limit: Maximum results to return
            offset: Offset for pagination
        
        Returns:
            Dictionary with results and metadata
        """
        logger.info(
            "Searching compendium",
            extra={
                'query': query,
                'category': category,
                'entry_type': entry_type,
                'limit': limit
            }
        )
        
        # Build query
        db_query = self.db.query(CompendiumEntry).filter(
            CompendiumEntry.is_public == True
        )
        
        # Search in name, description, and tags
        search_filter = or_(
            CompendiumEntry.name.ilike(f"%{query}%"),
            CompendiumEntry.description.ilike(f"%{query}%"),
            CompendiumEntry.search_tags.ilike(f"%{query}%")
        )
        db_query = db_query.filter(search_filter)
        
        # Apply filters
        if category:
            db_query = db_query.join(CompendiumCategory).filter(
                CompendiumCategory.name == category
            )
        
        if entry_type:
            db_query = db_query.filter(CompendiumEntry.type == entry_type)
        
        # Get total count
        total = db_query.count()
        
        # Execute query with pagination
        entries = db_query.offset(offset).limit(limit).all()
        
        results = [
            {
                'id': entry.id,
                'name': entry.name,
                'type': entry.type,
                'description': entry.description[:200] + '...' if len(entry.description) > 200 else entry.description,
                'properties': entry.properties,
                'source': entry.source
            }
            for entry in entries
        ]
        
        logger.info(
            "Search complete",
            extra={
                'results_count': len(results),
                'total_count': total
            }
        )
        
        return {
            'results': results,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total
        }
    
    def get_entry_by_id(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get full entry details by ID"""
        entry = self.db.query(CompendiumEntry).filter(
            CompendiumEntry.id == entry_id
        ).first()
        
        if not entry:
            return None
        
        # Calculate average rating
        ratings = entry.ratings
        avg_rating = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
        
        return {
            'id': entry.id,
            'name': entry.name,
            'type': entry.type,
            'description': entry.description,
            'content': entry.content,
            'properties': entry.properties,
            'category': {
                'id': entry.category.id,
                'name': entry.category.name
            },
            'source': entry.source,
            'page': entry.page,
            'search_tags': entry.search_tags,
            'rating': {
                'average': round(avg_rating, 2),
                'count': len(ratings)
            },
            'is_homebrew': entry.is_homebrew
        }
    
    def get_entries_by_type(
        self,
        entry_type: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get entries by type (e.g., all spells, all items)"""
        entries = self.db.query(CompendiumEntry).filter(
            and_(
                CompendiumEntry.type == entry_type,
                CompendiumEntry.is_public == True
            )
        ).offset(offset).limit(limit).all()
        
        return [
            {
                'id': entry.id,
                'name': entry.name,
                'type': entry.type,
                'description': entry.description[:200],
                'properties': entry.properties
            }
            for entry in entries
        ]
    
    # Rating Operations
    
    def add_rating(self, entry_id: int, user_id: int, rating: int, comment: str = "") -> Dict[str, Any]:
        """Add or update rating for an entry"""
        from datetime import datetime
        
        # Check if user already rated
        existing = self.db.query(CompendiumRating).filter(
            and_(
                CompendiumRating.entry_id == entry_id,
                CompendiumRating.user_id == user_id
            )
        ).first()
        
        if existing:
            existing.rating = rating
            existing.comment = comment
            existing.updated_at = datetime.utcnow().isoformat()
        else:
            new_rating = CompendiumRating(
                entry_id=entry_id,
                user_id=user_id,
                rating=rating,
                comment=comment,
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(new_rating)
        
        self.db.commit()
        
        logger.info(
            "Rating added",
            extra={
                'entry_id': entry_id,
                'user_id': user_id,
                'rating': rating
            }
        )
        
        return {'success': True, 'rating': rating}
    
    # Comment Operations
    
    def add_comment(self, entry_id: int, user_id: int, content: str, parent_id: Optional[int] = None) -> Dict[str, Any]:
        """Add comment to an entry"""
        from datetime import datetime
        
        comment = CompendiumComment(
            entry_id=entry_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        self.db.add(comment)
        self.db.commit()
        
        logger.info(
            "Comment added",
            extra={
                'entry_id': entry_id,
                'user_id': user_id,
                'parent_id': parent_id
            }
        )
        
        return {'success': True, 'comment_id': comment.id}
    
    # Homebrew Operations
    
    def create_homebrew(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new homebrew content"""
        homebrew = UserHomebrew(
            user_id=user_id,
            name=data['name'],
            type=data['type'],
            description=data.get('description', ''),
            content=data.get('content', ''),
            metadata=data.get('metadata', {}),
            is_public=data.get('is_public', False),
            version=data.get('version', '1.0.0')
        )
        
        self.db.add(homebrew)
        self.db.commit()
        self.db.refresh(homebrew)
        
        logger.info(
            "Homebrew created",
            extra={
                'user_id': user_id,
                'name': homebrew.name,
                'type': homebrew.type
            }
        )
        
        return {
            'id': homebrew.id,
            'name': homebrew.name,
            'type': homebrew.type
        }
    
    def get_user_homebrew(self, user_id: int, include_public: bool = True) -> List[Dict[str, Any]]:
        """Get user's homebrew content"""
        query = self.db.query(UserHomebrew).filter(
            UserHomebrew.user_id == user_id
        )
        
        if not include_public:
            query = query.filter(UserHomebrew.is_public == False)
        
        homebrew_list = query.all()
        
        return [
            {
                'id': hb.id,
                'name': hb.name,
                'type': hb.type,
                'description': hb.description,
                'is_public': hb.is_public,
                'views': hb.views,
                'likes': hb.likes,
                'version': hb.version
            }
            for hb in homebrew_list
        ]


# Predefined category structure for D&D 5e
DEFAULT_CATEGORIES = [
    {
        'name': 'Spells',
        'icon': '✨',
        'description': 'Magical spells and incantations',
        'subcategories': [
            {'name': 'Cantrips', 'description': 'Level 0 spells'},
            {'name': '1st Level', 'description': '1st level spells'},
            {'name': '2nd Level', 'description': '2nd level spells'},
            # ... more levels
        ]
    },
    {
        'name': 'Items',
        'icon': '🎒',
        'description': 'Equipment, weapons, armor, and magical items',
        'subcategories': [
            {'name': 'Weapons', 'description': 'Melee and ranged weapons'},
            {'name': 'Armor', 'description': 'Light, medium, and heavy armor'},
            {'name': 'Magic Items', 'description': 'Magical equipment'},
        ]
    },
    {
        'name': 'Monsters',
        'icon': '🐉',
        'description': 'Creatures and NPCs',
        'subcategories': [
            {'name': 'Aberrations', 'description': 'Alien creatures'},
            {'name': 'Beasts', 'description': 'Natural animals'},
            {'name': 'Dragons', 'description': 'True dragons'},
            # ... more types
        ]
    },
    {
        'name': 'Rules',
        'icon': '📖',
        'description': 'Game rules and mechanics',
        'subcategories': [
            {'name': 'Combat', 'description': 'Combat rules'},
            {'name': 'Skills', 'description': 'Skill checks and abilities'},
            {'name': 'Feats', 'description': 'Character feats'},
        ]
    },
    {
        'name': 'Backgrounds',
        'icon': '📜',
        'description': 'Character backgrounds',
        'subcategories': []
    },
    {
        'name': 'Races',
        'icon': '🧝',
        'description': 'Playable races and lineages',
        'subcategories': []
    },
    {
        'name': 'Classes',
        'icon': '⚔️',
        'description': 'Character classes and subclasses',
        'subcategories': []
    }
]
