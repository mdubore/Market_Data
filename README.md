# Market Data Candlestick Chart Generator

A Python tool to generate professional daily candlestick charts from financial market data stored in a SQLite database.

## Features

- 📊 **Candlestick Charts** - Professional OHLC visualization using mplfinance
- 💾 **SQLite Database** - Store and retrieve market data efficiently
- 🎯 **Multi-Ticker Support** - Visualize multiple tickers simultaneously
- 📁 **Batch Processing** - Generate charts for all tickers or specific ones
- 💾 **Export Options** - Save charts as PNG files or display interactively
- 📋 **Command-Line Interface** - Easy-to-use CLI with multiple options

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Setup Instructions

### 1. Clone or Download the Project

```bash
cd /path/to/Market_Data
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Creating Your Own config.yaml

Create a `config.yaml` file in the project root directory with the following structure:

```yaml
# Database Configuration
database:
  path: "market_data.db"
  
# API Configuration (for data fetching)
api:
  base_url: "https://api.example.com"
  timeout: 30
  
# Chart Configuration
chart:
  style: "default"
  figsize: [15, 8]
  dpi: 100
  
# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**Note:** The `config.yaml` file should not be committed to version control. Each user should create their own copy with their specific settings.

### Example config.yaml for Different Use Cases

**Minimal Configuration:**
```yaml
database:
  path: "market_data.db"
```

**Production Configuration:**
```yaml
database:
  path: "/var/data/market_data.db"
  
api:
  base_url: "https://api.production.example.com"
  timeout: 60
  
chart:
  style: "seaborn"
  figsize: [20, 10]
  dpi: 150
  
logging:
  level: "WARNING"
  format: "%(asctime)s - %(levelname)s - %(message)s"
```

## Database Schema

The SQLite database uses a single table `ohlc_data` with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| ticker | TEXT | Stock/crypto ticker symbol |
| date | TEXT | Trading date (YYYY-MM-DD) |
| open | REAL | Opening price |
| high | REAL | Highest price of the day |
| low | REAL | Lowest price of the day |
| close | REAL | Closing price |
| adj_close | REAL | Adjusted closing price |
| volume | INTEGER | Trading volume |

## Usage

### List Available Tickers

```bash
python candlestick_chart.py --list
```

Output:
```
Available tickers (8):
  - BTC-USD
  - FBTC
  - IBIT
  - MSTR
  - STRC
  - STRD
  - STRF
  - STRK
```

### Plot Single Ticker

Display chart interactively:
```bash
python candlestick_chart.py --ticker BTC-USD
```

Save chart to file:
```bash
python candlestick_chart.py --ticker BTC-USD --save-file btc_chart.png
```

### Generate All Charts

Create individual PNG files for each ticker:
```bash
python candlestick_chart.py --all --save-dir charts
```

### Combined View

Display all tickers in subplots:
```bash
python candlestick_chart.py --all --combined
```

Save combined view:
```bash
python candlestick_chart.py --all --combined --save-file all_tickers.png
```

### Using Custom Database Path

```bash
python candlestick_chart.py --db /path/to/custom_database.db --ticker BTC-USD
```

## Command-Line Arguments

```
options:
  -h, --help            show this help message and exit
  --db DB               Path to market_data.db (default: market_data.db)
  --ticker TICKER       Specific ticker to plot (e.g., BTC-USD)
  --all                 Plot all tickers
  --list                List all available tickers
  --save-dir SAVE_DIR   Directory to save charts (individual files)
  --save-file SAVE_FILE File to save combined chart
  --combined            Plot multiple tickers in subplots
```

## Project Structure

```
Market_Data/
├── README.md                      # This file
├── candlestick_chart.py          # Main chart generation script
├── market_data.py                # Database and data fetching utilities
├── config.yaml.example           # Example configuration (create your own)
├── requirements.txt              # Python dependencies
├── IMPLEMENTATION_SUMMARY.md     # Technical implementation details
├── REVIEW.md                     # Project review and notes
├── .gitignore                    # Git ignore rules
└── venv/                         # Virtual environment (not in git)
```

## Examples

### Example 1: Generate BTC-USD Chart

```bash
source venv/bin/activate
python candlestick_chart.py --ticker BTC-USD --save-file bitcoin.png
```

### Example 2: Create All Charts in a Directory

```bash
source venv/bin/activate
mkdir -p output
python candlestick_chart.py --all --save-dir output
```

### Example 3: View Combined Dashboard

```bash
source venv/bin/activate
python candlestick_chart.py --all --combined
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'mplfinance'"

**Solution:** Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Database not found: market_data.db"

**Solution:** Either:
1. Ensure `market_data.db` exists in the current directory
2. Specify the database path: `--db /path/to/market_data.db`

### Issue: "No data found for ticker: XXX"

**Solution:** The ticker may not exist in the database. Use `--list` to see available tickers.

### Issue: "WARNING: YOU ARE PLOTTING SO MUCH DATA..."

This is a normal warning when plotting large datasets. The chart will still generate correctly. To suppress it, modify the chart generation parameters in the code.

## Performance Notes

- Charts with >1000 data points may take longer to render
- Saving to PNG is faster than interactive display on large datasets
- Combined subplots are slower than individual charts

## Contributing

To add new features or improvements:

1. Create a new branch
2. Make your changes
3. Test thoroughly with sample data
4. Update documentation
5. Submit a pull request

## Dependencies

- **pandas** (>=3.0.0) - Data manipulation and analysis
- **matplotlib** (>=3.10.0) - 2D plotting library
- **mplfinance** (>=0.12.0) - Financial charting library
- **pyyaml** (>=6.0) - YAML configuration file parsing

## License

Specify your license here (e.g., MIT, Apache 2.0, etc.)

## Support

For issues, questions, or contributions, please refer to the project documentation or contact the maintainers.

---

**Last Updated:** February 2025
