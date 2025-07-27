"""
Database operations for FSRS memory cards.

This module provides the CardOperations class to handle database operations
for spaced repetition cards, including creation, updates, and retrieval.
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from fsrs import Scheduler, Card
from weaviate.classes.query import Filter

# Get logger for this module
logger = logging.getLogger(__name__)


class CardOperations:
    """
    Handles database operations for FSRS memory cards.
    
    This class encapsulates all Weaviate operations specific to memory cards,
    including card creation, review updates, and study session retrieval.
    """
    
    def __init__(self, cards_collection):
        """
        Initialize card operations with a Weaviate cards collection.
        
        Args:
            cards_collection: Weaviate cards collection instance
        """
        self.cards_collection = cards_collection
        self.fsrs_scheduler = Scheduler()  # Using default parameters for now
    
    def _get_date_cutoff(self, date_filter: str) -> datetime:
        """
        Get the datetime cutoff for filtering cards based on date filter.
        
        Args:
            date_filter: "overdue", "today", "this_week", "all"
            
        Returns:
            UTC datetime for comparison, or None for "all"
        """
        now = datetime.now(timezone.utc)
        
        if date_filter == "overdue":
            # Past due (due < today, not including today)
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "today":
            # Due today or earlier (due <= end of today)
            return now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif date_filter == "this_week":
            # Due within 7 days (due <= now + 7 days)
            return now + timedelta(days=7)
        elif date_filter == "all":
            # No date restriction
            return None
        else:
            raise ValueError(f"Invalid date_filter: {date_filter}")
    
    def _group_by_subjects(self, due_cards):
        """
        Group cards by subject only - flat grouping.
        
        Args:
            due_cards: List of card objects from Weaviate query
            
        Returns:
            Dictionary with "groups" key containing subject counts
        """
        grouped = {}
        for card in due_cards:
            subject = card.properties["parent_note_subject"]
            grouped[subject] = grouped.get(subject, 0) + 1
        return {"groups": grouped}
    
    def _group_by_subject_notes(self, due_cards):
        """
        Group cards hierarchically by subject -> notes.
        
        Args:
            due_cards: List of card objects from Weaviate query
            
        Returns:
            Dictionary with "subjects" key containing hierarchical structure
        """
        subjects = {}
        for card in due_cards:
            subject = card.properties["parent_note_subject"]
            note = card.properties["parent_note_title"]
            
            if subject not in subjects:
                subjects[subject] = {}
            subjects[subject][note] = subjects[subject].get(note, 0) + 1
        
        return {"subjects": subjects}
    
    def _group_by_tag_subjects(self, due_cards, tags):
        """
        Group cards hierarchically by tag -> subject -> notes.
        
        Args:
            due_cards: List of card objects from Weaviate query
            tags: List of tags that were filtered for
            
        Returns:
            Dictionary with "filtered_tags" and "tag_groups" keys
        """
        tag_groups = {}
        for card in due_cards:
            card_tags = card.properties.get("parent_note_tags", [])
            subject = card.properties["parent_note_subject"] 
            note = card.properties["parent_note_title"]
            
            # Card appears in groups for each of its tags that match the filter
            for tag in card_tags:
                if tag in tags:  # Only include tags that were filtered for
                    if tag not in tag_groups:
                        tag_groups[tag] = {}
                    if subject not in tag_groups[tag]:
                        tag_groups[tag][subject] = {}
                    tag_groups[tag][subject][note] = tag_groups[tag][subject].get(note, 0) + 1
        
        return {"filtered_tags": tags, "tag_groups": tag_groups}
    
    def _build_cards_filters(self, subject=None, tags=None, deck_title=None, date_filter="today"):
        """
        Build Weaviate filters for cards queries.
        
        Args:
            subject: Filter by specific subject
            tags: Filter by tags - must contain ALL specified tags (AND logic)
            deck_title: Filter by specific note/deck title
            date_filter: "overdue", "today", "this_week", "all"
            
        Returns:
            List of Filter objects ready for Filter.all_of()
        """
        # Start with base filters
        filters = [
            Filter.by_property("deck_archived").equal(False)
        ]
        
        # Add date filter if not "all"
        date_cutoff = self._get_date_cutoff(date_filter)
        if date_cutoff is not None:
            if date_filter == "overdue":
                filters.append(Filter.by_property("due_date").less_than(date_cutoff))
            else:
                filters.append(Filter.by_property("due_date").less_or_equal(date_cutoff))
        
        # Add subject filter if provided
        if subject:
            filters.append(Filter.by_property("parent_note_subject").equal(subject))
        
        # Add tags filter if provided (intersection - must contain ALL tags)
        if tags:
            for tag in tags:
                filters.append(Filter.by_property("parent_note_tags").contains_any([tag]))
        
        # Add deck_title filter if provided
        if deck_title:
            filters.append(Filter.by_property("parent_note_title").equal(deck_title))
        
        return filters
    
    def _sort_and_randomize_cards(self, cards, limit=50):
        """
        Sort cards by due date and randomize within same day, then apply limit.
        
        Args:
            cards: List of card objects from Weaviate query
            limit: Maximum number of cards to return
            
        Returns:
            List of cards sorted by due date, randomized within each day, limited
        """
        import random
        from collections import defaultdict
        
        # Group cards by their due date (just the date part, not time)
        cards_by_date = defaultdict(list)
        
        for card in cards:
            due_date = card.properties.get("due_date")
            if due_date:
                due_date_only = due_date.date()  # Extract just date part
                cards_by_date[due_date_only].append(card)
            else:
                # Handle cards without due_date (shouldn't happen but be safe)
                cards_by_date[datetime.now(timezone.utc).date()].append(card)
        
        # Randomize within each day, then combine in date order
        randomized_cards = []
        for date in sorted(cards_by_date.keys()):  # Keep dates in chronological order
            cards_on_this_date = cards_by_date[date]
            random.shuffle(cards_on_this_date)  # Randomize within the day
            randomized_cards.extend(cards_on_this_date)  # Add all to final list
        
        # Apply limit
        return randomized_cards[:limit]
    
    def _parse_recall_prompts(self, content: str) -> list[str]:
        """
        Extract recall prompts from markdown content.
        
        Args:
            content: Full markdown content of the note
            
        Returns:
            List of prompt text strings (bullet markers removed, empty prompts filtered)
        """
        logger.info("Parsing recall prompts from note content")
        
        lines = content.split('\n')
        prompts = []
        in_recall_section = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # Check if we're entering the recall prompts section
            if stripped_line.lower() == "### recall prompts":
                in_recall_section = True
                continue
            
            # Check if we've hit another section (1-3 hashtags or ---)
            if in_recall_section and (stripped_line.startswith('---') or 
                                    stripped_line.startswith('#') and 
                                    len(stripped_line.split()[0]) <= 3):
                break
            
            # Process bullet points in the recall section
            if in_recall_section and stripped_line:
                # Remove bullet markers (-, *, +) and clean whitespace
                if stripped_line.startswith(('-', '*', '+')):
                    prompt_text = stripped_line[1:].strip()
                    if prompt_text:  # Filter out empty prompts
                        prompts.append(prompt_text)
        
        logger.info(f"Found {len(prompts)} recall prompts")
        return prompts
    
    def create_cards_from_note(self, note_object) -> bool:
        """
        Create recall cards from a note object and insert into Weaviate.
        
        Args:
            note_object: Weaviate note object with properties (title, subject, content, tags, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            note_title = note_object.properties["title"]
            logger.info(f"Creating cards from note: {note_title}")
            
            # Parse recall prompts from note content
            recall_prompts = self._parse_recall_prompts(note_object.properties["content"])
            
            if not recall_prompts:
                logger.info(f"No recall prompts found in note: {note_title}")
                return True
            
            # Create and insert cards for each recall prompt
            cards_created = 0
            for prompt_text in recall_prompts:
                try:
                    # Create new FSRS card
                    fsrs_card = Card()
                    
                    # Build card properties matching cards_collection schema
                    card_properties = {
                        "parent_note_uuid": str(note_object.uuid),
                        "parent_note_title": note_object.properties["title"],
                        "parent_note_subject": note_object.properties["subject"],
                        "parent_note_tags": note_object.properties["tags"],
                        "prompt_text": prompt_text,
                        "fsrs_card_json": json.dumps(fsrs_card.to_dict()),
                        "due_date": fsrs_card.due,
                        "review_history": [],
                        "deck_archived": False
                    }
                    
                    # Insert card into Weaviate
                    self.cards_collection.data.insert(card_properties)
                    cards_created += 1
                    
                except Exception as e:
                    logger.error(f"Error creating card for prompt '{prompt_text[:50]}...': {e}")
                    continue
            
            logger.info(f"Successfully created {cards_created} cards from note: {note_title}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating cards from note: {e}")
            return False
    
    def update_card(self, card_uuid: str, rating: int, review_time: float) -> bool:
        """
        Update a card after review with FSRS scheduling.
        
        Args:
            card_uuid: UUID of the card to update
            rating: User rating (1-4: Again, Hard, Good, Easy)
            review_time: Time taken for review in seconds
            
        Returns:
            True if successful, False otherwise
        """
        # TODO: Implement card update logic with FSRS
        logger.info(f"Updating card {card_uuid} with rating {rating}")
        # Note: review_time parameter will be used in future implementation
        return True
    
    def get_cards_overview(self, subject=None, tags=None, date_filter="today", view="subject_notes"):
        """
        Get overview of cards due for study with flexible grouping.
        
        Args:
            subject: Filter by specific subject (e.g. "Mathematics")
            tags: Filter by tags - must contain ALL specified tags (AND logic)
            date_filter: "overdue", "today", "this_week", "all" 
            view: "subjects", "subject_notes", "tag_subjects"
            
        Returns:
            Dictionary with grouped counts for study planning
        """
        logger.info(f"Getting cards overview with filters: subject={subject}, tags={tags}, date_filter={date_filter}, view={view}")
        
        # Input validation
        if view == "tag_subjects" and not tags:
            raise ValueError("'tag_subjects' view requires tags parameter")
        
        # Build filters using helper method
        filters = self._build_cards_filters(subject, tags, None, date_filter)
        
        try:
            # Query only due cards with all filters applied at database level
            response = self.cards_collection.query.fetch_objects(
                where=Filter.all_of(filters),
                limit=10000  # Large limit to get all matching cards
            )
            
            due_cards = response.objects
            logger.info(f"Found {len(due_cards)} cards matching filters")
            
            # Prepare base result structure
            base_result = {
                "total_due_cards": len(due_cards),
                "view": view,
                "filters_applied": {
                    "subject": subject,
                    "tags": tags,
                    "date_filter": date_filter
                }
            }
            
            # Call appropriate view helper
            if view == "subjects":
                view_data = self._group_by_subjects(due_cards)
            elif view == "subject_notes":
                view_data = self._group_by_subject_notes(due_cards)
            elif view == "tag_subjects":
                view_data = self._group_by_tag_subjects(due_cards, tags)
            else:
                raise ValueError(f"Invalid view: {view}")
            
            # Merge results
            return {**base_result, **view_data}
            
        except Exception as e:
            logger.error(f"Error getting cards overview: {e}")
            raise e
    
    def get_cards(self, subject=None, tags=None, deck_title=None, date_filter="today"):
        """
        Get actual cards for study session with LLM coaching data.
        
        Args:
            subject: Filter by specific subject
            tags: Filter by tags - must contain ALL specified tags (AND logic)  
            deck_title: Filter by specific note/deck title
            date_filter: "overdue", "today", "this_week", "all"
            
        Returns:
            Dictionary with up to 50 cards with full details for study session
        """
        logger.info(f"Getting study cards with filters: subject={subject}, tags={tags}, deck_title={deck_title}, date_filter={date_filter}")
        
        # Build filters using helper method
        filters = self._build_cards_filters(subject, tags, deck_title, date_filter)
        
        try:
            # Query cards with all filters applied at database level
            response = self.cards_collection.query.fetch_objects(
                where=Filter.all_of(filters),
                limit=10000  # Large limit to get all matching cards before sorting/limiting
            )
            
            query_results = response.objects
            logger.info(f"Found {len(query_results)} cards matching filters before limit")
            
            # Handle empty results
            if not query_results:
                return {
                    "total_cards": 0,
                    "filters_applied": {
                        "subject": subject,
                        "tags": tags,
                        "deck_title": deck_title,
                        "date_filter": date_filter
                    },
                    "cards": []
                }
            
            # Apply sorting and limit
            CARD_LIMIT = 50
            limited_cards = self._sort_and_randomize_cards(query_results, CARD_LIMIT)
            
            # Build detailed card information for LLM coaching
            cards_data = []
            for obj in limited_cards:
                try:
                    # Reconstruct FSRS Card object for detailed information
                    fsrs_card_json = obj.properties.get("fsrs_card_json")
                    if not fsrs_card_json:
                        logger.warning(f"Card {obj.uuid} missing fsrs_card_json, skipping")
                        continue
                    
                    # Parse JSON and reconstruct FSRS card
                    import json
                    from fsrs import Card
                    fsrs_data = json.loads(fsrs_card_json)
                    fsrs_card = Card.from_dict(fsrs_data)
                    
                    # Calculate retrievability for LLM coaching
                    retrievability = self.fsrs_scheduler.get_card_retrievability(fsrs_card)
                    
                    # Get native object array from Weaviate
                    review_history = obj.properties.get("review_history", [])
                    review_count = len(review_history)
                    
                    # Build card information useful for study sessions
                    card_info = {
                        # Essential identification
                        "card_uuid": str(obj.uuid),
                        "prompt_text": obj.properties["prompt_text"],
                        
                        # FSRS algorithm data
                        "fsrs_card_id": fsrs_card.card_id,
                        "fsrs_state": fsrs_card.state.name,
                        "fsrs_difficulty": round(fsrs_card.difficulty, 3) if fsrs_card.difficulty is not None else None,
                        "fsrs_stability": round(fsrs_card.stability, 3) if fsrs_card.stability is not None else None,
                        "fsrs_due_date": fsrs_card.due.isoformat(),
                        "fsrs_last_review": fsrs_card.last_review.isoformat() if fsrs_card.last_review else None,
                        "fsrs_retrievability": round(retrievability, 3),
                        
                        # Review analytics
                        "review_count": review_count,
                        "review_history": review_history,  # Native object array from Weaviate
                        
                        # Source note context
                        "note_title": obj.properties["parent_note_title"],
                        "note_subject": obj.properties["parent_note_subject"],
                        "note_tags": obj.properties.get("parent_note_tags", [])
                    }
                    
                    cards_data.append(card_info)
                    
                except (KeyError, ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Invalid FSRS data for card {obj.uuid}: {e}")
                    # Skip this card and continue with others
                    continue
            
            return {
                "total_cards": len(cards_data),
                "filters_applied": {
                    "subject": subject,
                    "tags": tags,
                    "deck_title": deck_title,
                    "date_filter": date_filter
                },
                "cards": cards_data
            }
            
        except Exception as e:
            logger.error(f"Error getting study cards: {e}")
            raise e