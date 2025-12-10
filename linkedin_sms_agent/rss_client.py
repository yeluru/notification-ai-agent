"""RSS/Atom feed client for fetching feed items."""

import logging
from datetime import datetime
from typing import List
import feedparser

from .config import RSSConfig
from .models import RSSItem

logger = logging.getLogger(__name__)


def fetch_items(config: RSSConfig) -> List[RSSItem]:
    """
    Fetch items from configured RSS/Atom feeds.
    
    Args:
        config: RSS configuration.
        
    Returns:
        List of RSSItem objects.
    """
    if not config.enabled or not config.feeds:
        return []
    
    all_items = []
    
    for feed_url in config.feeds:
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            
            # Parse feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing error for {feed_url}: {feed.bozo_exception}")
                continue
            
            # Get feed title/name
            feed_title = feed.feed.get("title", feed_url)
            
            # Process entries
            for entry in feed.entries:
                try:
                    # Get unique ID
                    unique_id = entry.get("id") or entry.get("link", "")
                    if not unique_id:
                        continue
                    
                    # Get title
                    title = entry.get("title", "No title")
                    
                    # Get snippet from summary, description, or content
                    snippet = ""
                    if "summary" in entry:
                        snippet = entry.summary
                    elif "description" in entry:
                        snippet = entry.description
                    elif "content" in entry:
                        if isinstance(entry.content, list) and entry.content:
                            snippet = entry.content[0].get("value", "")
                        else:
                            snippet = str(entry.content)
                    
                    # Limit snippet length
                    snippet = snippet[:600].strip()
                    if len(snippet) > 600:
                        snippet = snippet[:600] + "..."
                    
                    # Parse published date
                    published_dt = None
                    if "published_parsed" in entry and entry.published_parsed:
                        # feedparser returns time_struct in UTC
                        published_dt = datetime(*entry.published_parsed[:6])
                    elif "updated_parsed" in entry and entry.updated_parsed:
                        published_dt = datetime(*entry.updated_parsed[:6])
                    
                    if not published_dt:
                        published_dt = datetime.utcnow()
                    else:
                        # Ensure it's treated as UTC
                        published_dt = published_dt.replace(tzinfo=None)
                        # If feedparser didn't provide timezone, assume UTC
                    
                    published_at = published_dt.isoformat() + "Z"
                    
                    all_items.append(RSSItem(
                        id=unique_id,
                        source=feed_title,
                        title=title,
                        snippet=snippet,
                        published_at=published_at,
                    ))
                    
                except Exception as e:
                    logger.debug(f"Error processing RSS entry: {e}")
                    continue
            
            logger.info(f"Extracted {len([e for e in feed.entries])} items from {feed_url}")
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            continue
    
    logger.info(f"Total RSS items extracted: {len(all_items)}")
    return all_items

