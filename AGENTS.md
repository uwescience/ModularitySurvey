# Modularity Survey Project

This is a literature survey database tracking academic papers on modularity in biology. The database is stored as a CSV file and can be queried via [DataSette](https://lite.datasette.io/?csv=https://raw.githubusercontent.com/uwescience/ModularitySurvey/main/db/modularity_survey.csv).

## Project Structure

- `db/modularity_survey.csv` — Main literature database with detailed paper metadata
- `README.md` — Project overview and basic query examples

## Database Schema

The CSV contains these key columns (see header rows for full documentation):

- **Metadata**: AddedBy, AIAgentAndModel, LastNameOf1stAuthor, All authors, Paper title, Year, Paper type, DOI URL
- **Technical**: Modeling framework, Definition of module, Algorithmic aspect, Data
- **Biological Context**: Context of system, Purpose of module, Level of organization, Organism  
- **Impact**: Impact of paper, Citations, Summary, Primary theme
- **Review Status**: Read by, Notes (multiple columns for different reviewers)

## Common Workflows

### Adding New Papers

When adding entries to `modularity_survey.csv`:
1. Maintain consistent formatting with existing entries
2. Include all required metadata fields (especially: authors, title, year, DOI)
3. Use standardized keywords for: Paper type (research/review/perspective), Modeling framework (Boolean network/ODE/graph based/stochastic), Level of organization (cell/tissue/organism)
4. Provide concise 1-2 sentence summary for the Summary column
5. Always credit AddedBy and AIAgentAndModel used

### Expanding the Bibliography

**Use the `@literature-search-agent` to find related papers:**
- Find papers that cite influential works already in the database
- Expand specific subdisciplines (e.g., Boolean networks, evolutionary modularity)
- Identify follow-up work on key papers

Example: *"@literature-search-agent find papers that cite the Newman 2006 modularity matrix paper and filter by >50 citations"*

### Querying the Database

The README shows basic SQL examples. More complex queries via DataSette:
- Filter by year range, organism, modeling framework
- Aggregate by primary theme or level of organization
- Search summaries for specific concepts

## Conventions

- **Citation format**: Standard academic format with all authors listed
- **DOI URLs**: Always use `https://doi.org/` format
- **Keywords**: Use controlled vocabulary from existing entries when possible
- **AI attribution**: When AI agents help curate entries, note the agent and model version in AIAgentAndModel column

## License

MIT License — see LICENSE file
