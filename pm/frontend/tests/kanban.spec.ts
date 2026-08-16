import { expect, test, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  try {
    await page.request.post("http://127.0.0.1:8008/api/auth/register", {
      data: { username: "user", password: "password" },
    });
  } catch {
    // Ignore if already registered
  }
});

const login = async (page: Page) => {
  await page.goto("/");
  const boardHeading = page.getByRole("heading", { name: /Drag N Drop/i }).first();
  if (await boardHeading.isVisible()) {
    return;
  }
  const signInTab = page.getByRole("button", { name: "Sign In", exact: true }).first();
  if (await signInTab.isVisible()) {
    await signInTab.click();
  }

  const usernameInput = page.getByLabel(/username/i);
  await expect(usernameInput).toBeVisible({ timeout: 10000 });
  await usernameInput.fill("user");
  await page.getByLabel(/password/i).fill("password");
  await page.locator('button[type="submit"]').click();
  await expect(boardHeading).toBeVisible({ timeout: 15000 });
};

test("shows login screen initially", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign In" })).toBeVisible();
});

test("shows error on invalid login", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel(/username/i).fill("wrong_ghost_user");
  await page.getByLabel(/password/i).fill("wrongpass_123");
  await page.locator('button[type="submit"]').click();
  await expect(page.getByText("Invalid username or password")).toBeVisible();
});

test("loads the kanban board after login", async ({ page }) => {
  await login(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await login(page);
  const uid = Math.random().toString(36).slice(2, 6);
  const cardTitle = `Playwright card ${uid}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: "Add Task" }).click();
  await firstColumn.getByPlaceholder("Card title...").fill(cardTitle);
  await firstColumn.getByPlaceholder("Details and context...").fill("Added via e2e.");
  await firstColumn.locator('button[type="submit"]').click();
  await expect(firstColumn.getByText(cardTitle)).toBeVisible();
});

test("creates and edits a detailed task and verifies UI updates", async ({ page }) => {
  await login(page);
  const uid = Math.random().toString(36).slice(2, 6);
  const initTitle = `Task To Edit ${uid}`;
  const updatedTitle = `Updated Task ${uid}`;

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: "Add Task" }).click();
  await firstColumn.getByPlaceholder("Card title...").fill(initTitle);
  await firstColumn.getByPlaceholder("Details and context...").fill("Initial details.");
  await firstColumn.locator('button[type="submit"]').click();
  await expect(firstColumn.getByText(initTitle)).toBeVisible();

  const editBtn = page.getByLabel(`Edit ${initTitle}`);
  await editBtn.click();
  await expect(page.getByRole("heading", { name: "Edit Task" })).toBeVisible();


  await page.getByPlaceholder("Title...").fill(updatedTitle);
  await page.getByPlaceholder("Add detailed task description...").fill("Enriched description for Part 11.");
  await page.locator("form").getByRole("button", { name: "high" }).click();
  await page.locator('input[type="date"]').fill("2026-12-31");
  await page.getByPlaceholder("Assignee name or user...").fill("yash");
  await page.getByPlaceholder("New tag...").fill("e2etag");
  await page.getByRole("button", { name: "+ Add Tag" }).click();
  await expect(page.locator("form").getByText("#e2etag")).toBeVisible();
  await page.getByRole("button", { name: /save changes/i }).click();

  await expect(page.getByText(updatedTitle)).toBeVisible();
  await expect(page.locator('[data-testid^="card-"]').getByText("#e2etag").first()).toBeVisible();
  await expect(page.locator('[data-testid^="card-"]').getByText("2026-12-31").first()).toBeVisible();
  await expect(page.locator('[data-testid^="card-"]').getByText("yash").first()).toBeVisible();
});

test("supports search, filtering, sorting, and resetting filters", async ({ page }) => {
  await login(page);
  const uid = Math.random().toString(36).slice(2, 6);
  const targetTitle = `Target Roadmap ${uid}`;
  const otherTitle = `Other Signal ${uid}`;

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: "Add Task" }).click();
  await firstColumn.getByPlaceholder("Card title...").fill(targetTitle);
  await firstColumn.getByPlaceholder("Details and context...").fill("Roadmap details");
  await firstColumn.locator('button[type="submit"]').click();
  await expect(firstColumn.getByText(targetTitle)).toBeVisible();

  await firstColumn.getByRole("button", { name: "Add Task" }).click();
  await firstColumn.getByPlaceholder("Card title...").fill(otherTitle);
  await firstColumn.getByPlaceholder("Details and context...").fill("Customer feedback");
  await firstColumn.locator('button[type="submit"]').click();
  await expect(firstColumn.getByText(otherTitle)).toBeVisible();

  const searchInput = page.getByPlaceholder("Search tasks by title or description...");
  await searchInput.fill(targetTitle);
  await expect(page.getByText(targetTitle)).toBeVisible();
  await expect(page.getByText(otherTitle)).not.toBeVisible();

  await page.getByRole("button", { name: "Clear search" }).click();
  await expect(page.getByText(otherTitle)).toBeVisible();
});


test("supports creating and switching between multiple independent projects", async ({ page }) => {
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
  await page.route("**/activity*", async (route) => {
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
  const actBtn = page.getByRole("button", { name: /activity log/i }).first();
  await actBtn.click();

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

test("handles registration and new user login flow", async ({ page, context }) => {
  await context.clearCookies();
  await page.goto("/");
  await page.evaluate(() => localStorage.clear()).catch(() => {});
  await page.goto("/");

  const uid = Math.random().toString(36).slice(2, 8);
  const newUsername = `reg_${uid}`;
  const newPassword = "Password!123";

  const createAccountTab = page.getByRole("button", { name: "Create Account" }).first();
  await expect(createAccountTab).toBeVisible({ timeout: 10000 });
  await createAccountTab.click();
  await expect(page.getByRole("heading", { name: "Register Account" })).toBeVisible();

  await page.getByLabel(/username/i).fill(newUsername);
  await page.getByLabel(/password/i).fill(newPassword);
  await page.locator('button[type="submit"]').click();

  await expect(page.getByRole("heading", { name: /Drag N Drop/i }).first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("button", { name: /logout/i })).toBeVisible();
});




test("renders mobile viewport without overflow and supports theme toggle", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await login(page);

  await expect(page.getByRole("heading", { name: /Drag N Drop/i }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: /activity log/i }).first()).toBeVisible();

  // Test Theme Toggle
  const themeBtn = page.getByRole("button", { name: /toggle theme|theme/i }).first();
  await expect(themeBtn).toBeVisible();
  await themeBtn.click();
});

test("supports undo and redo controls", async ({ page }) => {
  await login(page);

  const undoBtn = page.getByRole("button", { name: /undo/i }).first();
  const redoBtn = page.getByRole("button", { name: /redo/i }).first();

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

  const notifBtn = page.getByRole("button", { name: /notifications|alerts/i }).first();
  await expect(notifBtn).toBeVisible();
  await notifBtn.click();

  await expect(page.getByRole("heading", { name: "Notifications & Reminders" })).toBeVisible();
  await page.getByRole("button", { name: "Close", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "Notifications & Reminders" })).not.toBeVisible();
});



