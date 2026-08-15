import type { BoardData } from "@/lib/kanban";

export type Project = {
  id: string;
  name: string;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export const getApiUrl = (path: string) => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl) {
    const baseUrl = envUrl.replace(/\/$/, "");
    return `${baseUrl}${path}`;
  }
  if (typeof window !== "undefined") {
    if (
      (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") &&
      window.location.protocol === "http:"
    ) {
      return `http://127.0.0.1:8001${path}`;
    }
    if (window.location.port === "8001" || window.location.port === "8000") {
      return path;
    }
    return `https://drag-n-drop-28p3.onrender.com${path}`;
  }
  return path;
};

export function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (typeof localStorage !== "undefined") {
    const token = localStorage.getItem("pm_auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
      headers["X-Session-Token"] = token;
    }
  }
  return headers;
}

export function getAuthFetchHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (typeof localStorage !== "undefined") {
    const token = localStorage.getItem("pm_auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
      headers["X-Session-Token"] = token;
    }
  }
  return headers;
}

function checkUnauthorized(response: Response) {
  if (response.status === 401 && typeof localStorage !== "undefined") {
    localStorage.removeItem("pm_auth_token");
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("pm_auth_unauthorized"));
    }
  }
}

export async function registerApi(username: string, password: string) {
  const cleanUsername = username.trim().toLowerCase();
  try {
    const response = await fetch(getApiUrl("/api/auth/register"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: cleanUsername, password }),
    });
    const data = await response.json().catch(() => ({}));
    if (response.ok && data.success) {
      if (typeof localStorage !== "undefined" && data.token) {
        localStorage.setItem("pm_auth_token", data.token);
      }
      return { success: true, user: data.user || cleanUsername, token: data.token };
    }
    return { success: false, error: data.detail || "Registration failed" };
  } catch (error) {
    console.error("Error registering user:", error);
    return { success: false, error: "Network error during registration" };
  }
}

export async function loginApi(username: string, password: string) {
  const cleanUsername = username.trim().toLowerCase();
  try {
    const response = await fetch(getApiUrl("/api/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: cleanUsername, password }),
    });
    const data = await response.json().catch(() => ({}));
    if (response.ok && data.success) {
      if (typeof localStorage !== "undefined" && data.token) {
        localStorage.setItem("pm_auth_token", data.token);
      }
      return { success: true, user: data.user || cleanUsername, token: data.token };
    }
    return { success: false, error: data.detail || "Invalid username or password" };
  } catch (error) {
    console.error("Error logging in:", error);
    return { success: false, error: "Network error during login" };
  }
}

export async function checkAuthApi(): Promise<{ authenticated: boolean; user?: string }> {
  try {
    const response = await fetch(getApiUrl("/api/auth/me"), {
      headers: getAuthFetchHeaders(),
    });
    checkUnauthorized(response);
    if (response.ok) {
      const data = await response.json();
      return { authenticated: true, user: data.user };
    }
  } catch (error) {
    console.error("Error checking auth:", error);
  }
  return { authenticated: false };
}

export async function logoutApi(): Promise<boolean> {
  try {
    await fetch(getApiUrl("/api/auth/logout"), {
      method: "POST",
      headers: getAuthHeaders(),
    });
  } catch (error) {
    console.error("Error logging out:", error);
  }
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem("pm_auth_token");
  }
  return true;
}

