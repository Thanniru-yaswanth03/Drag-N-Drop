import json
import logging
import re
import httpx
import config

logger = logging.getLogger("ai_service")


async def test_ai_connection():
    if not config.OPENROUTER_API_KEY or "example-key" in config.OPENROUTER_API_KEY:
        return {
            "status": "mock",
            "message": "OpenRouter API Key not configured in .env. Test mock response: 2+2=4.",
        }

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Project Management MVP",
    }

    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": "What is 2+2? Reply with just the number 4."}
        ],
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                config.OPENROUTER_URL, headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()
            reply_text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return {
                "status": "success",
                "model": config.OPENROUTER_MODEL,
                "response": reply_text,
            }
        except Exception as e:
            logger.error(f"OpenRouter test error: {str(e)}")
            return {
                "status": "error",
                "message": f"OpenRouter API error: {str(e)}",
            }


SYSTEM_PROMPT = """You are an intelligent AI Project Management Assistant for Kanban Studio.
You assist users by answering questions and helping them manage their Kanban board.

You will receive the user's message and the current JSON state of their Kanban board.

Respond ONLY with a valid JSON object matching this schema:
{
  "reply": "Your friendly and helpful text message response to the user.",
  "board_update": null OR {
    "columns": [ ... updated list of columns with cardIds ... ],
    "cards": { ... updated card dictionary mapping cardId to {id, title, details, description, priority, dueDate, tags, assignee} ... }
  }
}

Rules for board updates:
1. Creating cards: If the user asks to add/create a card (e.g. 'Add QA Testing to In Progress'), add a new card entry to 'cards' and append its ID to the target column's 'cardIds'.
2. Moving cards: If the user asks to move a card (e.g. 'Move card-1 to Done' or 'shift roadmap to Review'), remove its ID from the source column 'cardIds' and append it to the target column 'cardIds'.
3. Deleting/Clearing cards: If the user asks to clear or delete a card or clear a column (e.g. 'clear card from progress' or 'delete card-2'), remove the card ID from 'cardIds' and delete it from 'cards'.
4. Column Renaming: If the user asks to rename a column (e.g. 'Rename Backlog to Upcoming'), update the title of that column in 'columns'.
5. General questions: If no board mutation is requested, set 'board_update' to null.
6. Return ONLY raw valid JSON string without markdown wrappers."""


