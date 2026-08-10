import type { BoardData } from "@/lib/kanban";

export async function fetchBoard(username: string = "user"): Promise<BoardData | null> {
  try {
    const response = await fetch(`/api/board?username=${encodeURIComponent(username)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch board: ${response.statusText}`);
    }
    const data = await response.json();
    return {
      columns: data.columns || [],
      cards: data.cards || {},
    };
  } catch (error) {
    console.error("Error fetching board:", error);
    return null;
  }
}

export async function saveBoard(username: string = "user", boardData: BoardData): Promise<boolean> {
  try {
    const response = await fetch(`/api/board?username=${encodeURIComponent(username)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(boardData),
    });
    return response.ok;
  } catch (error) {
    console.error("Error saving board:", error);
    return false;
  }
}

export async function createCardApi(
  username: string,
  columnId: string,
  title: string,
  details: string
) {
  try {
    const response = await fetch(`/api/cards?username=${encodeURIComponent(username)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ columnId, title, details }),
    });
    if (response.ok) {
      const data = await response.json();
      return data.card;
    }
  } catch (error) {
    console.error("Error creating card via API:", error);
  }
  return null;
}

export async function deleteCardApi(cardId: string) {
  try {
    const response = await fetch(`/api/cards/${encodeURIComponent(cardId)}`, {
      method: "DELETE",
    });
    return response.ok;
  } catch (error) {
    console.error("Error deleting card via API:", error);
    return false;
  }
}