export async function fetchProjects(): Promise<Project[]> {
  try {
    const response = await fetch(getApiUrl("/api/projects"), {
      headers: getAuthFetchHeaders(),
    });
    checkUnauthorized(response);
    if (!response.ok) {
      throw new Error(`Failed to fetch projects: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching projects:", error);
    return [];
  }
}

export async function createProjectApi(name: string): Promise<Project | null> {
  try {
    const response = await fetch(getApiUrl("/api/projects"), {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ name }),
    });
    checkUnauthorized(response);
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error("Error creating project:", error);
  }
  return null;
}

export async function updateProjectApi(
  projectId: string,
  name: string
): Promise<Project | null> {
  try {
    const response = await fetch(getApiUrl(`/api/projects/${encodeURIComponent(projectId)}`), {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({ name }),
    });
    checkUnauthorized(response);
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error("Error updating project:", error);
  }
  return null;
}

export async function deleteProjectApi(projectId: string): Promise<boolean> {
  try {
    const response = await fetch(getApiUrl(`/api/projects/${encodeURIComponent(projectId)}`), {
      method: "DELETE",
      headers: getAuthFetchHeaders(),
    });
    checkUnauthorized(response);
    return response.ok;
  } catch (error) {
    console.error("Error deleting project:", error);
    return false;
  }
}

export async function fetchBoard(projectId?: string): Promise<BoardData | null> {
  try {
    let path = "/api/board";
    if (projectId) {
      path += `?project_id=${encodeURIComponent(projectId)}`;
    }
    const response = await fetch(getApiUrl(path), {
      headers: getAuthFetchHeaders(),
    });
    checkUnauthorized(response);
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

export async function saveBoard(
  boardData: BoardData,
  projectId?: string
): Promise<boolean> {
  try {
    let path = "/api/board";
    if (projectId) {
      path += `?project_id=${encodeURIComponent(projectId)}`;
    }
    const response = await fetch(getApiUrl(path), {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(boardData),
    });
    checkUnauthorized(response);
    return response.ok;
  } catch (error) {
    console.error("Error saving board:", error);
    return false;
  }
}

export async function createCardApi(
  columnId: string,
  title: string,
  details: string,
  extraFields?: {
    description?: string;
    priority?: "high" | "medium" | "low";
    dueDate?: string | null;
    tags?: string[];
    assignee?: string | null;
  }
) {
  try {
    const response = await fetch(getApiUrl("/api/cards"), {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ columnId, title, details, ...extraFields }),
    });
    checkUnauthorized(response);
    if (response.ok) {
      const data = await response.json();
      return data.card;
    }
  } catch (error) {
    console.error("Error creating card via API:", error);
  }
  return null;
}

export async function updateCardApi(
  cardId: string,
  cardData: {
    title?: string;
    details?: string;
    description?: string;
    priority?: "high" | "medium" | "low";
    dueDate?: string | null;
    tags?: string[];
    assignee?: string | null;
  }
) {
  try {
    const response = await fetch(getApiUrl(`/api/cards/${encodeURIComponent(cardId)}`), {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(cardData),
    });
    checkUnauthorized(response);
    if (response.ok) {
      const data = await response.json();
      return data.card;
    }
  } catch (error) {
    console.error("Error updating card via API:", error);
  }
  return null;
}

export async function deleteCardApi(cardId: string) {
  try {
    const response = await fetch(getApiUrl(`/api/cards/${encodeURIComponent(cardId)}`), {
      method: "DELETE",
      headers: getAuthFetchHeaders(),
    });
    checkUnauthorized(response);
    return response.ok;
  } catch (error) {
    console.error("Error deleting card via API:", error);
    return false;
  }
}

export async function moveCardApi(cardId: string, columnId: string, position: number = 0) {
  try {
    const response = await fetch(getApiUrl(`/api/cards/${encodeURIComponent(cardId)}/move`), {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify({ columnId, position }),
    });
    checkUnauthorized(response);
    return response.ok;
  } catch (error) {
    console.error("Error moving card via API:", error);
    return false;
  }
}

export async function updateColumnApi(columnId: string, title: string) {
  try {
    const response = await fetch(getApiUrl(`/api/columns/${encodeURIComponent(columnId)}`), {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify({ title }),
    });
    checkUnauthorized(response);
    return response.ok;
  } catch (error) {
    console.error("Error updating column via API:", error);
    return false;
  }
}

export async function clearColumnApi(columnId: string) {
  try {
    const response = await fetch(getApiUrl(`/api/columns/${encodeURIComponent(columnId)}/clear`), {
      method: "POST",
      headers: getAuthHeaders(),
    });
    checkUnauthorized(response);
    return response.ok;
  } catch (error) {
    console.error("Error clearing column via API:", error);
    return false;
  }
}

export type ActivityItem = {
  id: string;
  projectId: string;
  userId: string;
  actionType: string;
  entityType: string;
  entityId: string;
  message: string;
  details?: Record<string, unknown>;
  createdAt?: string | null;
};

export async function fetchProjectActivity(projectId: string): Promise<ActivityItem[]> {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects/${encodeURIComponent(projectId)}/activity`),
      { headers: getAuthFetchHeaders() }
    );
    checkUnauthorized(response);
    if (response.ok) {
      const data = await response.json();
      return data.activities || [];
    }
  } catch (error) {
    console.error("Error fetching project activity:", error);
  }
  return [];
}

