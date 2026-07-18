# AI Agency Lead Generator

A no-code agency tool that scrapes local business listings, generates personalized cold emails via AI, and saves them to a CSV.

## Usage

```bash
python agency_system.py --city "Miami" --niche "Roofers"
```

### Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--city` | Target city | `"Miami"`, `"Austin"`, `"New York"` |
| `--niche` | Industry / niche | `"Roofers"`, `"Plumbers"`, `"Electricians"` |

### Output

Creates a CSV file named `{niche}_{city}_leads.csv` with columns:

- `business_name` — Name of the business
- `phone` — Phone number
- `ai_email` — AI-generated cold email (requires `GROQ_KEY`)

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_KEY` | For AI emails | Groq API key for LLM-generated email copy |

### Example

```bash
export GROQ_KEY="gsk_your_key_here"
python agency_system.py --city "Austin" --niche "Plumbers"
```
