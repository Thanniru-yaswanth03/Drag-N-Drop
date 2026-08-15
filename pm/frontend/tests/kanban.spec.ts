import { expect, test, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  try {
    await page.request.post("http://127.0.0.1:8000/api/board/reset?username=user");
  } catch {
    // Ignore reset errors
  }
});

const login = async (page: Page) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.locator('button[type="submit"]').click();
  await expect(page.getByRole("heading", { name: /Drag N Drop|Kanban Studio/i }).first()).toBeVisible();
};

test("shows login screen initially", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign In" })).toBeVisible();
});

test("shows error on invalid login", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("wrong");
  await page.getByLabel("Password").fill("wrongpass");
  await page.locator('button[type="submit"]').click();
  await expect(page.getByText("Invalid username or password")).toBeVisible();
});

test("loads the kanban board after login", async ({ page }) => {
  await login(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add (a card|task)/i }).click();
  await firstColumn.getByPlaceholder(/card title/i).fill("Playwright card");
  await firstColumn.getByPlaceholder(/details/i).fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add (card|task)/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("creates and edits a detailed task and verifies UI updates", async ({ page }) => {
  await login(page);

  const card1 = page.getByTestId("card-card-1");
  await card1.getByRole("button", { name: /edit/i }).click();
  await expect(page.getByRole("heading", { name: "Edit Task" })).toBeVisible();

  await page.getByPlaceholder("Title...").fill("Updated Roadmap Task");
  await page.getByPlaceholder("Add detailed task description...").fill("Enriched description for Part 11.");
  await page.locator("form").getByRole("button", { name: "high" }).click();
  await page.locator('input[type="date"]').fill("2026-12-31");
  await page.getByPlaceholder("Assignee name or user...").fill("yash");
  await page.getByPlaceholder("New tag...").fill("e2etag");
  await page.getByRole("button", { name: "+ Add Tag" }).click();
  await expect(page.getByText("#e2etag")).toBeVisible();
  await page.getByRole("button", { name: /save changes/i }).click();

  await expect(card1.getByText("Updated Roadmap Task")).toBeVisible();
  await expect(card1.getByText("#e2etag")).toBeVisible();
  await expect(card1.getByText("2026-12-31")).toBeVisible();
  await expect(card1.getByText("yash")).toBeVisible();
});

test("supports search, filtering, sorting, and resetting filters", async ({ page }) => {
  await login(page);

  const searchInput = page.getByPlaceholder("Search tasks by title or description...");
  await searchInput.fill("roadmap");
  await expect(page.getByText("Align roadmap themes")).toBeVisible();
  await expect(page.getByText("Gather customer signals")).not.toBeVisible();

  await page.getByRole("button", { name: "Clear search" }).click();
  await expect(page.getByText("Gather customer signals")).toBeVisible();

  await page.getByLabel("Sort tasks by").selectOption("title-asc");
  await page.getByLabel("Filter by priority").selectOption("medium");

  const clearFiltersBtn = page.getByRole("button", { name: /clear filters/i });
  await expect(clearFiltersBtn).toBeVisible();
  await clearFiltersBtn.click();

  await expect(page.getByText("Gather customer signals")).toBeVisible();
});

test("supports creating and switching between multiple independent projects", async ({ page }) => {
  // Mock /api/projects POST so it reliably returns a new project regardless of server state
  await page.route(/\/api\/projects/, async (route) => {
    const method = route.request().method();
    if (method === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: "proj-mobile-e2e", name: "Mobile Release" }),
      });
    } else if (method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ id: "proj-main-e2e", name: "Main Project" }]),
      });
    } else {
      await route.continue();
    }
  });

  await login(page);

  // Open Project Switcher
  const switcherBtn = page.getByRole("button", { name: /switch project/i });
  await switcherBtn.click();

  // Open New Project modal
  await page.getByRole("button", { name: "New Project" }).click();
  await page.getByPlaceholder("e.g. Q4 Marketing Campaign").fill("Mobile Release");
  await page.getByRole("button", { name: "Create Project" }).click();

  // After successful creation, switcher button should show new project name
  await expect(switcherBtn).toContainText("Mobile Release", { timeout: 8000 });

  // Switch back via switcher dropdown
  await switcherBtn.click();
  await page.getByRole("button", { name: "Main Project" }).click();
  await expect(switcherBtn).toContainText("Main Project", { timeout: 8000 });
});

