import { fetchBoard, saveBoard } from "@/lib/api";
import { initialData } from "@/lib/kanban";

describe("api client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches board data successfully", async () => {
    const mockBoardResponse = {
      columns: [{ id: "col-1", title: "Backlog", cardIds: ["card-1"] }],
      cards: { "card-1": { id: "card-1", title: "Test", details: "" } },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockBoardResponse,
    } as Response);

    const result = await fetchBoard("user");
    expect(result).toEqual(mockBoardResponse);
    expect(fetch).toHaveBeenCalledWith("/api/board?username=user");
  });

  it("saves board data successfully", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
    } as Response);

    const success = await saveBoard("user", initialData);
    expect(success).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/board?username=user", expect.objectContaining({
      method: "PUT",
    }));
  });
});
