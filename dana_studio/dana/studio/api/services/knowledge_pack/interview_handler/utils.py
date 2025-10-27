"""
Utility functions for interview handler.
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def parse_interview_note(note_path: str) -> dict:
    """
    Parse interview_notes.md and extract topic progress.
    
    Returns: {
        "topics": [
            {
                "topic_name": "...",
                "status": "in_progress",
                "completeness": 25,
                "insights_count": 3,
                "questions": [...]
            }
        ],
        "overall_completeness": 40,
        "current_topic": "Safety Procedures"
    }
    """
    try:
        # Read note file
        note_path_obj = Path(note_path)
        if not note_path_obj.exists():
            return {
                "topics": [],
                "overall_completeness": 0,
                "current_topic": None
            }
        
        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        topics = []
        current_topic = None
        
        # Find all topic sections (### Topic Name)
        # Capture only the header line, not the entire section
        topic_pattern = r'### ([^\n]+)'  # Match everything except newline
        topic_matches = list(re.finditer(topic_pattern, content))
        
        for i, match in enumerate(topic_matches):
            topic_name = match.group(1).strip()
            
            # Find the full section content (from this ### to the next ### or end)
            start_pos = match.start()
            # Find next topic header or end of file
            if i + 1 < len(topic_matches):
                end_pos = topic_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            topic_section = content[start_pos:end_pos]
            
            # Extract status
            status_match = re.search(r'\*\*Status\*\*:\s*(.+?)(?:\n|$)', topic_section)
            status = "not_started"
            if status_match:
                status_text = status_match.group(1).strip().lower()
                if "completed" in status_text:
                    status = "completed"
                elif "in progress" in status_text or "in-progress" in status_text:
                    status = "in_progress"
                    # Always update to the LAST in-progress topic (most recent)
                    current_topic = topic_name
                elif "not started" in status_text:
                    status = "not_started"
            
            # Count insights (bullet points under **Expert Insights**)
            insights_count = 0
            # Try multiple patterns to handle different formatting variations
            
            # Pattern 1: Standard bullet points (- or *)
            insights_section_match = re.search(r'\*\*Expert Insights\*\*\s*\n((?:^[-*•]\s.+$\n?)+)', topic_section, re.MULTILINE)
            
            # Pattern 2: Handle extra spacing or colons
            if not insights_section_match:
                insights_section_match = re.search(r'\*\*Expert Insights\*\*[:\s]*\n+((?:^[-*•]\s.+$\n?)+)', topic_section, re.MULTILINE)
            
            # Pattern 3: Handle numbered lists
            if not insights_section_match:
                insights_section_match = re.search(r'\*\*Expert Insights\*\*[:\s]*\n+((?:^\d+\.\s.+$\n?)+)', topic_section, re.MULTILINE)
            
            if insights_section_match:
                insights_text = insights_section_match.group(1)
                # Count bullet points (supporting -, *, •) and numbered lists
                bullet_count = len(re.findall(r'^[-*•]\s', insights_text, re.MULTILINE))
                numbered_count = len(re.findall(r'^\d+\.\s', insights_text, re.MULTILINE))
                insights_count = max(bullet_count, numbered_count)
                logger.debug(f"Found {insights_count} insights for topic '{topic_name}'")
            
            # Calculate completeness from status (no longer parse from notes)
            if status == "completed":
                completeness = 100
            elif status == "in_progress":
                # Estimate from insights: ~15% per insight, cap at 90%
                completeness = min(90, insights_count * 15) if insights_count > 0 else 10
            else:  # not_started
                completeness = 0
            
            logger.debug(f"Topic '{topic_name}': status={status}, insights={insights_count}, completeness={completeness}%")
            
            # Extract questions
            questions = []
            questions_match = re.search(r'\*\*Key Questions\*\*:\s*(.+?)(?=\n\*\*|\Z)', topic_section, re.DOTALL)
            if questions_match:
                questions_text = questions_match.group(1).strip()
                
                # Try multiple formats for extracting questions
                # Format 1: Numbered list (1. Question text)
                question_items = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\Z)', questions_text, re.DOTALL)
                if question_items:
                    questions = [q.strip() for q in question_items if q.strip()]
                else:
                    # Format 2: Bullet points (- Question text or * Question text)
                    question_items = re.findall(r'^[-*]\s*(.+?)$', questions_text, re.MULTILINE)
                    if question_items:
                        questions = [q.strip() for q in question_items if q.strip()]
                    else:
                        # Format 3: Simple line breaks (one question per line)
                        lines = questions_text.split('\n')
                        questions = [line.strip() for line in lines if line.strip() and not line.strip().startswith('**')]
            
            topics.append({
                "topic_name": topic_name,
                "status": status,
                "completeness": completeness,
                "insights_count": insights_count,
                "questions": questions
            })
        
        # Calculate overall completeness
        if topics:
            total_completeness = sum(t["completeness"] for t in topics)
            overall_completeness = total_completeness // len(topics)
        else:
            overall_completeness = 0
        
        return {
            "topics": topics,
            "overall_completeness": overall_completeness,
            "current_topic": current_topic
        }
    
    except Exception as e:
        # Return empty structure on error
        return {
            "topics": [],
            "overall_completeness": 0,
            "current_topic": None,
            "error": str(e)
        }


def similarity_ratio(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def extract_question_from_agent_message(content: str) -> str:
    """
    Extract the actual question from HTML-formatted agent messages.
    
    Agent messages contain:
    - Acknowledgment in <p> tags
    - Question in <p><strong>question</strong></p> tags
    
    Returns the clean question text without HTML tags.
    """
    if not content:
        return ""
    
    # First priority: Look for <strong> tags (most likely the main question)
    strong_match = re.search(r'<strong>(.*?)</strong>', content)
    if strong_match:
        question_text = strong_match.group(1).strip()
        if question_text.endswith('?'):
            return question_text
    
    # Second priority: Remove HTML tags and find lines ending with ?
    clean_content = re.sub(r'<[^>]+>', '', content)
    lines = clean_content.split('\n')
    questions = [line.strip() for line in lines if line.strip().endswith('?')]
    
    if questions:
        # Return the last question found (most likely the main question)
        return questions[-1]
    
    # If still no question found, return empty string
    return ""


def analyze_question_status(
    template_questions: list[str],
    conversation_messages: list,
    current_topic_name: str | None = None
) -> list[dict]:
    """
    Analyze conversation to determine status of each question.
    
    Returns list of questions with status indicators:
    - "not_asked": Question hasn't been asked yet
    - "being_asked": Question is currently being asked (last agent question)
    - "answered": Question was asked and user responded
    - "skipped": Question wasn't asked but topic moved on
    
    Args:
        template_questions: List of question strings from template
        conversation_messages: List of conversation message dicts with 'role' and 'content'
        current_topic_name: Name of current topic (if in progress)
    
    Returns:
        List of dicts with question_text, status, and asked_at
    """
    if not template_questions:
        return []
    
    question_statuses = []
    
    # Extract agent questions from conversation
    agent_questions = []
    for msg in conversation_messages:
        if msg.get('role') in ['agent', 'assistant'] or msg.get('sender') == 'agent':
            content = msg.get('content', '')
            # Extract questions (lines ending with ?)
            questions_in_msg = [q.strip() for q in content.split('\n') if q.strip().endswith('?')]
            for q in questions_in_msg:
                agent_questions.append({
                    'question': q,
                    'timestamp': msg.get('created_at') or msg.get('timestamp'),
                    'full_content': content
                })
    
    # Match template questions to agent questions
    for template_q in template_questions:
        best_match = None
        best_similarity = 0.0
        
        # Find best matching agent question
        for agent_q in agent_questions:
            similarity = similarity_ratio(template_q, agent_q['question'])
            if similarity > best_similarity and similarity > 0.5:  # Threshold for matching
                best_similarity = similarity
                best_match = agent_q
        
        if best_match:
            # Check if there's a user response after this question
            agent_q_index = agent_questions.index(best_match)
            
            # Check if this is the last agent question
            is_last = (agent_q_index == len(agent_questions) - 1)
            
            # Check if user responded after this question
            has_user_response = False
            if not is_last:
                # There are more agent questions after, so this one was answered
                has_user_response = True
            else:
                # Check if last message in conversation is from user
                if conversation_messages:
                    last_msg = conversation_messages[-1]
                    if last_msg.get('role') == 'user' or last_msg.get('sender') == 'user':
                        has_user_response = True
            
            # Determine status
            if is_last and not has_user_response:
                status = "being_asked"
            elif has_user_response:
                status = "answered"
            else:
                status = "answered"  # Has response (another question came after)
            
            question_statuses.append({
                'question_text': template_q,
                'status': status,
                'asked_at': best_match['timestamp']
            })
        else:
            # Question not found in conversation
            question_statuses.append({
                'question_text': template_q,
                'status': 'not_asked',
                'asked_at': None
            })
    
    return question_statuses


def infer_current_topic_from_conversation(
    topics: list[dict],
    conversation_messages: list
) -> str | None:
    """
    Infer which topic is currently active based on recent conversation.
    
    Logic:
    1. Find the most recent agent question
    2. Extract clean question text from HTML-formatted message
    3. Match it to topic questions
    4. Return that topic as current
    5. If no match, check for topic names mentioned in recent messages
    6. Fallback to topics with insights or in-progress status
    """
    if not topics or not conversation_messages:
        return None
    
    logger.debug(f"🔍 Starting current topic inference with {len(topics)} topics: {[t['topic_name'] for t in topics]}")
    logger.debug(f"🔍 Processing {len(conversation_messages)} conversation messages")
    
    # Get last few agent messages
    recent_agent_messages = [
        msg for msg in conversation_messages[-10:]
        if msg.get('role') in ['agent', 'assistant'] or msg.get('sender') == 'agent' or msg.get('sender') == 'assistant'
    ]
    
    if not recent_agent_messages:
        return None
    
    # Extract clean question from the most recent agent message
    last_agent_content = recent_agent_messages[-1].get('content', '')
    extracted_question = extract_question_from_agent_message(last_agent_content)
    
    logger.debug(f"🔍 Current topic inference - Found {len(recent_agent_messages)} recent agent messages")
    logger.debug(f"🔍 Last agent message content: {last_agent_content[:200]}...")
    logger.debug(f"🔍 Extracted question: '{extracted_question}'")
    
    # Try to match extracted question to topic questions
    if extracted_question:
        for topic in topics:
            for question in topic.get('questions', []):
                if isinstance(question, dict):
                    q_text = question.get('question_text', '')
                else:
                    q_text = str(question)
                
                # Clean template question text for better matching
                clean_template_q = q_text.strip().lower()
                clean_agent_q = extracted_question.strip().lower()
                
                # Multiple matching strategies
                # 1. Direct similarity match
                similarity = similarity_ratio(clean_template_q, clean_agent_q)
                logger.debug(f"🔍 Comparing '{clean_agent_q}' vs '{clean_template_q}' - similarity: {similarity:.3f}")
                
                if similarity > 0.3:
                    logger.debug(f"✅ Matched question to topic '{topic['topic_name']}': '{extracted_question}'")
                    return topic['topic_name']
                
                # 2. Check if agent question contains key words from template question
                template_words = set(clean_template_q.split())
                agent_words = set(clean_agent_q.split())
                common_words = template_words.intersection(agent_words)
                logger.debug(f"🔍 Common words between questions: {common_words}")
                
                if len(template_words) > 0 and len(common_words) >= 2:
                    logger.debug(f"✅ Matched by keywords to topic '{topic['topic_name']}': '{extracted_question}'")
                    return topic['topic_name']
    
    # Fallback 1: Check if any topic names are mentioned in recent agent messages
    logger.debug(f"🔍 Fallback 1: Checking for topic names in recent agent messages")
    for msg in recent_agent_messages[-3:]:  # Check last 3 agent messages
        content = msg.get('content', '').lower()
        logger.debug(f"🔍 Checking message content: {content[:100]}...")
        for topic in topics:
            topic_name_lower = topic['topic_name'].lower()
            # Check if topic name appears in the message content
            if topic_name_lower in content and topic['status'] != 'completed':
                logger.debug(f"✅ Found topic name '{topic['topic_name']}' mentioned in agent message")
                return topic['topic_name']
    
    # Fallback 2: Find topic with in_progress status (highest priority)
    logger.debug(f"🔍 Fallback 2: Looking for in_progress topics")
    for topic in topics:
        if topic['status'] == 'in_progress':
            logger.debug(f"✅ Found in_progress topic: '{topic['topic_name']}'")
            return topic['topic_name']
    
    # Fallback 3: Find topic with insights but not completed  
    logger.debug(f"🔍 Fallback 3: Looking for topics with insights")
    for topic in topics:
        if (topic['status'] != 'completed' and 
            topic['insights_count'] > 0):
            logger.debug(f"✅ Found topic with insights: '{topic['topic_name']}' ({topic['insights_count']} insights)")
            return topic['topic_name']
    
    # Fallback 4: First not-completed topic
    logger.debug(f"🔍 Fallback 4: Looking for first not-completed topic")
    for topic in topics:
        if topic['status'] != 'completed':
            logger.debug(f"✅ Found first not-completed topic: '{topic['topic_name']}'")
            return topic['topic_name']
    
    # All topics completed
    logger.debug(f"🔍 All topics are completed, returning None")
    return None

