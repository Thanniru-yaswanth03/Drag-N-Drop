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
      return `http://127.0.0.1:8000${path}`;
    }
    if (window.location.port === "8000") {
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

export async function fetchProjects(username: string = "user"): Promise<Project[]> {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects?username=${encodeURIComponent(username)}`),
      { headers: getAuthFetchHeaders() }
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch projects: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching projects:", error);
    return [];
  }
}

export async function createProjectApi(
  username: string = "user",
  name: string
): Promise<Project | null> {
  try {
    const response = await fetch(getApiUrl(`/api/projects?username=${encodeURIComponent(username)}`), {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ name }),
    });
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error("Error creating project:", error);
  }
  return null;
}

export async function updateProjectApi(
  username: string = "user",
  projectId: string,
  name: string
): Promise<Project | null> {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects/${encodeURIComponent(projectId)}?username=${encodeURIComponent(username)}`),
      {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify({ name }),
      }
    );
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error("Error updating project:", error);
  }
  return null;
}

export async function deleteProjectApi(
  username: string = "user",
  projectId: string
): Promise<boolean> {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects/${encodeURIComponent(projectId)}?username=${encodeURIComponent(username)}`),
      {
        method: "DELETE",
        headers: getAuthFetchHeaders(),
      }
    );
    return response.ok;
  } catch (error) {
    console.error("Error deleting project:", error);
    return false;
  }
}

export async function fetchBoard(
  username: string = "user",
  projectId?: string
): Promise<BoardData | null> {
  try {
    let path = `/api/board?username=${encodeURIComponent(username)}`;
    if (projectId) {
      path += `&project_id=${encodeURIComponent(projectId)}`;
    }
    const response = await fetch(getApiUrl(path), {
      headers: getAuthFetchHeaders(),
    });
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
  username: string = "user",
  boardData: BoardData,
  projectId?: string
): Promise<boolean> {
  try {
    let path = `/api/board?username=${encodeURIComponent(username)}`;
    if (projectId) {
      path += `&project_id=${encodeURIComponent(projectId)}`;
    }
    const response = await fetch(getApiUrl(path), {
      method: "PUT",
      headers: getAuthHeaders(),
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
    const response = await fetch(getApiUrl(`/api/cards?username=${encodeURIComponent(username)}`), {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ columnId, title, details, ...extraFields }),
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
  },
  username: string = "user"
) {
  try {
    const activeUser = username !== "user" ? username : (typeof localStorage !== "undefined" ? localStorage.getItem("pm_auth_user") || "user" : "user");
    const response = await fetch(getApiUrl(`/api/cards/${encodeURIComponent(cardId)}?username=${encodeURIComponent(activeUser)}`), {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(cardData),
    });
    if (response.ok) {
      const data = await response.json();
      return data.card;
    }
  } catch (error) {
    console.error("Error updating card via API:", error);
  }
  return null;
}

export async function deleteCardApi(cardId: string, username: string = "user") {
  try {
    const activeUser = username !== "user" ? username : (typeof localStorage !== "undefined" ? localStorage.getItem("pm_auth_user") || "user" : "user");
    const response = await fetch(getApiUrl(`/api/cards/${encodeURIComponent(cardId)}?username=${encodeURIComponent(activeUser)}`), {
      method: "DELETE",
      headers: getAuthFetchHeaders(),
    });
    return response.ok;
  } catch (error) {
    console.error("Error deleting card via API:", error);
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
  details?: Record<string, any>;
  createdAt?: string | null;
};

export async function fetchProjectActivity(
  projectId: string,
  username: string = "user"
): Promise<ActivityItem[]> {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects/${encodeURIComponent(projectId)}/activity?username=${encodeURIComponent(username)}`),
      { headers: getAuthFetchHeaders() }
    );
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
  projectId: string,
  username: string = "user"
): Promise<{ members: ProjectMember[]; userRole: string }> {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects/${encodeURIComponent(projectId)}/members?username=${encodeURIComponent(username)}`),
      { headers: getAuthFetchHeaders() }
    );
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
  role: string,
  requestingUsername: string = "user"
) {
  try {
    const response = await fetch(
      getApiUrl(`/api/projects/${encodeURIComponent(projectId)}/members?username=${encodeURIComponent(requestingUsername)}`),
      {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ username: targetUsername, role }),
      }
    );
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
  targetUsername: string,
  requestingUsername: string = "user"
) {
  try {
    const response = await fetch(
      getApiUrl(
        `/api/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(targetUsername)}?username=${encodeURIComponent(requestingUsername)}`
      ),
      {
        method: "DELETE",
        headers: getAuthFetchHeaders(),
      }
    );
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

export async function fetchNotificationsApi(
  username: string = "user"
): Promise<{ notifications: NotificationItem[]; unreadCount: number }> {
  try {
    const response = await fetch(
      getApiUrl(`/api/notifications?username=${encodeURIComponent(username)}`),
      { headers: getAuthFetchHeaders() }
    );
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

export async function markNotificationReadApi(
  notificationId: string,
  username: string = "user"
) {
  try {
    const response = await fetch(
      getApiUrl(
        `/api/notifications/${encodeURIComponent(notificationId)}/read?username=${encodeURIComponent(username)}`
      ),
      {
        method: "PUT",
        headers: getAuthFetchHeaders(),
      }
    );
    return response.ok;
  } catch (error) {
    console.error("Error marking notification read:", error);
    return false;
  }
}

export async function markAllNotificationsReadApi(username: string = "user") {
  try {
    const response = await fetch(
      getApiUrl(`/api/notifications/read-all?username=${encodeURIComponent(username)}`),
      {
        method: "POST",
        headers: getAuthHeaders(),
      }
    );
    return response.ok;
  } catch (error) {
    console.error("Error marking all read:", error);
    return false;
  }
}
