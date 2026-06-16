import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

const apiBoard = {
  id: "board_default",
  title: "My Board",
  userId: "user_default",
  columns: initialData.columns.map((column, index) => ({
    id: column.id,
    title: column.title,
    position: index,
    cardIds: column.cardIds,
  })),
  cards: Object.fromEntries(
    Object.values(initialData.cards).map((card, index) => [
      card.id,
      {
        id: card.id,
        title: card.title,
        details: card.details,
        columnId: initialData.columns.find((c) => c.cardIds.includes(card.id))?.id ?? "col-backlog",
        position: index,
      },
    ])
  ),
};

const getFirstColumn = async () => (await screen.findAllByTestId(/column-/i))[0];

const jsonResponse = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/users/") && url.includes("/board")) {
          return jsonResponse(apiBoard);
        }
        if (url.includes("/api/boards/") && url.includes("/columns/") && init?.method === "PUT") {
          return jsonResponse({ ...apiBoard.columns[0], title: "New Name" });
        }
        if (url.includes("/api/columns/") && url.includes("/cards") && init?.method === "POST") {
          return jsonResponse({
            id: "card_new",
            title: "New card",
            details: "Notes",
            columnId: "col-backlog",
            position: 2,
          }, 201);
        }
        if (url.includes("/api/cards/") && init?.method === "DELETE") {
          return jsonResponse({ status: "ok" });
        }
        if (url.includes("/api/cards/") && url.includes("/move") && init?.method === "PATCH") {
          return jsonResponse({ status: "ok" });
        }
        return jsonResponse({ detail: "Not mocked" }, 500);
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders five columns", () => {
    render(<KanbanBoard userId="user" />);
    return expect(screen.findAllByTestId(/column-/i)).resolves.toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard userId="user" />);
    const column = await getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    await userEvent.tab();
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard userId="user" />);
    const column = await getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });
});