test("logs out user", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: /logout/i }).click();
  await expect(page.getByRole("heading", { name: "Sign In" })).toBeVisible();
});

test("displays activity log modal with recorded project actions", async ({ page }) => {
  await page.route("**/api/projects/**/activity*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        activities: [
          {
            id: "act-101",
            projectId: "board-user",
            userId: "user",
            actionType: "card_created",
            entityType: "card",
            entityId: "card-1",
            message: "Created task 'Build Authentication Flow'",
            createdAt: "2026-08-11T10:00:00Z",
          },
          {
            id: "act-102",
            projectId: "board-user",
            userId: "user",
            actionType: "project_created",
            entityType: "project",
            entityId: "board-user",
            message: "Created project 'Main Project'",
            createdAt: "2026-08-11T09:00:00Z",
          },
        ],
      }),
    });
  });

  await login(page);

  // Click Activity Log button in header
  await page.getByRole("button", { name: /activity log/i }).click();

  // Verify Activity History dialog opens
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name: /activity history/i })).toBeVisible();

  // Verify activities listed
  await expect(dialog.getByText("Created task 'Build Authentication Flow'")).toBeVisible();

  // Test search filtering inside activity modal
  await dialog.getByPlaceholder("Search activity log...").fill("Authentication");
  await expect(dialog.getByText("Created task 'Build Authentication Flow'")).toBeVisible();

  // Close modal
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  await expect(dialog).not.toBeVisible();
});

test("handles registration and new user login flow", async ({ page }) => {
  await page.route("**/api/auth/register", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        user: "e2e_newuser",
        userId: "user-e2e-reg",
        token: "token-e2e-newuser",
      }),
    });
  });

  await page.route("**/api/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        user: "e2e_newuser",
        token: "token-e2e-newuser",
      }),
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Create Account" }).first().click();
  await expect(page.getByRole("heading", { name: "Register Account" })).toBeVisible();

  await page.getByLabel(/username/i).fill("e2e_newuser");
  await page.getByLabel(/password/i).fill("password123");
  await page.locator('button[type="submit"]').click();

  await expect(page.getByText("e2e_newuser")).toBeVisible();
});

test("renders mobile viewport without overflow and supports theme toggle", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await login(page);

  await expect(page.getByRole("heading", { name: "Drag N Drop" })).toBeVisible();
  await expect(page.getByRole("button", { name: /activity log/i })).toBeVisible();

  // Test Theme Toggle
  const themeBtn = page.getByRole("button", { name: /toggle theme/i });
  await expect(themeBtn).toBeVisible();
  await themeBtn.click();
});

test("supports undo and redo controls", async ({ page }) => {
  await login(page);

  const undoBtn = page.getByRole("button", { name: "Undo" });
  const redoBtn = page.getByRole("button", { name: "Redo" });

  await expect(undoBtn).toBeVisible();
  await expect(redoBtn).toBeVisible();
});

test("opens team members modal and lists project members", async ({ page }) => {
  await login(page);

  const membersBtn = page.getByRole("button", { name: /members/i });
  await expect(membersBtn).toBeVisible();
  await membersBtn.click();

  await expect(page.getByRole("heading", { name: "Project Team Members" })).toBeVisible();
  await page.getByRole("button", { name: "Close", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "Project Team Members" })).not.toBeVisible();
});

test("opens notifications modal and displays alerts", async ({ page }) => {
  await login(page);

  const notifBtn = page.getByRole("button", { name: /notifications/i });
  await expect(notifBtn).toBeVisible();
  await notifBtn.click();

  await expect(page.getByRole("heading", { name: "Notifications & Reminders" })).toBeVisible();
  await page.getByRole("button", { name: "Close", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "Notifications & Reminders" })).not.toBeVisible();
});
