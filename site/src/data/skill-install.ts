// Target the displayed bundle explicitly: root skills/ may contain older mirrors.
export function skillInstall(id: string): string {
  return `npx skills add https://github.com/mithudso/llms-explorer/tree/main/.claude/skills/${id} --skill ${id}`;
}
