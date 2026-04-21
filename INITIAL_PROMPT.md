# First-run prompt for Claude Code

You are helping me set up two GitHub repositories for the PDA Investigations
programme. This is a real, public-facing piece of research that will be cited
and scrutinised. Quality matters more than speed.

## Step 1: Read these files before doing anything else

1. `AGENT_CONTEXT.md` in this repo — shared context, standards, and working
   principles for all PDA Investigations work.
2. `INVESTIGATION_BRIEF.md` in this repo — MTD-specific decisions, framing,
   and the methodology we have agreed.
3. `NOTES.md` if present — my private working notes (gitignored). Read but do
   not commit or quote from.
4. `data/sources.yaml`, `data/external_series.yaml`, `data/assumptions.yaml`
   — structured seed data that will populate Supabase.

You must also have read access to the sibling repo at `../pda-investigations`.
If that directory is not present, stop and ask me to clone it alongside this
one before proceeding.

## Step 2: Propose a branch strategy

Before creating any files or running any commits, tell me:
- What feature branches you propose to create in each repo
- What work goes in each branch
- The order in which you'll open PRs

I want to review this before you start. My coding standards are in
`AGENT_CONTEXT.md`; nothing goes to main without a PR.

## Step 3: First-run tasks (once branch strategy is approved)

Execute these in order, opening PRs as appropriate:

1. Scaffold both repos with standard structure (see `AGENT_CONTEXT.md` for the
   conventions).
2. Draft README.md for both repos. The umbrella README describes the PDA
   Investigations programme as a whole. The MTD README describes this specific
   investigation. Both should cross-link and cite the PDA Platform.
3. Draft methodology.md for the MTD investigation. This is the public
   methodology document and must be defensible to an FT editor, a
   tax-policy reviewer, and a Public Accounts Committee reader. The
   INVESTIGATION_BRIEF gives you the substance; your job is to structure and
   render it.
4. Write CITATION.cff for both repos with Ant Newman as author
   (ORCID 0000-0002-8612-3647, affiliation TortoiseAI).
5. Write LICENSE files: MIT for code, CC BY 4.0 for written content and data.
   Follow the same pattern as the existing ARMM and PDA Platform repos.
6. Write .gitignore that includes NOTES.md, .env, node_modules, __pycache__,
   .DS_Store, and any Supabase credential files.
7. Load the seed data from the three YAML files into Supabase via the MCP
   connection to project `bulheatuxvktopxrwbvs`. Use the `apply_migration` or
   `execute_sql` tool as appropriate. Propose the SQL before running it.
8. Produce a short summary of what got loaded where, with a link to the
   Supabase project dashboard.

## Step 4: Stop

Do not start the drift analysis itself. That is a separate unit of work with
its own review gate. Once the repositories are scaffolded, the documentation
is drafted (as PRs awaiting my review), and the seed data is loaded into
Supabase, your job is done for this session.

## Things I do not want you to do in this session

- Direct commits to main on either repo
- Force pushes or destructive git operations
- Assume my preferences; if something is unclear, ask
- Start the analysis or the drift calculations
- Summarise INVESTIGATION_BRIEF.md rather than execute against it
- Create NOTES.md or write to it (that's mine)
- Commit API keys, service role tokens, or any credentials to git

Begin with step 1.