def smart_local_nlp(user_message: str, board_data: dict) -> dict:
    lower = user_message.lower().strip()
    columns = board_data.get("columns", [])
    cards = dict(board_data.get("cards", {}))

    # Helper: Match column by title or alias
    def match_column(text: str):
        for col in columns:
            title_lower = col["title"].lower()
            col_id = col["id"].lower()
            if title_lower in text or col_id in text:
                return col
            # Common column aliases
            if "progress" in text and "progress" in title_lower:
                return col
            if "backlog" in text and "backlog" in title_lower:
                return col
            if ("done" in text or "complete" in text or "finished" in text) and "done" in title_lower:
                return col
            if "review" in text and "review" in title_lower:
                return col
            if "discovery" in text and "discovery" in title_lower:
                return col
        return None

    # Helper: Match card by ID or title token overlap
    def match_card(text: str):
        # 1. Exact or normalized ID match
        for cid, cobj in cards.items():
            cid_clean = cid.lower().replace("-", "")
            text_clean = text.replace("-", "")
            if cid.lower() in text or cid_clean in text_clean:
                return cid, cobj

        # 2. Exact title substring match
        for cid, cobj in cards.items():
            t_lower = cobj.get("title", "").lower()
            if t_lower and (t_lower in text or text in t_lower):
                return cid, cobj

        # 3. Token overlap match
        text_words = set(re.findall(r"\w+", text)) - {"card", "card1", "card2", "card3", "to", "in", "from", "the", "a", "an", "on", "for", "move", "delete", "clear", "remove"}
        best_cid = None
        best_overlap = 0

        for cid, cobj in cards.items():
            t_lower = cobj.get("title", "").lower()
            title_words = set(re.findall(r"\w+", t_lower)) - {"card", "to", "in", "from", "the", "a", "an", "on", "for"}
            overlap = len(text_words & title_words)
            if overlap > best_overlap:
                best_overlap = overlap
                best_cid = cid

        if best_cid and best_overlap > 0:
            return best_cid, cards[best_cid]

        return None, None

    # Intent 1: CLEAR / DELETE / REMOVE / CLEAN
    if any(k in lower for k in ["clear", "delete", "remove", "drop", "clean", "erase"]):
        # Check if clearing all cards in a column
        if "all" in lower or "everything" in lower:
            target_col = match_column(lower)
            if target_col:
                removed_ids = set(target_col.get("cardIds", []))
                new_cards = {cid: cobj for cid, cobj in cards.items() if cid not in removed_ids}
                updated_cols = []
                for col in columns:
                    col_copy = dict(col)
                    if col["id"] == target_col["id"]:
                        col_copy["cardIds"] = []
                    updated_cols.append(col_copy)
                return {
                    "reply": f"Cleared all **{len(removed_ids)}** cards from **{target_col['title']}** column!",
                    "board_update": {"columns": updated_cols, "cards": new_cards},
                }

        # Check for specific card match
        card_id, card_obj = match_card(lower)
        if card_id and card_obj:
            new_cards = {cid: cobj for cid, cobj in cards.items() if cid != card_id}
            updated_cols = [
                {**col, "cardIds": [c for c in col["cardIds"] if c != card_id]}
                for col in columns
            ]
            return {
                "reply": f"Removed card **'{card_obj.get('title')}'** from the board.",
                "board_update": {"columns": updated_cols, "cards": new_cards},
            }

        # Match column to remove top card
        target_col = match_column(lower)
        if target_col:
            card_ids = list(target_col.get("cardIds", []))
            if card_ids:
                removed_id = card_ids.pop(0)
                removed_title = cards.get(removed_id, {}).get("title", removed_id)
                cards.pop(removed_id, None)

                updated_cols = []
                for col in columns:
                    col_copy = dict(col)
                    if col["id"] == target_col["id"]:
                        col_copy["cardIds"] = card_ids
                    updated_cols.append(col_copy)

                return {
                    "reply": f"Cleared card **'{removed_title}'** from **{target_col['title']}**!",
                    "board_update": {"columns": updated_cols, "cards": cards},
                }
            return {
                "reply": f"The column **{target_col['title']}** is already empty!",
                "board_update": None,
            }

    # Intent 2: RENAME COLUMN
    if "rename" in lower and "column" in lower:
        for col in columns:
            if col["title"].lower() in lower:
                match = re.search(r"(?:to|as)\s+([a-zA-Z0-9\s]+)", user_message, re.IGNORECASE)
                if match:
                    new_name = match.group(1).strip().capitalize()
                    updated_cols = [
                        {**c, "title": new_name} if c["id"] == col["id"] else c
                        for c in columns
                    ]
                    return {
                        "reply": f"Renamed column **{col['title']}** to **{new_name}**!",
                        "board_update": {"columns": updated_cols, "cards": cards},
                    }

    # Intent 3: MOVE / SHIFT / TRANSFER
    if any(k in lower for k in ["move", "shift", "transfer", "send"]):
        target_col = match_column(lower) or (columns[-1] if "done" in lower else None)
        card_id, card_obj = match_card(lower)

        if not card_id:
            # Find any available card in a different column
            for col in columns:
                if target_col and col["id"] != target_col["id"] and col.get("cardIds"):
                    card_id = col["cardIds"][0]
                    card_obj = cards.get(card_id)
                    break

        if target_col and card_id:
            updated_cols = []
            for col in columns:
                col_copy = dict(col)
                col_copy["cardIds"] = [c for c in col_copy["cardIds"] if c != card_id]
                if col["id"] == target_col["id"]:
                    col_copy["cardIds"].append(card_id)
                updated_cols.append(col_copy)

            card_title = card_obj.get("title", card_id) if card_obj else card_id
            return {
                "reply": f"Moved card **'{card_title}'** to **{target_col['title']}**!",
                "board_update": {"columns": updated_cols, "cards": cards},
            }

    # Intent 4: ADD / CREATE / NEW
    if any(k in lower for k in ["add", "create", "new", "insert"]):
        target_col = match_column(lower) or columns[0]
        raw = re.sub(r"(add|create|new|insert|a card|task|for|to|in progress|backlog|done|review|discovery)", "", lower, flags=re.IGNORECASE).strip()
        title = raw.title() if len(raw) > 1 else "New AI Task"
        new_id = f"card-ai-{len(cards) + 1}"

        cards[new_id] = {
            "id": new_id,
            "title": title,
            "details": "Created by AI Assistant.",
            "description": "Created by AI Assistant.",
            "priority": "high" if "urgent" in lower or "priority" in lower else "medium",
            "dueDate": None,
            "tags": ["AI"],
            "assignee": None,
        }

        updated_cols = []
        for col in columns:
            col_copy = dict(col)
            if col["id"] == target_col["id"]:
                col_copy["cardIds"] = list(col_copy["cardIds"]) + [new_id]
            updated_cols.append(col_copy)

        return {
            "reply": f"Created new task **'{title}'** in **{target_col['title']}**!",
            "board_update": {"columns": updated_cols, "cards": cards},
        }

    # Intent 5: PROJECT SUMMARY / INTELLIGENCE
    if any(k in lower for k in ["summary", "summarize", "overview", "health", "progress"]):
        total_tasks = len(cards)
        done_col = next((c for c in columns if "done" in c["title"].lower() or "complete" in c["title"].lower()), None)
        done_count = len(done_col["cardIds"]) if done_col else 0
        pct = round((done_count / total_tasks * 100)) if total_tasks > 0 else 0
        high_prio = sum(1 for c in cards.values() if c.get("priority") == "high")

        counts = [f"• **{c['title']}**: {len(c.get('cardIds', []))} tasks" for c in columns]
        summary_text = (
            f"📊 **Project Intelligence Summary**\n\n"
            f"• **Total Tasks**: {total_tasks}\n"
            f"• **Completed**: {done_count} ({pct}% completion)\n"
            f"• **High Priority**: {high_prio} tasks\n\n"
            f"**Column Breakdown:**\n" + "\n".join(counts) + "\n\n"
            f"💡 *Recommendation:* Focus on clearing high-priority tasks in In Progress to maintain momentum."
        )
        return {"reply": summary_text, "board_update": None}

    # Intent 6: WORKLOAD ANALYSIS
    if any(k in lower for k in ["workload", "assignee", "capacity", "team"]):
        assignee_map = {}
        unassigned = 0
        for card in cards.values():
            assignee = card.get("assignee")
            if assignee:
                assignee_map[assignee] = assignee_map.get(assignee, 0) + 1
            else:
                unassigned += 1

        workload_lines = [f"• **@{user}**: {cnt} task(s)" for user, cnt in assignee_map.items()]
        if unassigned > 0:
            workload_lines.append(f"• **Unassigned**: {unassigned} task(s)")

        workload_text = (
            f"👥 **Workload Distribution Analysis**\n\n"
            + ("\n".join(workload_lines) if workload_lines else "No tasks assigned yet.") +
            f"\n\n💡 *Insight:* Ensure tasks are balanced across team members to prevent individual burnout."
        )
        return {"reply": workload_text, "board_update": None}

    # Intent 7: OVERDUE & DEADLINES
    if any(k in lower for k in ["overdue", "due", "deadline", "schedule"]):
        due_list = []
        for card in cards.values():
            if card.get("dueDate"):
                due_list.append(f"• **'{card.get('title')}'** — Due {card.get('dueDate')} ({card.get('priority', 'medium')} priority)")

        due_text = (
            f"⏰ **Upcoming & Overdue Task Analysis**\n\n"
            + ("\n".join(due_list) if due_list else "No scheduled deadlines found on active cards.") +
            f"\n\n💡 *Action:* Review due dates regularly in the task details editor."
        )
        return {"reply": due_text, "board_update": None}

    # Intent 8: ORGANIZATION & PRIORITIZATION
    if any(k in lower for k in ["organize", "organization", "prioritize", "suggest", "suggestion", "clean"]):
        high_backlog = 0
        backlog_col = columns[0] if columns else None
        if backlog_col:
            for cid in backlog_col.get("cardIds", []):
                if cards.get(cid, {}).get("priority") == "high":
                    high_backlog += 1

        suggest_text = (
            f"⚡ **Project Organization Recommendations**\n\n"
            f"1. **High Priority in Backlog**: {high_backlog} urgent task(s) waiting in Backlog.\n"
            f"2. **Column Balance**: Recommend keeping 'In Progress' capped at 3-5 tasks for optimal flow.\n"
            f"3. **Tagging**: Ensure all active tasks have descriptive tags for fast filtering."
        )
        return {"reply": suggest_text, "board_update": None}

    return {
        "reply": f"I processed your prompt: *\"{user_message}\"*. Ask me to summarize project, analyze workload, check overdue tasks, or move cards!",
        "board_update": None,
    }


async def chat_with_ai(user_message: str, history: list, board_data: dict):
    if not config.OPENROUTER_API_KEY or "example-key" in config.OPENROUTER_API_KEY:
        return smart_local_nlp(user_message, board_data)

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Project Management MVP",
    }

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-4:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    prompt_content = f"Current Kanban Board JSON:\n{json.dumps(board_data)}\n\nUser Request:\n{user_message}"
    messages.append({"role": "user", "content": prompt_content})

    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(2):
            try:
                response = await client.post(
                    config.OPENROUTER_URL, headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )

                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                parsed = json.loads(content)
                return {
                    "reply": parsed.get("reply", "I processed your request."),
                    "board_update": parsed.get("board_update"),
                }
            except Exception as e:
                logger.warning(f"OpenRouter attempt {attempt + 1} failed: {str(e)}")
                if attempt == 1:
                    logger.error(f"OpenRouter chat error after retries: {str(e)}")
                    return smart_local_nlp(user_message, board_data)