export type ProjectMember = {
  id: string;
  username: string;
  role: "owner" | "admin" | "member" | "viewer";
  createdAt?: string | null;
};

export async function fetchProjectMembers(
  projectId: string
): Promise<{ members: ProjectMember[]; userRole: string }> {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects/${encodeURIComponent(projectId)}/members`),
      { headers: getAuthFetchHeaders() }
    );
    checkUnauthorized(response);
    if (response.ok) {
      const data = await response.json();
      return {
        members: data.members || [],
        userRole: data.userRole || "viewer",
      };
    }
  } catch (error) {
    console.error("Error fetching project members:", error);
  }
  return { members: [], userRole: "viewer" };
}

export async function addProjectMemberApi(
  projectId: string,
  targetUsername: string,
  role: string
) {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects/${encodeURIComponent(projectId)}/members`),
      {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ username: targetUsername, role }),
      }
    );
    checkUnauthorized(response);
    const data = await response.json().catch(() => ({}));
    if (response.ok && data.success) {
      return { success: true, member: data };
    }
    return { success: false, error: data.detail || "Failed to add member" };
  } catch (error) {
    console.error("Error adding project member:", error);
    return { success: false, error: "Network error" };
  }
}

export async function removeProjectMemberApi(
  projectId: string,
  targetUsername: string
) {
  try {
    const response = await fetch(
      getApiUrl(
        `/api/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(targetUsername)}`
      ),
      {
        method: "DELETE",
        headers: getAuthFetchHeaders(),
      }
    );
    checkUnauthorized(response);
    const data = await response.json().catch(() => ({}));
    if (response.ok && data.success) {
      return { success: true };
    }
    return { success: false, error: data.detail || "Failed to remove member" };
  } catch (error) {
    console.error("Error removing member:", error);
    return { success: false, error: "Network error" };
  }
}

export type NotificationItem = {
  id: string;
  projectId?: string | null;
  type: "due_soon" | "assigned" | "invited" | "system";
  title: string;
  message: string;
  isRead: boolean;
  createdAt?: string | null;
};

export async function fetchNotificationsApi(): Promise<{ notifications: NotificationItem[]; unreadCount: number }> {
  try {
    const response = await fetch(getApiUrl("/api/notifications"), {
      headers: getAuthFetchHeaders(),
    });
    checkUnauthorized(response);
    if (response.ok) {
      const data = await response.json();
      return {
        notifications: data.notifications || [],
        unreadCount: data.unreadCount || 0,
      };
    }
  } catch (error) {
    console.error("Error fetching notifications:", error);
  }
  return { notifications: [], unreadCount: 0 };
}

export async function markNotificationReadApi(notificationId: string) {
  try {
    const response = await fetch(
      getApiUrl(`/api/notifications/${encodeURIComponent(notificationId)}/read`),
      {
        method: "PUT",
        headers: getAuthFetchHeaders(),
      }
    );
    checkUnauthorized(response);
    return response.ok;
  } catch (error) {
    console.error("Error marking notification read:", error);
    return false;
  }
}

export async function markAllNotificationsReadApi() {
  try {
    const response = await fetch(getApiUrl("/api/notifications/read-all"), {
      method: "POST",
      headers: getAuthHeaders(),
    });
    checkUnauthorized(response);
    return response.ok;
  } catch (error) {
    console.error("Error marking all read:", error);
    return false;
  }
}
