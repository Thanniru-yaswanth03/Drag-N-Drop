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

    const result = await fetchBoard("board-test-123");
    expect(result).toEqual(mockBoardResponse);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/board\?project_id=board-test-123/),
      expect.objectContaining({ headers: expect.any(Object) })
    );
  });

  it("saves board data successfully", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
    } as Response);

    const success = await saveBoard(initialData, "board-test-123");
    expect(success).toBe(true);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/board\?project_id=board-test-123/),
      expect.objectContaining({
        method: "PUT",
      })
    );
  });
});
