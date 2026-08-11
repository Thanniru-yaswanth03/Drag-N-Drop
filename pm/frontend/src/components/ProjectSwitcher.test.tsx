import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProjectSwitcher } from "./ProjectSwitcher";
import type { Project } from "@/lib/api";

describe("ProjectSwitcher Component", () => {
  const sampleProjects: Project[] = [
    { id: "proj-1", name: "Main Project" },
    { id: "proj-2", name: "Mobile App Release" },
  ];

  it("renders active project button name", () => {
    render(
      <ProjectSwitcher
        projects={sampleProjects}
        activeProjectId="proj-1"
        onSelectProject={vi.fn()}
        onCreateProject={vi.fn()}
        onRenameProject={vi.fn()}
        onDeleteProject={vi.fn()}
      />
    );

    expect(screen.getByText("Main Project")).toBeInTheDocument();
  });

  it("opens dropdown and displays list of projects on click", () => {
    render(
      <ProjectSwitcher
        projects={sampleProjects}
        activeProjectId="proj-1"
        onSelectProject={vi.fn()}
        onCreateProject={vi.fn()}
        onRenameProject={vi.fn()}
        onDeleteProject={vi.fn()}
      />
    );

    const button = screen.getByRole("button", { name: /switch project/i });
    fireEvent.click(button);

    expect(screen.getByText("Workspace Projects")).toBeInTheDocument();
    expect(screen.getByText("Mobile App Release")).toBeInTheDocument();
  });

  it("calls onSelectProject when clicking a project item", () => {
    const handleSelect = vi.fn();
    render(
      <ProjectSwitcher
        projects={sampleProjects}
        activeProjectId="proj-1"
        onSelectProject={handleSelect}
        onCreateProject={vi.fn()}
        onRenameProject={vi.fn()}
        onDeleteProject={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /switch project/i }));
    fireEvent.click(screen.getByText("Mobile App Release"));

    expect(handleSelect).toHaveBeenCalledWith("proj-2");
  });

  it("opens create project dialog and submits new project name", () => {
    const handleCreate = vi.fn();
    render(
      <ProjectSwitcher
        projects={sampleProjects}
        activeProjectId="proj-1"
        onSelectProject={vi.fn()}
        onCreateProject={handleCreate}
        onRenameProject={vi.fn()}
        onDeleteProject={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /switch project/i }));
    fireEvent.click(screen.getByText("New Project"));

    expect(screen.getByText("Create New Project")).toBeInTheDocument();

    const nameInput = screen.getByPlaceholderText("e.g. Q4 Marketing Campaign");
    fireEvent.change(nameInput, { target: { value: "Sprint 2026" } });
    fireEvent.click(screen.getByRole("button", { name: /create project/i }));

    expect(handleCreate).toHaveBeenCalledWith("Sprint 2026");
  });
});
